#pragma once
// The decoration's window shadow (Lucent Aurorae, design/gen_aurorae.py, from
// --shadow-window in pebble-drift.css), rendered as one image whose 3x3 grid
// becomes KWindowShadow's eight tiles.
#include <QColor>
#include <QImage>
#include <QMargins>
#include <QVector>

namespace LucentShadow {

struct Drop {          // one CSS box-shadow layer: 0 dy blur spread colour
    QColor color;
    int dy;
    int blur;
    int spread;
};

QVector<Drop> windowDrops(bool dark, bool active);
// Shadow extent outside the window (left, top, right, bottom), as the decoration.
QMargins padding(const QVector<Drop> &drops);
// Half the side of the window square the shadow is rendered for. Big enough
// that the negative spreads (-20) and long blurs still have a straight middle
// as under a real window; the 9-slice splits at the centre pixel, so the
// corner tiles reach this far into the (transparent) window area.
int coreHalf(const QVector<Drop> &drops, int radius);
// Image of size padding + (2 * coreHalf + 1) square; the window's own rounded
// rectangle is cut out, so nothing shows through the transparent corners.
QImage render(const QVector<Drop> &drops, int radius, const QMargins &pad);

}
