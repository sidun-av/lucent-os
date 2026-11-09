#pragma once
// WindowGlyph: the decoration's button glyphs (design/gen_aurorae.py GLYPHS:
// lucent.js symbols on a 24-unit grid, stroke 1.9, round caps), painted
// with QPainter so they are as crisp as the Aurorae SVG at any scale.
#include <QColor>
#include <QQuickPaintedItem>

class WindowGlyph : public QQuickPaintedItem
{
    Q_OBJECT
    Q_PROPERTY(QString kind READ kind WRITE setKind NOTIFY changed)   // minimize, maximize, restore, close
    Q_PROPERTY(QColor color READ color WRITE setColor NOTIFY changed)
public:
    explicit WindowGlyph(QQuickItem *parent = nullptr);
    QString kind() const { return m_kind; }
    void setKind(const QString &k);
    QColor color() const { return m_color; }
    void setColor(const QColor &c);
    void paint(QPainter *p) override;
Q_SIGNALS:
    void changed();
private:
    QString m_kind;
    QColor m_color = Qt::black;
};
