#!/usr/bin/env python3
"""Generate the Lucent window decorations (Aurorae v2 themes, light + dark)
from the Pebble Drift tokens (pebble-drift.css, design/tokens.py).

The mockup's window (.win/.head/.wb): one matte surface, radius
--radius-window (18), a 1 px top light (--highlight-top) and the long,
cool-tinted --shadow-window. The title bar is the top of that surface in the
window colour, so it runs straight into the app's own menu and toolbar rows
(Kvantum draws those flat in the same colour): the header reads as one block.
App icon on the left, title next to it (Windows habit), minimise / maximise /
close as 44 x 36 rounded buttons (--radius-control) with 17 px glyphs on the
right; hover --state-hover, close hover --status-danger with a white glyph.

The decoration draws square bottom corners under the client; the
KDE-Rounded-Corners KWin effect (configured to the same radius) clips the
whole window and draws the 1 px outline.

Output: system_files/usr/share/aurorae/themes/{Lucent,LucentDark}/
"""
import gzip
import shutil
from pathlib import Path

import numpy as np

import tokens
from framekit import SCALE, Cursor, SvgDoc, crop, render_box, rgba, sdf_roundrect, downsample, coverage, over, SS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "system_files/usr/share/aurorae/themes"

TITLE_H = 48      # 36 px buttons with 6 px above and below
BTN_W = 44        # .wb i: 44 x 36
BTN_H = 36
BTN_GAP = 2       # .wb gap
EDGE = 12         # .head padding-right
C = 8             # stretchable middle of the 9-slice


def theme(t: dict, dark: bool) -> dict:
    sh = tokens.shadows(t["shadow-window"])
    ring = sh[0][4]
    drops = [(col, blur, dx, dy, spread) for dx, dy, blur, spread, col in sh[1:]]
    # Inactive windows: the same shape at 60 % strength.
    weaker = [(tokens.rgba_str(c, tokens.color(c)[3] * 0.6), b, dx, dy, s) for c, b, dx, dy, s in drops]
    return dict(
        name="Lucent Dark" if dark else "Lucent", head=t["surface-window-solid"],
        R=int(tokens.px(t["radius-window"])), btn_r=int(tokens.px(t["radius-control"])),
        text=t["text-primary"], text_inactive=t["text-tertiary"],
        glyph=t["text-secondary"], glyph_inactive=t["text-disabled"], glyph_hover=t["text-primary"],
        hover=t["state-hover"], pressed=t["state-pressed"],
        close_hover=t["status-danger"], close_pressed=tokens.flatten(tokens.rgba_str("#000000", .14), t["status-danger"]),
        ring=ring, highlight=tokens.shadows(t["highlight-top"])[0][4],
        shadows=drops, shadows_inactive=weaker,
    )


def padding(shadows):
    """Shadow extent around the window: 2.2 sigma (+ spread), shifted by dy.
    Past that the long shadow is under 1 % alpha; a smaller padding keeps every
    window's decoration texture (and its blending on llvmpipe) smaller."""
    reach = [(1.1 * blur + spread, dy) for _, blur, _, dy, spread in shadows]
    side = int(round(max(r for r, _ in reach)))
    top = int(round(max(max(r - dy, 4) for r, dy in reach)))
    bottom = int(round(max(r + dy for r, dy in reach)))
    return side, top, side, bottom


def decoration(doc, cur, prefix, t, shadows, pad):
    pl, pt, pr, pb = pad
    R = t["R"]
    bw, bh = 2 * R + C, TITLE_H + C + R
    W, H = pl + bw + pr, pt + bh + pb

    def top_light(img):
        # --highlight-top: inset 0 1px 0 white .9, following the rounded top edge
        a = sdf_roundrect(W, H, pl, pt, bw, bh, R, SCALE, SS)
        b = sdf_roundrect(W, H, pl, pt + 1, bw, bh, R, SCALE, SS)
        band = np.clip(downsample(coverage(a), SS) - downsample(coverage(b), SS), 0, 1)
        return over(img, rgba(tokens.rgba_str(t["highlight"])), band)

    img = render_box(W, H, (pl, pt, bw, bh), R, fill=t["head"], ring=tokens.rgba_str(t["ring"]),
                     shadows=[(tokens.rgba_str(c), b, dx, dy, s) for c, b, dx, dy, s in shadows],
                     cut_inside_shadow=True, extra=top_light)
    cols = [(0, pl + R), (pl + R, C), (pl + R + C, R + pr)]
    rows = [(0, pt + TITLE_H), (pt + TITLE_H, C), (pt + TITLE_H + C, R + pb)]
    names = [["topleft", "top", "topright"], ["left", "center", "right"], ["bottomleft", "bottom", "bottomright"]]
    x0, y0 = cur.place(W, H, gap=8)
    for ri, (ry, rh) in enumerate(rows):
        for ci, (cx, cw) in enumerate(cols):
            doc.image(f"{prefix}-{names[ri][ci]}", x0 + cx, y0 + ry, crop(img, cx, ry, cw, rh))


