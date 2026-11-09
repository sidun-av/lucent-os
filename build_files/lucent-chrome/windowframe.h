#pragma once
// WindowFrame: what KWin's decoration does for a decorated window, for a
// frameless QQuickWindow that draws its own header row.
//   - a KWin-drawn shadow (KWindowShadow) of the Lucent decoration's shape,
//     light/dark and active/inactive, none when maximised;
//   - the button order of kwinrc [org.kde.kdecoration2] ButtonsOnLeft/Right,
//     [Windows] TitlebarDoubleClickCommand and the corner radius, followed
//     live (KConfigWatcher);
//   - move / resize / maximise / minimise / window-menu actions for the QML.
#include <QObject>
#include <QPointer>
#include <QQuickWindow>
#include <KConfigWatcher>
#include <KWindowShadow>

class WindowFrame : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QQuickWindow *window READ window WRITE setWindow NOTIFY windowChanged)
    Q_PROPERTY(bool dark READ dark WRITE setDark NOTIFY darkChanged)
    // kwinrc [Round-Corners] Size: the KDE-Rounded-Corners effect's radius
    Q_PROPERTY(int radius READ radius NOTIFY radiusChanged)
    // the effect is on ([Plugins] kwin4_effect_shapecornersEnabled): it clips
    // and outlines this window like the decorated ones, so draw square corners
    Q_PROPERTY(bool compositorRounds READ compositorRounds NOTIFY radiusChanged)
    Q_PROPERTY(bool active READ active NOTIFY stateChanged)
    Q_PROPERTY(bool maximized READ maximized NOTIFY stateChanged)
    Q_PROPERTY(QString buttonsLeft READ buttonsLeft NOTIFY buttonsChanged)
    Q_PROPERTY(QString buttonsRight READ buttonsRight NOTIFY buttonsChanged)
    Q_PROPERTY(bool shadowShown READ shadowShown NOTIFY shadowShownChanged)

public:
    explicit WindowFrame(QObject *parent = nullptr);
    ~WindowFrame() override;

    QQuickWindow *window() const { return m_window; }
    void setWindow(QQuickWindow *w);
    bool dark() const { return m_dark; }
    void setDark(bool d);
    int radius() const { return m_radius; }
    bool compositorRounds() const { return m_compositorRounds; }
    bool active() const;
    bool maximized() const;
    QString buttonsLeft() const { return m_left; }
    QString buttonsRight() const { return m_right; }
    bool shadowShown() const { return m_shadowShown; }

    Q_INVOKABLE void startMove();
    Q_INVOKABLE void startResize(int edges);
    Q_INVOKABLE void toggleMaximize();
    Q_INVOKABLE void minimize();
    Q_INVOKABLE void close();
    Q_INVOKABLE void titleDoubleClicked();
    Q_INVOKABLE void showWindowMenu();

Q_SIGNALS:
    void windowChanged();
    void darkChanged();
    void radiusChanged();
    void stateChanged();
    void buttonsChanged();
    void shadowShownChanged();

protected:
    bool eventFilter(QObject *watched, QEvent *event) override;

private:
    void readConfig();
    void updateShadow();

    QPointer<QQuickWindow> m_window;
    bool m_dark = false;
    int m_radius = 18;
    bool m_compositorRounds = false;
    QString m_left = QStringLiteral("M");
    QString m_right = QStringLiteral("IAX");
    QString m_doubleClick = QStringLiteral("Maximize");
    KSharedConfigPtr m_config;
    KConfigWatcher::Ptr m_watcher;
    KWindowShadow *m_shadow = nullptr;
    QString m_shadowKey;
    bool m_shadowShown = false;
};
