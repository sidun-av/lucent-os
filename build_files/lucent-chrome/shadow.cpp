#include "shadow.h"

#include <QPainter>
#include <QPainterPath>
#include <algorithm>
#include <cmath>

namespace LucentShadow {

QVector<Drop> windowDrops(bool dark, bool active)
{
    // --shadow-window without its first layer (the 1 px ring, drawn by the app).
    QVector<Drop> d = dark
        ? QVector<Drop>{{QColor(0, 0, 0, int(.25 * 255)), 2, 4, 0},
                        {QColor(0, 0, 0, int(.45 * 255)), 18, 40, -6},
                        {QColor(0, 0, 0, int(.60 * 255)), 50, 120, -20}}
        : QVector<Drop>{{QColor(25, 35, 90, int(.05 * 255)), 2, 4, 0},
                        {QColor(25, 35, 90, int(.15 * 255)), 16, 34, -6},
                        {QColor(25, 35, 90, int(.30 * 255)), 50, 110, -20}};
    if (!active) {   // inactive windows: the same shape at 60 % (gen_aurorae)
        for (auto &x : d)
            x.color.setAlphaF(x.color.alphaF() * 0.6);
    }
    return d;
}

QMargins padding(const QVector<Drop> &drops)
{
    // gen_aurorae.padding(): 2.2 sigma (+ spread), shifted by dy.
    double side = 0, top = 0, bottom = 0;
    for (const auto &d : drops) {
        const double reach = 1.1 * d.blur + d.spread;
        side = std::max(side, reach);
        top = std::max(top, std::max(reach - d.dy, 4.0));
        bottom = std::max(bottom, reach + d.dy);
    }
    return QMargins(int(std::lround(side)), int(std::lround(top)), int(std::lround(side)), int(std::lround(bottom)));
}

int coreHalf(const QVector<Drop> &drops, int radius)
{
    double k = 0;
    for (const auto &d : drops)
        k = std::max(k, 1.1 * d.blur + std::abs(d.spread));
    return radius + int(std::ceil(k));
}

// Three box blurs approximate a Gaussian of the given sigma (alpha channel only).
static void boxBlur(QVector<float> &a, int w, int h, int r)
{
    if (r < 1)
        return;
    QVector<float> tmp(a.size());
    const float n = 2 * r + 1;
    for (int y = 0; y < h; ++y) {               // horizontal
        float acc = 0;
        for (int x = -r; x <= r; ++x)
            acc += a[y * w + std::clamp(x, 0, w - 1)];
        for (int x = 0; x < w; ++x) {
            tmp[y * w + x] = acc / n;
            acc += a[y * w + std::clamp(x + r + 1, 0, w - 1)] - a[y * w + std::clamp(x - r, 0, w - 1)];
        }
    }
    for (int x = 0; x < w; ++x) {               // vertical
        float acc = 0;
        for (int y = -r; y <= r; ++y)
            acc += tmp[std::clamp(y, 0, h - 1) * w + x];
        for (int y = 0; y < h; ++y) {
            a[y * w + x] = acc / n;
            acc += tmp[std::clamp(y + r + 1, 0, h - 1) * w + x] - tmp[std::clamp(y - r, 0, h - 1) * w + x];
        }
    }
}

QImage render(const QVector<Drop> &drops, int radius, const QMargins &pad)
{
    const int core = 2 * coreHalf(drops, radius) + 1;
    const int w = pad.left() + core + pad.right();
    const int h = pad.top() + core + pad.bottom();
    QImage out(w, h, QImage::Format_ARGB32_Premultiplied);
    out.fill(Qt::transparent);
    QPainter p(&out);
    p.setRenderHint(QPainter::Antialiasing);
    for (const auto &d : drops) {
        QImage mask(w, h, QImage::Format_Grayscale8);
        mask.fill(0);
        {
            QPainter m(&mask);
            m.setRenderHint(QPainter::Antialiasing);
            m.setPen(Qt::NoPen);
            m.setBrush(Qt::white);
            const QRectF r(pad.left() - d.spread, pad.top() + d.dy - d.spread, core + 2 * d.spread, core + 2 * d.spread);
            const double rr = std::max(0, radius + d.spread);
            m.drawRoundedRect(r, rr, rr);
        }
        QVector<float> a(w * h);
        for (int y = 0; y < h; ++y) {
            const uchar *line = mask.constScanLine(y);
            for (int x = 0; x < w; ++x)
                a[y * w + x] = line[x] / 255.0f;
        }
        // CSS blur radius = 2 sigma; three box passes of radius ~ sigma
        const double sigma = d.blur / 2.0;
        const int r = int(std::lround(std::sqrt(12.0 * sigma * sigma / 3 + 1) / 2));
        for (int i = 0; i < 3; ++i)
            boxBlur(a, w, h, r);
        QImage layer(w, h, QImage::Format_ARGB32_Premultiplied);
        for (int y = 0; y < h; ++y) {
            auto *line = reinterpret_cast<QRgb *>(layer.scanLine(y));
            for (int x = 0; x < w; ++x) {
                const float al = std::clamp(a[y * w + x], 0.0f, 1.0f) * d.color.alphaF();
                line[x] = qPremultiply(qRgba(d.color.red(), d.color.green(), d.color.blue(), int(al * 255 + .5)));
            }
        }
        p.drawImage(0, 0, layer);
    }
    // The window covers its own rounded rectangle: cut it out.
    p.setCompositionMode(QPainter::CompositionMode_Clear);
    p.setPen(Qt::NoPen);
    p.setBrush(Qt::black);
    p.drawRoundedRect(QRectF(pad.left(), pad.top(), core, core), radius, radius);
    p.end();
    return out;
}

}
