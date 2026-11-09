#!/usr/bin/env python3
"""Generate the Lucent window decorations (Aurorae v2 themes, light + dark).

docs/mockups/lucent.css .win/.titlebar: 44 px title bar in the header colour
(seamless with the app's own header), title centred 15 px/600, app icon
20 px at the left, minimise/maximise/close as thin 15 px glyphs in 52 px
wide buttons on the right, window radius 14, soft two-layer shadow.

The decoration draws square bottom corners under the client; the
KDE-Rounded-Corners KWin effect (configured to the same radius) clips the
whole window and draws the 1 px outline.

Output: system_files/usr/share/aurorae/themes/{Lucent,LucentDark}/
"""
import gzip
import shutil
from pathlib import Path

from framekit import SCALE, Cursor, SvgDoc, crop, render_box

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "system_files/usr/share/aurorae/themes"

R = 14            # --radius-win
TITLE_H = 44      # .titlebar height
BTN_W = 52        # .titlebar .wb i width
C = 8             # stretchable middle of the 9-slice

THEMES = {
    "Lucent": dict(
        name="Lucent", head="#f4f5f8", text="#1b1f27", text_inactive="#6a7282",
        glyph="#4c5463", glyph_inactive="#9aa1ae", hover="rgba(20,28,45,.07)", pressed="rgba(20,28,45,.13)",
        close_hover="#d23b3b", close_pressed="#b52f2f",
        shadows=[("rgba(15,20,35,.22)", 60, 0, 24, 0), ("rgba(15,20,35,.10)", 18, 0, 6, 0)],
        shadows_inactive=[("rgba(15,20,35,.13)", 44, 0, 16, 0), ("rgba(15,20,35,.06)", 12, 0, 4, 0)],
    ),
    "LucentDark": dict(
        name="Lucent Dark", head="#191b21", text="#eef0f5", text_inactive="#959cab",
        glyph="#b4bac6", glyph_inactive="#6f7685", hover="rgba(255,255,255,.08)", pressed="rgba(255,255,255,.14)",
        close_hover="#d23b3b", close_pressed="#b52f2f",
        shadows=[("rgba(0,0,0,.55)", 70, 0, 24, 0)],
        shadows_inactive=[("rgba(0,0,0,.38)", 50, 0, 16, 0)],
    ),
}


def padding(shadows):
    """Shadow extent around the window: 2.6 sigma, shifted by the y offset."""
    reach = [(1.3 * blur, dy) for _, blur, _, dy, _ in shadows]
    side = int(round(max(r for r, _ in reach)))
    top = int(round(max(max(r - dy, 4) for r, dy in reach)))
    bottom = int(round(max(r + dy for r, dy in reach)))
    return side, top, side, bottom


def decoration(doc, cur, prefix, t, shadows, pad):
    pl, pt, pr, pb = pad
    bw, bh = 2 * R + C, TITLE_H + C + R
    W, H = pl + bw + pr, pt + bh + pb
    img = render_box(W, H, (pl, pt, bw, bh), R, fill=t["head"], shadows=shadows, cut_inside_shadow=True)
    cols = [(0, pl + R), (pl + R, C), (pl + R + C, R + pr)]
    rows = [(0, pt + TITLE_H), (pt + TITLE_H, C), (pt + TITLE_H + C, R + pb)]
    names = [["topleft", "top", "topright"], ["left", "center", "right"], ["bottomleft", "bottom", "bottomright"]]
    x0, y0 = cur.place(W, H, gap=8)
    for ri, (ry, rh) in enumerate(rows):
        for ci, (cx, cw) in enumerate(cols):
            doc.image(f"{prefix}-{names[ri][ci]}", x0 + cx, y0 + ry, crop(img, cx, ry, cw, rh))


def maximized(doc, cur, prefix, t):
    """Maximised: no shadow, square corners, just the title bar colour."""
    x, y = cur.place(3, TITLE_H + 2, gap=8)
    names = [["topleft", "top", "topright"], ["left", "center", "right"], ["bottomleft", "bottom", "bottomright"]]
    for ri, (ry, rh) in enumerate([(0, TITLE_H), (TITLE_H, 1), (TITLE_H + 1, 1)]):
        for ci in range(3):
            doc.rect(f"{prefix}-{names[ri][ci]}", x + ci, y + ry, 1, rh, fill=t["head"], opacity=1)


GLYPHS = {   # lucent.js symbols (24-unit grid), drawn at 15 px like .titlebar .wb i svg
    "minimize": '<path d="M5.5 12h13"/>',
    "maximize": '<rect x="5.5" y="5.5" width="13" height="13" rx="2.5"/>',
    "restore": '<rect x="5.5" y="8.5" width="10" height="10" rx="2"/><path d="M8.5 5.5h7.5a2.5 2.5 0 0 1 2.5 2.5v7.5"/>',
    "close": '<path d="M6.5 6.5l11 11M17.5 6.5l-11 11"/>',
}


