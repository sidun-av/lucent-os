#include "windowframe.h"
#include "shadow.h"

#include <KConfigGroup>
#include <KSharedConfig>
#include <KWindowShadow>
#include <QDBusConnection>
#include <QDBusMessage>
#include <QDebug>
#include <QEvent>
#include <QPlatformSurfaceEvent>
#include <QSurfaceFormat>

WindowFrame::WindowFrame(QObject *parent)
    : QObject(parent)
{
    m_config = KSharedConfig::openConfig(QStringLiteral("kwinrc"), KConfig::NoGlobals);
    m_watcher = KConfigWatcher::create(m_config);
    connect(m_watcher.data(), &KConfigWatcher::configChanged, this, [this](const KConfigGroup &group) {
        static const QStringList groups{QStringLiteral("org.kde.kdecoration2"), QStringLiteral("Windows"),
                                        QStringLiteral("Round-Corners"), QStringLiteral("Plugins")};
        if (groups.contains(group.name()))
            readConfig();
    });
    readConfig();
}

WindowFrame::~WindowFrame()
{
    delete m_shadow;
}

void WindowFrame::readConfig()
{
    // KWin rereads kwinrc on reconfigure; KConfigWatcher only sees --notify
    // writes, so reparse here as well.
    m_config->reparseConfiguration();
    const KConfigGroup deco(m_config, QStringLiteral("org.kde.kdecoration2"));
    const QString left = deco.readEntry("ButtonsOnLeft", QStringLiteral("MS"));
    const QString right = deco.readEntry("ButtonsOnRight", QStringLiteral("HIAX"));
    m_doubleClick = KConfigGroup(m_config, QStringLiteral("Windows")).readEntry("TitlebarDoubleClickCommand", QStringLiteral("Maximize"));
    const int radius = KConfigGroup(m_config, QStringLiteral("Round-Corners")).readEntry("Size", 18);
    const bool rounds = KConfigGroup(m_config, QStringLiteral("Plugins")).readEntry("kwin4_effect_shapecornersEnabled", false);
    if (radius != m_radius || rounds != m_compositorRounds) {
        m_radius = radius;
        m_compositorRounds = rounds;
        Q_EMIT radiusChanged();
        updateShadow();
    }
    if (left != m_left || right != m_right) {
        m_left = left;
        m_right = right;
        Q_EMIT buttonsChanged();
    }
}

void WindowFrame::setWindow(QQuickWindow *w)
{
    if (w == m_window)
        return;
    if (m_window)
        m_window->removeEventFilter(this);
    m_window = w;
    if (m_window) {
        if (!m_window->handle()) {
            // No platform window yet: make it frameless and give it an alpha
            // channel for the rounded corners.
            m_window->setFlag(Qt::FramelessWindowHint, true);
            QSurfaceFormat f = m_window->format();
            f.setAlphaBufferSize(8);
            m_window->setFormat(f);
            m_window->setColor(Qt::transparent);
        }
        m_window->installEventFilter(this);
        connect(m_window, &QWindow::activeChanged, this, [this] {
            Q_EMIT stateChanged();
            updateShadow();
        });
        connect(m_window, &QWindow::windowStateChanged, this, [this] {
            Q_EMIT stateChanged();
            updateShadow();
        });
        connect(m_window, &QWindow::visibleChanged, this, &WindowFrame::updateShadow);
    }
    Q_EMIT windowChanged();
    Q_EMIT stateChanged();
    updateShadow();
}

bool WindowFrame::eventFilter(QObject *watched, QEvent *event)
{
    if (watched == m_window && event->type() == QEvent::PlatformSurface) {
        // The wl_surface is (re)created on show: the shadow has to follow it.
        if (static_cast<QPlatformSurfaceEvent *>(event)->surfaceEventType() == QPlatformSurfaceEvent::SurfaceCreated) {
            m_shadowKey.clear();
            QMetaObject::invokeMethod(this, &WindowFrame::updateShadow, Qt::QueuedConnection);
        }
    }
    return QObject::eventFilter(watched, event);
}

void WindowFrame::setDark(bool d)
{
    if (d == m_dark)
        return;
    m_dark = d;
    Q_EMIT darkChanged();
    updateShadow();
}

bool WindowFrame::active() const
{
    return m_window && m_window->isActive();
}

bool WindowFrame::maximized() const
{
    return m_window && (m_window->windowStates() & (Qt::WindowMaximized | Qt::WindowFullScreen));
}

