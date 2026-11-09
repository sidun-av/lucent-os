#pragma once
// image://lucent-chrome-icon/<theme icon name>[?size]: the app's icon from the
// icon theme (Papirus), as KWin's menu button shows it.
#include <QIcon>
#include <QQuickImageProvider>

class ThemeIconProvider : public QQuickImageProvider
{
public:
    ThemeIconProvider()
        : QQuickImageProvider(QQuickImageProvider::Pixmap)
    {
    }
    QPixmap requestPixmap(const QString &id, QSize *size, const QSize &requested) override
    {
        const QSize want = requested.isValid() && !requested.isEmpty() ? requested : QSize(28, 28);
        QPixmap px = QIcon::fromTheme(id).pixmap(want);
        if (px.isNull()) {          // no icon theme (offscreen checks): an empty square
            px = QPixmap(want);
            px.fill(Qt::transparent);
        }
        if (size)
            *size = px.size();
        return px;
    }
};