def css(c):
    """'rgba(r,g,b,a)' -> (fill, opacity) for QtSvg."""
    if c.startswith("rgba"):
        r, g, b, a = c[5:-1].split(",")
        return f"rgb({r},{g},{b})", a
    return c, "1"


def button(kind, t):
    s = 15 / 24
    ox, oy = (BTN_W - 15) / 2, (TITLE_H - 15) / 2
    states = {
        "active": (None, t["glyph"]),
        "hover": (t["close_hover"] if kind == "close" else t["hover"], "#ffffff" if kind == "close" else t["text"]),
        "pressed": (t["close_pressed"] if kind == "close" else t["pressed"], "#ffffff" if kind == "close" else t["text"]),
        "inactive": (None, t["glyph_inactive"]),
        "hover-inactive": (t["close_hover"] if kind == "close" else t["hover"], "#ffffff" if kind == "close" else t["text"]),
        "deactivated": (None, t["glyph_inactive"]),
    }
    parts = []
    for i, (state, (bg, fg)) in enumerate(states.items()):
        x0 = i * (BTN_W + 10)
        body = [f'<rect x="{x0}" y="0" width="{BTN_W}" height="{TITLE_H}" style="fill:#000;fill-opacity:0"/>']
        if bg:
            fill, op = css(bg)
            if kind == "close":   # Windows habit: a full-height red close button
                body.append(f'<rect x="{x0}" y="0" width="{BTN_W}" height="{TITLE_H}" style="fill:{fill};fill-opacity:{op}"/>')
            else:
                body.append(f'<rect x="{x0 + 8}" y="7" width="{BTN_W - 16}" height="{TITLE_H - 14}" rx="8" style="fill:{fill};fill-opacity:{op}"/>')
        body.append(f'<g transform="translate({x0 + ox} {oy}) scale({s})" style="fill:none;stroke:{fg};'
                    f'stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round">{GLYPHS[kind]}</g>')
        parts.append(f'<g id="{state}-center">' + "".join(body) + "</g>")
    w = len(states) * (BTN_W + 10)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{TITLE_H}" viewBox="0 0 {w} {TITLE_H}">\n'
            + "\n".join(parts) + "\n</svg>\n")


RC = """[General]
ActiveTextColor={text}
InactiveTextColor={text_inactive}
TitleAlignment=Center
TitleVerticalAlignment=Center
Animation=120

[Layout]
BorderLeft=0
BorderRight=0
BorderBottom=0
BorderTop=0
TitleEdgeTop=0
TitleEdgeBottom=0
TitleEdgeLeft=16
TitleEdgeRight=0
TitleEdgeTopMaximized=0
TitleEdgeBottomMaximized=0
TitleEdgeLeftMaximized=16
TitleEdgeRightMaximized=0
TitleBorderLeft=12
TitleBorderRight=12
TitleHeight={title_h}
ButtonWidth={btn_w}
ButtonWidthMenu=20
ButtonHeight={title_h}
ButtonSpacing=0
ButtonMarginTop=0
ButtonMarginTopMaximized=0
ExplicitButtonSpacer=8
PaddingLeft={pl}
PaddingRight={pr}
PaddingTop={pt}
PaddingBottom={pb}
"""

META = """[Desktop Entry]
Name={name}
Comment=Lucent OS window decoration
X-KDE-PluginInfo-Author=Lucent OS contributors
X-KDE-PluginInfo-Name={tid}
X-KDE-PluginInfo-Version=1.0
X-KDE-PluginInfo-License=Apache-2.0
X-KDE-PluginInfo-Website=https://github.com/sidun-av/lucent-os
"""


def rgb(hexcol):
    h = hexcol.lstrip("#")
    return ",".join(str(int(h[i:i + 2], 16)) for i in (0, 2, 4))


def main():
    for tid, t in THEMES.items():
        base = OUT / tid
        if base.exists():
            shutil.rmtree(base)
        base.mkdir(parents=True)
        # One padding for active and inactive (Aurorae has a single one).
        pad = padding(t["shadows"])
        doc, cur = SvgDoc(0, 0), Cursor()
        decoration(doc, cur, "decoration", t, t["shadows"], pad)
        decoration(doc, cur, "decoration-inactive", t, t["shadows_inactive"], pad)
        maximized(doc, cur, "decoration-maximized", t)
        maximized(doc, cur, "decoration-maximized-inactive", t)
        doc.w, doc.h = cur.max_w, cur.height + 4
        with gzip.GzipFile(base / "decoration.svgz", "wb", mtime=0) as f:
            f.write(doc.svg().encode())
        for kind in GLYPHS:
            (base / f"{kind}.svg").write_text(button(kind, t))
        pl, pt, pr, pb = pad
        (base / f"{tid}rc").write_text(RC.format(text=rgb(t["text"]), text_inactive=rgb(t["text_inactive"]),
                                                 title_h=TITLE_H, btn_w=BTN_W, pl=pl, pt=pt, pr=pr, pb=pb))
        (base / "metadata.desktop").write_text(META.format(name=t["name"], tid=tid))
        print("wrote", base, "padding", pad)


if __name__ == "__main__":
    main()