def maximized(doc, cur, prefix, t):
    """Maximised: no shadow, square corners, just the header colour."""
    x, y = cur.place(3, TITLE_H + 2, gap=8)
    names = [["topleft", "top", "topright"], ["left", "center", "right"], ["bottomleft", "bottom", "bottomright"]]
    for ri, (ry, rh) in enumerate([(0, TITLE_H), (TITLE_H, 1), (TITLE_H + 1, 1)]):
        for ci in range(3):
            doc.rect(f"{prefix}-{names[ri][ci]}", x + ci, y + ry, 1, rh, fill=t["head"], opacity=1)


GLYPHS = {   # lucent.js symbols (24-unit grid), drawn at 17 px like .wb i svg
    "minimize": '<path d="M5.5 12h13"/>',
    "maximize": '<rect x="5.5" y="5.5" width="13" height="13" rx="2.5"/>',
    "restore": '<rect x="5.5" y="8.5" width="10" height="10" rx="2"/><path d="M8.5 5.5h7.5a2.5 2.5 0 0 1 2.5 2.5v7.5"/>',
    "close": '<path d="M6.5 6.5l11 11M17.5 6.5l-11 11"/>',
}
GLYPH = 17


def css(c):
    """'rgba(r,g,b,a)' / '#rrggbb' -> (fill, opacity) for QtSvg."""
    r, g, b, a = tokens.color(c)
    return tokens.hexcolor((r, g, b)), f"{a:g}"


def button(kind, t):
    s = GLYPH / 24
    ox, oy = (BTN_W - GLYPH) / 2, (TITLE_H - GLYPH) / 2
    by = (TITLE_H - BTN_H) / 2
    close = kind == "close"
    states = {
        "active": (None, t["glyph"]),
        "hover": (t["close_hover"] if close else t["hover"], "#ffffff" if close else t["glyph_hover"]),
        "pressed": (t["close_pressed"] if close else t["pressed"], "#ffffff" if close else t["glyph_hover"]),
        "inactive": (None, t["glyph_inactive"]),
        "hover-inactive": (t["close_hover"] if close else t["hover"], "#ffffff" if close else t["glyph_hover"]),
        "deactivated": (None, t["glyph_inactive"]),
    }
    parts = []
    for i, (state, (bg, fg)) in enumerate(states.items()):
        x0 = i * (BTN_W + 10)
        body = [f'<rect x="{x0}" y="0" width="{BTN_W}" height="{TITLE_H}" style="fill:#000;fill-opacity:0"/>']
        if bg:
            fill, op = css(bg)
            body.append(f'<rect x="{x0}" y="{by}" width="{BTN_W}" height="{BTN_H}" rx="{t["btn_r"]}" '
                        f'style="fill:{fill};fill-opacity:{op}"/>')
        stroke, sop = css(fg)
        body.append(f'<g transform="translate({x0 + ox} {oy}) scale({s:.5f})" style="fill:none;stroke:{stroke};'
                    f'stroke-opacity:{sop};stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round">{GLYPHS[kind]}</g>')
        parts.append(f'<g id="{state}-center">' + "".join(body) + "</g>")
    w = len(states) * (BTN_W + 10)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{TITLE_H}" viewBox="0 0 {w} {TITLE_H}">\n'
            + "\n".join(parts) + "\n</svg>\n")


RC = """[General]
ActiveTextColor={text}
InactiveTextColor={text_inactive}
TitleAlignment=Left
TitleVerticalAlignment=Center
Animation=120

[Layout]
BorderLeft=0
BorderRight=0
BorderBottom=0
BorderTop=0
TitleEdgeTop=0
TitleEdgeBottom=0
TitleEdgeLeft=14
TitleEdgeRight={edge}
TitleEdgeTopMaximized=0
TitleEdgeBottomMaximized=0
TitleEdgeLeftMaximized=14
TitleEdgeRightMaximized={edge}
TitleBorderLeft=10
TitleBorderRight=12
TitleHeight={title_h}
ButtonWidth={btn_w}
ButtonWidthMenu=24
ButtonHeight={title_h}
ButtonSpacing={gap}
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
Comment=Lucent OS window decoration (Pebble Drift)
X-KDE-PluginInfo-Author=Lucent OS contributors
X-KDE-PluginInfo-Name={tid}
X-KDE-PluginInfo-Version=2.0
X-KDE-PluginInfo-License=Apache-2.0
X-KDE-PluginInfo-Website=https://github.com/sidun-av/lucent-os
"""


def rgb(hexcol):
    h = hexcol.lstrip("#")
    return ",".join(str(int(h[i:i + 2], 16)) for i in (0, 2, 4))


def main():
    tk = tokens.load()
    for tid, t in (("Lucent", theme(tk.light, False)), ("LucentDark", theme(tk.dark, True))):
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
                                                 title_h=TITLE_H, btn_w=BTN_W, gap=BTN_GAP, edge=EDGE,
                                                 pl=pl, pt=pt, pr=pr, pb=pb))
        (base / "metadata.desktop").write_text(META.format(name=t["name"], tid=tid))
        print("wrote", base, "padding", pad)


if __name__ == "__main__":
    main()