void WindowFrame::updateShadow()
{
    const bool want = m_window && m_window->isVisible() && m_window->handle() && !maximized();
    if (qEnvironmentVariableIsSet("LUCENT_CHROME_DEBUG"))
        qInfo() << "lucent-chrome: updateShadow want" << want << "visible" << (m_window && m_window->isVisible()) << "handle" << (m_window && m_window->handle());
    if (!want) {
        if (m_shadow) {
            m_shadow->destroy();
            delete m_shadow;
            m_shadow = nullptr;
        }
        m_shadowKey.clear();
        if (m_shadowShown) {
            m_shadowShown = false;
            Q_EMIT shadowShownChanged();
        }
        return;
    }
    const bool act = active();
    const QString key = QStringLiteral("%1/%2/%3").arg(m_dark).arg(act).arg(m_radius);
    if (key == m_shadowKey && m_shadow)
        return;
    m_shadowKey = key;

    const auto drops = LucentShadow::windowDrops(m_dark, act);
    const QMargins pad = LucentShadow::padding(drops);
    const QImage img = LucentShadow::render(drops, m_radius, pad);
    // 9-slice around the centre pixel, so the corner tiles hold the whole arc.
    const int half = LucentShadow::coreHalf(drops, m_radius);
    const int cx = pad.left() + half;
    const int cy = pad.top() + half;
    const int rw = img.width() - cx - 1;
    const int bh = img.height() - cy - 1;
    auto tile = [&img](int x, int y, int w, int h) {
        auto t = KWindowShadowTile::Ptr::create();
        t->setImage(img.copy(x, y, w, h));
        return t;
    };
    if (m_shadow) {
        m_shadow->destroy();
        delete m_shadow;
    }
    m_shadow = new KWindowShadow(this);
    m_shadow->setTopLeftTile(tile(0, 0, cx, cy));
    m_shadow->setTopTile(tile(cx, 0, 1, cy));
    m_shadow->setTopRightTile(tile(cx + 1, 0, rw, cy));
    m_shadow->setLeftTile(tile(0, cy, cx, 1));
    m_shadow->setRightTile(tile(cx + 1, cy, rw, 1));
    m_shadow->setBottomLeftTile(tile(0, cy + 1, cx, bh));
    m_shadow->setBottomTile(tile(cx, cy + 1, 1, bh));
    m_shadow->setBottomRightTile(tile(cx + 1, cy + 1, rw, bh));
    m_shadow->setPadding(pad);
    m_shadow->setWindow(m_window);
    const bool ok = m_shadow->create();
    if (qEnvironmentVariableIsSet("LUCENT_CHROME_DEBUG"))
        qInfo() << "lucent-chrome: shadow" << key << "padding" << pad << "image" << img.size() << "created" << ok << m_shadow->isCreated();
    if (!ok)
        qWarning("org.lucent.chrome: the compositor did not accept the window shadow");
    if (ok != m_shadowShown) {
        m_shadowShown = ok;
        Q_EMIT shadowShownChanged();
    }
}

void WindowFrame::startMove()
{
    if (m_window)
        m_window->startSystemMove();
}

void WindowFrame::startResize(int edges)
{
    if (m_window && !maximized())
        m_window->startSystemResize(Qt::Edges(edges));
}

void WindowFrame::toggleMaximize()
{
    if (!m_window)
        return;
    if (maximized())
        m_window->showNormal();
    else
        m_window->showMaximized();
}

void WindowFrame::minimize()
{
    if (m_window)
        m_window->showMinimized();
}

void WindowFrame::close()
{
    if (m_window)
        m_window->close();
}

void WindowFrame::titleDoubleClicked()
{
    // KWin's TitlebarDoubleClickCommand values that make sense for a client.
    if (m_doubleClick.startsWith(QLatin1String("Maximize")))
        toggleMaximize();
    else if (m_doubleClick == QLatin1String("Minimize"))
        minimize();
    else if (m_doubleClick == QLatin1String("Close"))
        close();
}

void WindowFrame::showWindowMenu()
{
    // KWin's own window menu (Alt+F3) for the active window - ours, as it was
    // just clicked. Wayland gives clients no other way to open it from Qt.
    auto msg = QDBusMessage::createMethodCall(QStringLiteral("org.kde.kglobalaccel"), QStringLiteral("/component/kwin"),
                                              QStringLiteral("org.kde.kglobalaccel.Component"), QStringLiteral("invokeShortcut"));
    msg << QStringLiteral("Window Operations Menu");
    QDBusConnection::sessionBus().send(msg);
}
