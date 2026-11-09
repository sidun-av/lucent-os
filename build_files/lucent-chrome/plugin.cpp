#include "glyph.h"
#include "iconprovider.h"
#include "windowframe.h"

#include <QQmlEngine>
#include <QQmlExtensionPlugin>
#include <QQuickWindow>
#include <qqml.h>

class LucentChromePlugin : public QQmlExtensionPlugin
{
    Q_OBJECT
    Q_PLUGIN_METADATA(IID QQmlExtensionInterface_iid)
public:
    void registerTypes(const char *uri) override
    {
        // Rounded corners need an alpha channel in every window the app makes.
        QQuickWindow::setDefaultAlphaBuffer(true);
        qmlRegisterType<WindowFrame>(uri, 1, 0, "WindowFrame");
        qmlRegisterType<WindowGlyph>(uri, 1, 0, "WindowGlyph");
    }
    void initializeEngine(QQmlEngine *engine, const char *) override
    {
        if (!engine->imageProvider(QStringLiteral("lucent-chrome-icon")))
            engine->addImageProvider(QStringLiteral("lucent-chrome-icon"), new ThemeIconProvider);
    }
};

#include "plugin.moc"
