#include "glyph.h"

#include <QPainter>
#include <QPainterPath>

WindowGlyph::WindowGlyph(QQuickItem *parent)
    : QQuickPaintedItem(parent)
{
    setAntialiasing(true);
    setImplicitSize(17, 17);
}

void WindowGlyph::setKind(const QString &k)
{
    if (k == m_kind)
        return;
    m_kind = k;
    Q_EMIT changed();
    update();
}

void WindowGlyph::setColor(const QColor &c)
{
    if (c == m_color)
        return;
    m_color = c;
    Q_EMIT changed();
    update();
}

void WindowGlyph::paint(QPainter *p)
{
    p->setRenderHint(QPainter::Antialiasing);
    const qreal s = std::min(width(), height()) / 24.0;
    p->translate((width() - 24 * s) / 2, (height() - 24 * s) / 2);
    p->scale(s, s);
    QPen pen(m_color, 1.9, Qt::SolidLine, Qt::RoundCap, Qt::RoundJoin);
    p->setPen(pen);
    p->setBrush(Qt::NoBrush);
    QPainterPath path;
    if (m_kind == QLatin1String("minimize")) {
        path.moveTo(5.5, 12);
        path.lineTo(18.5, 12);
    } else if (m_kind == QLatin1String("maximize")) {
        path.addRoundedRect(QRectF(5.5, 5.5, 13, 13), 2.5, 2.5);
    } else if (m_kind == QLatin1String("restore")) {
        path.addRoundedRect(QRectF(5.5, 8.5, 10, 10), 2, 2);
        // M8.5 5.5h7.5a2.5 2.5 0 0 1 2.5 2.5v7.5
        path.moveTo(8.5, 5.5);
        path.lineTo(16, 5.5);
        path.arcTo(QRectF(13.5, 5.5, 5, 5), 90, -90);
        path.lineTo(18.5, 15.5);
    } else if (m_kind == QLatin1String("close")) {
        path.moveTo(6.5, 6.5);
        path.lineTo(17.5, 17.5);
        path.moveTo(17.5, 6.5);
        path.lineTo(6.5, 17.5);
    }
    p->drawPath(path);
}
