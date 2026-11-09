/*
 * Lucent widget style: a thin QProxyStyle over Kvantum (theme "Lucent").
 *
 * Kvantum draws every Qt widget from Lucent's SVG theme. This proxy only
 * corrects the few places where an app's own drawing and Kvantum disagree:
 *
 *  1. KIO's breadcrumb (KUrlNavigator, Dolphin's path bar) paints its field
 *     with PE_FrameLineEdit, which Kvantum leaves empty (it draws line edits
 *     in PE_PanelLineEdit). Drawn as a Lucent field here.
 *  2. Toolbars: Kvantum's "grouped toolbar buttons" turn adjacent buttons into
 *     one segmented control. Lucent wants that only for toggle groups (view
 *     modes); plain actions (back, forward, up, split...) stay flat icons
 *     with a hover pill, without the little "hold for history" arrow.
 *  3. Dolphin lines its path bar up with the file view, which leaves a
 *     sidebar-wide gap after the back/forward/up buttons. Lucent's path bar
 *     starts right after them (docs/mockups/01-desktop).
 *  4. Dolphin paints selected file names in the palette's HighlightedText
 *     (white, for a solid accent selection); Lucent selects with a light
 *     accent tint (--sel), so its views get the normal text colour there.
 *  5. Qt Quick views (System Settings, Discover) paint selected text in the
 *     theme's white highlighted-text colour, so their selected rows get a
 *     solid accent pill instead of the light tint.
 *  6. Dolphin's free-space indicator: on an image-based system Solid maps
 *     every local path to the read-only root ("0 B free", a full bar). The
 *     indicator is hidden when it reports that root instead of a wrong value.
 *
 * Keys: "lucent" (Kvantum, theme Lucent) and "lucent-dark" (kvantum-dark,
 * theme LucentDark). Without Kvantum it falls back to Breeze.
 *
 * SPDX-License-Identifier: Apache-2.0
 */
#include <QApplication>
#include <QEvent>
#include <QLayout>
#include <QGraphicsScene>
#include <QGraphicsView>
#include <QPainter>
#include <QPalette>
#include <QPointer>
#include <QProxyStyle>
#include <QStyleFactory>
#include <QStyleOption>
#include <QStylePlugin>
#include <QTimer>
#include <QToolBar>
#include <QToolButton>
#include <sys/statvfs.h>

namespace {

QStyle *makeBase(const QString &key)
{
    if (QStyle *s = QStyleFactory::create(key))
        return s;
    return QStyleFactory::create(QStringLiteral("breeze"));
}

const QToolBar *horizontalToolBar(const QWidget *w)
{
    const auto *bar = w ? qobject_cast<const QToolBar *>(w->parentWidget()) : nullptr;
    return (bar && bar->orientation() == Qt::Horizontal) ? bar : nullptr;
}

// A checkable toolbar button touching another checkable one: part of a
// segmented control (Dolphin's icons/compact/details).
bool isSegment(const QToolButton *tb)
{
    const QToolBar *bar = horizontalToolBar(tb);
    if (!bar || !tb->isCheckable())
        return false;
    const QRect g = tb->geometry();
    const auto buttons = bar->findChildren<QToolButton *>(QString(), Qt::FindDirectChildrenOnly);
    for (const QToolButton *n : buttons) {
        if (n == tb || !n->isVisible() || !n->isCheckable())
            continue;
        const QRect o = n->geometry();
        if (qAbs(o.right() + 1 - g.left()) <= 3 || qAbs(g.right() + 1 - o.left()) <= 3)
            return true;
    }
    return false;
}

// The toolbar a widget sits in, through Dolphin's splitter/containers.
QToolBar *enclosingToolBar(QWidget *w)
{
    for (int i = 0; w && i < 4; ++i, w = w->parentWidget())
        if (auto *bar = qobject_cast<QToolBar *>(w))
            return bar;
    return nullptr;
}

// Drawn for a Qt Quick control (qqc2-desktop-style), not a widget.
bool isQuick(const QStyleOption *opt)
{
    return opt->styleObject && opt->styleObject->inherits("QQuickItem");
}

bool isFlatToolBarButton(const QWidget *w)
{
    const auto *tb = qobject_cast<const QToolButton *>(w);
    return tb && horizontalToolBar(tb) && !isSegment(tb);
}

// The root is a read-only image (composefs): nothing can ever be free there.
bool rootIsReadOnlyImage()
{
    struct statvfs s;
    return statvfs("/", &s) == 0 && s.f_bavail == 0 && (s.f_flag & ST_RDONLY);
}

class LucentStyle : public QProxyStyle
{
public:
    explicit LucentStyle(const QString &baseKey)
        : QProxyStyle(makeBase(baseKey))
    {
    }

    void drawPrimitive(PrimitiveElement pe, const QStyleOption *opt, QPainter *p, const QWidget *w) const override
    {
        if ((pe == PE_PanelItemViewItem || pe == PE_PanelItemViewRow) && !w && isQuick(opt) && (opt->state & State_Selected)) {
            if (pe == PE_PanelItemViewItem)
                drawQuickSelection(opt, p);
            return;
        }
        if (pe == PE_FrameLineEdit && w && w->inherits("KUrlNavigator")) {
            baseStyle()->drawPrimitive(PE_PanelLineEdit, opt, p, w);
            return;
        }
        QProxyStyle::drawPrimitive(pe, opt, p, w);
    }

    void drawControl(ControlElement ce, const QStyleOption *opt, QPainter *p, const QWidget *w) const override
    {
        if (ce == CE_ItemViewItem && !w && isQuick(opt) && (opt->state & State_Selected)) {
            if (const auto *vo = qstyleoption_cast<const QStyleOptionViewItem *>(opt)) {
                drawQuickSelection(opt, p);
                QStyleOptionViewItem o(*vo);
                o.state &= ~State_Selected;
                o.palette.setColor(QPalette::Text, vo->palette.color(QPalette::HighlightedText));
                QProxyStyle::drawControl(ce, &o, p, w);
                return;
            }
        }
        QProxyStyle::drawControl(ce, opt, p, w);
    }

    void drawComplexControl(ComplexControl cc, const QStyleOptionComplex *opt, QPainter *p, const QWidget *w) const override
    {
        if (cc == CC_ToolButton && isFlatToolBarButton(w)) {
            if (const auto *tbo = qstyleoption_cast<const QStyleOptionToolButton *>(opt)) {
                QStyleOptionToolButton o(*tbo);
                stripDelayedMenu(o);
                // Without the widget Kvantum can't see the toolbar, so the
                // button is drawn on its own: flat, hover pill only.
                baseStyle()->drawComplexControl(cc, &o, p, nullptr);
                return;
            }
        }
        QProxyStyle::drawComplexControl(cc, opt, p, w);
    }

    QSize sizeFromContents(ContentsType ct, const QStyleOption *opt, const QSize &size, const QWidget *w) const override
    {
        if (ct == CT_ToolButton && isFlatToolBarButton(w)) {
            if (const auto *tbo = qstyleoption_cast<const QStyleOptionToolButton *>(opt)) {
                QStyleOptionToolButton o(*tbo);
                stripDelayedMenu(o);
                return baseStyle()->sizeFromContents(ct, &o, size, nullptr);
            }
        }
        return QProxyStyle::sizeFromContents(ct, opt, size, w);
    }

    void polish(QWidget *w) override
    {
        QProxyStyle::polish(w);
        if (w->inherits("KUrlNavigator"))
            w->installEventFilter(this); // fixed up once it sits in the toolbar
        if (qobject_cast<QGraphicsView *>(w) && w->parentWidget() && w->parentWidget()->inherits("KItemListContainer")) {
            w->setProperty("_lucent_itemview", true);
            w->installEventFilter(this);
            fixItemViewPalette(static_cast<QGraphicsView *>(w));
        }
        if (w->inherits("StatusBarSpaceInfo") && rootIsReadOnlyImage()) {
            w->installEventFilter(this);
            for (QWidget *c : w->findChildren<QWidget *>())
                if (c->inherits("KCapacityBar"))
                    c->installEventFilter(this);
        }
    }

    void unpolish(QWidget *w) override
    {
        w->removeEventFilter(this);
        QProxyStyle::unpolish(w);
    }

    bool eventFilter(QObject *o, QEvent *e) override
    {
        if (o->inherits("KUrlNavigator")
            && (e->type() == QEvent::Show || e->type() == QEvent::Resize || e->type() == QEvent::ParentChange)) {
            fixPathBar(static_cast<QWidget *>(o));
            return false;
        }
        if (o->property("_lucent_itemview").toBool()) {
            if (e->type() == QEvent::PaletteChange || e->type() == QEvent::Show)
                fixItemViewPalette(static_cast<QGraphicsView *>(o));
            return false;
        }
        if (o->property("_lucent_lead").toBool()) {
            auto *lead = static_cast<QWidget *>(o);
            if ((e->type() == QEvent::Resize || e->type() == QEvent::Show) && lead->minimumWidth() > 0)
                lead->setMinimumWidth(0);
            return false;
        }
        if (e->type() == QEvent::Show || e->type() == QEvent::Paint) {
            QWidget *info = qobject_cast<QWidget *>(o);
            if (info && !info->inherits("StatusBarSpaceInfo"))
                info = info->parentWidget();
            if (info && info->inherits("StatusBarSpaceInfo")) {
                for (QWidget *c : info->findChildren<QWidget *>()) {
                    // Dolphin measured the read-only root: 100 % used.
                    if (c->inherits("KCapacityBar") && c->property("value").toInt() >= 100) {
                        QPointer<QWidget> guard(info);
                        QTimer::singleShot(0, info, [guard] {
                            if (guard)
                                guard->hide();
                        });
                        break;
                    }
                }
            }
        }
        return QProxyStyle::eventFilter(o, e);
    }

private:
    // Qt Quick (qqc2-desktop-style) selection: solid accent, radius 8, inset 4/1
    static void drawQuickSelection(const QStyleOption *opt, QPainter *p)
    {
        const QRectF r = QRectF(opt->rect).adjusted(4, 1, -4, -1);
        p->save();
        p->setRenderHint(QPainter::Antialiasing);
        p->setPen(Qt::NoPen);
        p->setBrush(opt->palette.color(QPalette::Active, QPalette::Highlight));
        p->drawRoundedRect(r, 8, 8);
        p->restore();
    }

    // Dolphin's item views take their colours from the graphics view; the
    // scene (and so every item) follows it.
    static void fixItemViewPalette(QGraphicsView *view)
    {
        QPalette pal = view->palette();
        bool changed = false;
        for (auto g : {QPalette::Active, QPalette::Inactive, QPalette::Disabled}) {
            if (pal.color(g, QPalette::HighlightedText) != pal.color(g, QPalette::Text)) {
                pal.setColor(g, QPalette::HighlightedText, pal.color(g, QPalette::Text));
                changed = true;
            }
        }
        if (changed)
            view->setPalette(pal);
        if (view->scene() && view->scene()->palette().color(QPalette::Active, QPalette::HighlightedText) != pal.color(QPalette::Active, QPalette::HighlightedText))
            view->scene()->setPalette(pal);
    }

    // Dolphin: toolbar > splitter > container [spacer, navigator, ...]
    void fixPathBar(QWidget *nav)
    {
        QWidget *box = nav->parentWidget();
        if (!box || !box->layout() || box->layout()->count() == 0 || !enclosingToolBar(box))
            return;
        // the field is 36 px tall like the mockup's (.crumbs/.search)
        if (nav->maximumHeight() > 36)
            nav->setMaximumHeight(36);
        QWidget *lead = box->layout()->itemAt(0)->widget();
        if (!lead || lead == nav || qstrcmp(lead->metaObject()->className(), "QWidget") != 0)
            return;
        if (!lead->property("_lucent_lead").toBool()) {
            lead->setProperty("_lucent_lead", true);
            lead->installEventFilter(this);
        }
        if (lead->minimumWidth() > 0)
            lead->setMinimumWidth(0);
        // 8 px between the field and the buttons around it (.toolbar gap)
        if (box->layout()->contentsMargins() != QMargins(4, 0, 8, 0))
            box->layout()->setContentsMargins(4, 0, 8, 0);
    }

    static void stripDelayedMenu(QStyleOptionToolButton &o)
    {
        // Back/forward keep their history menu on press-and-hold; only the
        // arrow hint goes (MenuButtonPopup buttons keep their arrow part).
        if ((o.features & QStyleOptionToolButton::HasMenu) && !(o.features & QStyleOptionToolButton::MenuButtonPopup))
            o.features &= ~(QStyleOptionToolButton::HasMenu | QStyleOptionToolButton::PopupDelay);
    }
};

} // namespace

class LucentStylePlugin : public QStylePlugin
{
    Q_OBJECT
    Q_PLUGIN_METADATA(IID "org.qt-project.Qt.QStyleFactoryInterface" FILE "lucentstyle.json")
public:
    QStyle *create(const QString &key) override
    {
        const QString k = key.toLower();
        if (k == QLatin1String("lucent"))
            return new LucentStyle(QStringLiteral("kvantum"));
        if (k == QLatin1String("lucent-dark"))
            return new LucentStyle(QStringLiteral("kvantum-dark"));
        return nullptr;
    }
};

#include "lucentstyle.moc"
