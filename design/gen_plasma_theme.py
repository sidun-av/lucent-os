#!/usr/bin/env python3
"""Generate the Lucent Plasma desktop themes (light and dark) from the
Pebble Drift tokens (pebble-drift.css, design/tokens.py).

Only the parts that define the look are generated; everything else falls
back to Plasma's default (Breeze) theme, coloured by the Lucent scheme:

  widgets/panel-background   the dock (glass.css): a floating, centred card,
                             --glass-dock (translucent/, blurred) or its
                             opaque twin (base, solid/, opaque/), radius 24,
                             top light, --elev-3, 72 px
  dialogs/background         popups, OSD, notifications, calendar, tray:
                             --surface-popover, radius 16, --shadow-popover
  widgets/tooltip            hover previews: the same popover
  widgets/tasks              dock cells: hover = flat --state-hover tile,
                             focused = 14 x 5 accent dash, running = 5 px dot
  widgets/viewitem           list highlights in popups: radius 10
  widgets/tabbar             tab underline; no "popup open" line on the taskbar
  widgets/lineedit           text fields: a sunken well, accent ring on focus

Everything drawn in the accent is a vector shape with
class="ColorScheme-Highlight", so the accent chosen in Settings (KDE's
AccentColor) recolours it; the rest is rasterised (soft shadows).
Output: system_files/usr/share/plasma/desktoptheme/lucent{,-dark}/
Run: python3 design/gen_plasma_theme.py   (numpy + pillow)
"""
import gzip
import json
import shutil
from pathlib import Path

import numpy as np

import tokens
from framekit import (SCALE, Cursor, SvgDoc, crop, hints, nine_slice, over,
                      render_box, rgba, sdf_roundrect, downsample, coverage, SS)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "system_files/usr/share/plasma/desktoptheme"

# Dock geometry (glass.css .dock, .dk): a floating, centred, fit-width card,
# 72 px tall, radius 24 (--r-xl), --glass-dock + KWin blur, --elev-3. Applets
# get 72 - 2 x 11 = 50 px: under 52 px the system tray keeps one row of
# icons (it stacks two rows from 2 x (22 + 4) px). Each task cell is that
# 50 px tile (radius 13); hover = --state-hover, the focused app = a 14 x 5
# accent dash under the 42 px icon, running = a 5 px dot.
PANEL_H = 72
DOCK_R = 24
PANEL_PAD = (10, 11, 10, 11)
FLOAT_GAP = (12, 12, 12, 12)
TASK_W = TASK_H = 50
TASK_TILE = (0, 0, 50, 50)
TASK_R = 13
TASK_ICON_PAD = (4, 2, 4, 6)
BAR_W, BAR_H, BAR_BOTTOM = 14, 5, 1        # .dk.active .run i
DOT, DOT_BOTTOM = 5, 1                     # .dk .run i
POPUP_R = 16


def theme(t: dict, dark: bool, gl: dict | None = None) -> dict:
    gl = gl or tokens.load(tokens.GLASS).mode(dark)
    e3 = tokens.shadows(gl["elev-3"])
    sp = tokens.shadows(t["shadow-popover"])
    sr = tokens.shadows(t["shadow-raised"])
    st = tokens.shadows(t["shadow-taskbar"])
    hl = tokens.shadows(t["highlight-top"])[0][4]
    as_shadow = lambda s: (tokens.rgba_str(s[4]), s[2], s[0], s[1], s[3])  # (col, blur, dx, dy, spread)
    return dict(
        dark=dark, name="Lucent Dark" if dark else "Lucent",
        bar=t["surface-taskbar"], bar_solid=t["surface-window-solid"],
        bar_line=tokens.rgba_str(st[0][4]), bar_shadow=[as_shadow(st[1])], highlight=tokens.rgba_str(hl),
        popup=t["surface-popover"], popup_solid=tokens.flatten(t["surface-popover"], t["surface-window-solid"]),
        popup_ring=tokens.rgba_str(sp[0][4]), popup_shadow=[as_shadow(s) for s in sp[1:]],
        raised=t["surface-raised"], raised2=t["surface-raised-2"],
        raised_ring=tokens.rgba_str(sr[0][4]), raised_drop=[as_shadow(s) for s in sr[1:]],
        hover=t["state-hover"], pressed=t["state-pressed"],
        well=t["surface-sunken"], well_strong=t["surface-sunken-strong"],
        well_shadow=tokens.shadows(t["shadow-sunken"])[0][4], well_ring=tokens.shadows(t["shadow-sunken"])[1][4],
        dot=t["text-tertiary"], attention=t["status-warning"], accent=t["accent"],
        soft_a=0.12 if not dark else 0.18, soft_strong_a=0.20 if not dark else 0.28,
        # Glass Card dock
        dock=gl["glass-dock"], dock_solid=gl["glass-dock-solid"], dock_ring=tokens.rgba_str(e3[0][4]),
        dock_shadow=[as_shadow(s) for s in e3[1:]],
        glass_hl=tokens.rgba_str(tokens.shadows(gl["glass-highlight"])[0][4]),
        dk_hover=gl["state-hover"], dk_dot=gl["text-tertiary"],
    )


def hl_rect(x, y, w, h, r=0, opacity=1.0):
    """A vector rectangle in the current accent (KSvg colour class)."""
    op = f"fill-opacity:{opacity:g};" if opacity < 1 else ""
    return (f'<rect class="ColorScheme-Highlight" x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" '
            f'rx="{r:g}" style="fill:currentColor;{op}stroke:none"/>')


def hl_ring(x, y, w, h, r, sw):
    """An accent outline drawn inside the box (stroke centred sw/2 in)."""
    return (f'<rect class="ColorScheme-Highlight" x="{x + sw / 2:g}" y="{y + sw / 2:g}" width="{w - sw:g}" '
            f'height="{h - sw:g}" rx="{max(r - sw / 2, 0):g}" style="fill:none;stroke:currentColor;stroke-width:{sw:g}"/>')


def quarter_ring(cx, cy, sx, sy, r, sw, opacity=1.0):
    """The corner of an accent outline: a filled quarter annulus around
    (cx, cy), facing (sx, sy) = (-1|1, -1|1)."""
    sweep = 1 if sx * sy > 0 else 0
    ri = r - sw
    op = f"fill-opacity:{opacity:g};" if opacity < 1 else ""
    return (f'<path class="ColorScheme-Highlight" d="M{cx + sx * r:g},{cy:g} A{r},{r} 0 0 {sweep} {cx:g},{cy + sy * r:g} '
            f'L{cx:g},{cy + sy * ri:g} A{ri},{ri} 0 0 {1 - sweep} {cx + sx * ri:g},{cy:g} Z" '
            f'style="fill:currentColor;{op}stroke:none"/>')


def shadow_tiles(doc, cur, r, shadows, ring, prefix="shadow"):
    """A soft shadow as 8 tiles around a rounded rect, interior cut out.
    shadows: [(css colour, blur, dx, dy, spread)]. Returns the margins."""
    ext = max(int(round(1.1 * blur + spread)) + abs(dx) for _, blur, dx, dy, spread in shadows)
    ml = mr = ext
    mt = max(max(int(round(1.1 * b + s)) - dy for _, b, _, dy, s in shadows), 2)
    mb = max(int(round(1.1 * b + s)) + dy for _, b, _, dy, s in shadows)
    inset = r + 2                      # how far the tiles reach under the frame
    bw = 2 * (inset + ext) + 8         # wide enough that edges are uniform
    bh = 2 * (inset + max(mt, mb)) + 8
    W, H = ml + bw + mr, mt + bh + mb
    img = render_box(W, H, (ml, mt, bw, bh), r, ring=ring, shadows=shadows)
    cx = ml + bw // 2
    cy = mt + bh // 2
    tiles = {
        "topleft": crop(img, 0, 0, ml + inset, mt + inset),
        "top": crop(img, cx, 0, 4, mt + inset),
        "topright": crop(img, W - mr - inset, 0, mr + inset, mt + inset),
        "left": crop(img, 0, cy, ml + inset, 4),
        "right": crop(img, W - mr - inset, cy, mr + inset, 4),
        "bottomleft": crop(img, 0, H - mb - inset, ml + inset, mb + inset),
        "bottom": crop(img, cx, H - mb - inset, 4, mb + inset),
        "bottomright": crop(img, W - mr - inset, H - mb - inset, mr + inset, mb + inset),
    }
    for name, part in tiles.items():
        h, w = part.shape[0] // SCALE, part.shape[1] // SCALE
        x, y = cur.place(w, h)
        doc.image(f"{prefix}-{name}", x, y, part)
    x, y = cur.place(4, 4)
    doc.rect(f"{prefix}-center", x, y, 4, 4)
    hints(doc, cur, prefix, (ml, mt, mr, mb))
    return ml, mt, mr, mb


def top_light(W, H, box, r, color):
    """--highlight-top: a 1 px light along the inside top edge."""
    x, y, w, h = box

    def draw(img):
        a = downsample(coverage(sdf_roundrect(W, H, x, y, w, h, r, SCALE, SS)), SS)
        b = downsample(coverage(sdf_roundrect(W, H, x, y + 1, w, h, r, SCALE, SS)), SS)
        return over(img, rgba(color), np.clip(a - b, 0, 1))
    return draw


def popover(s, r, fill, t):
    return render_box(s, s, (0, 0, s, s), r, fill=fill, border=t["popup_ring"],
                      extra=top_light(s, s, (0, 0, s, s), r, t["highlight"]))


def write(path, doc):
    # Plasma tiles frame edges unless told to stretch them: a tiled accent
    # underline turns into dashes, a tiled pill edge into a seam.
    if not any('id="hint-stretch-borders"' in i for i in doc.items):
        doc.rect("hint-stretch-borders", 0, doc.h, 1, 1)
        doc.h += 2
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.GzipFile(path, "wb", mtime=0) as f:
        f.write(doc.svg().encode())


def panel_background(t, solid):
    """The dock (glass.css .dock): a rounded card, --glass-dock (blurred by
    KWin through the mask) or its opaque twin, a hairline ring, the 1 px top
    light of --glass-highlight and the --elev-3 drop. When the panel stops
    floating (a maximised window), Plasma turns off the bottom border and the
    adaptive opacity switches to solid/."""
    doc, cur = SvgDoc(0, 0), Cursor()
    r = DOCK_R
    s = 2 * r + 8
    fill = t["dock_solid"] if solid else tokens.rgba_str(t["dock"])
    img = render_box(s, s, (0, 0, s, s), r, fill=fill, border=t["dock_ring"],
                     extra=top_light(s, s, (0, 0, s, s), r, t["glass_hl"]))
    mask = render_box(s, s, (0, 0, s, s), r, fill="#000000")
    for pre in ("", "floating", "thick"):
        nine_slice(doc, cur, pre, img, r, r, r, r, mask=mask)
    hints(doc, cur, "", PANEL_PAD)
    # Panel.qml: applet padding = thick margins + smallSpacing (4 px).
    hints(doc, cur, "thick", PANEL_PAD)
    # Panel.qml: the gap between the floating dock and the screen edge.
    hints(doc, cur, "floating", FLOAT_GAP)
    shadow_tiles(doc, cur, r, t["dock_shadow"], t["dock_ring"])
    doc.w, doc.h = cur.max_w, cur.height + 4
    return doc


def dialog_background(t, solid, r=POPUP_R, margins=(10, 10, 10, 10)):
    doc, cur = SvgDoc(0, 0), Cursor()
    s = 2 * r + 8
    fill = t["popup_solid"] if solid else tokens.rgba_str(t["popup"])
    img = popover(s, r, fill, t)
    mask = render_box(s, s, (0, 0, s, s), r, fill="#000000")
    nine_slice(doc, cur, "", img, r, r, r, r, mask=mask)
    hints(doc, cur, "", margins)
    shadow_tiles(doc, cur, r, t["popup_shadow"], t["popup_ring"])
    doc.w, doc.h = cur.max_w, cur.height + 4
    return doc


def hover_tile(t, color=None):
    """.dk.hover: a flat --state-hover tile, no shadow (nothing is raised)."""
    return render_box(TASK_W, TASK_H, TASK_TILE, TASK_R, fill=tokens.rgba_str(color or t["dk_hover"]))


def dot_img(img, color):
    x, y, w, h = TASK_TILE
    cx, cy = x + w / 2, y + h - DOT_BOTTOM - DOT
    d = sdf_roundrect(TASK_W, TASK_H, cx - DOT / 2, cy, DOT, DOT, DOT / 2, SCALE, SS)
    return over(img, rgba(color), downsample(coverage(d), SS))


def bar_svg(color=None):
    x, y, w, h = TASK_TILE
    bx, by = x + (w - BAR_W) / 2, y + h - BAR_BOTTOM - BAR_H
    if color:
        r, g, b, _ = tokens.color(color)
        return (f'<rect x="{bx:g}" y="{by:g}" width="{BAR_W}" height="{BAR_H}" rx="2.5" '
                f'style="fill:{tokens.hexcolor((r, g, b))};stroke:none"/>')
    return hl_rect(bx, by, BAR_W, BAR_H, 2.5)


def tasks(t):
    doc, cur = SvgDoc(0, 0), Cursor()
    empty = np.zeros((TASK_H * SCALE, TASK_W * SCALE, 4), np.float32)
    hover = hover_tile(t)
    x, y, w, h = TASK_TILE
    states = {   # name: (raster, vector overlay on the bottom-middle piece)
        "normal": (dot_img(empty, t["dk_dot"]), ""),
        "normal-hover": (dot_img(hover, t["dk_dot"]), ""),
        "minimized": (dot_img(empty, t["dk_dot"]), ""),
        "minimized-hover": (dot_img(hover, t["dk_dot"]), ""),
        "focus": (empty, bar_svg()),
        "focus-hover": (hover, bar_svg()),
        "attention": (empty, bar_svg(t["attention"])),
        "attention-hover": (hover, bar_svg(t["attention"])),
        "launcher-hover": (hover, ""),
        "hover": (hover, ""),
        # progress (drawn behind the icon, clipped to the progress): an accent-soft tile
        "progress": (render_box(TASK_W, TASK_H, TASK_TILE, TASK_R, fill=tokens.rgba_str(t["accent"], t["soft_a"])), ""),
    }
    for name, (img, overlay) in states.items():
        # Slice so the bottom-middle piece is exactly the bar's (or dot's)
        # width: a cell of the designed width shows them un-stretched, and
        # the vector bar lies wholly inside that piece.
        pw = BAR_W if overlay or name.startswith(("focus", "attention")) else DOT
        side = (TASK_W - pw) // 2
        bottom_h = TASK_H - (y + h - TASK_R) + 0
        nine_slice(doc, cur, name, img, side, y + TASK_R + 1, TASK_W - side - pw, bottom_h,
                   overlays={"bottom": overlay} if overlay else None)
    hints(doc, cur, "normal", TASK_ICON_PAD)
    for name in ("focus", "hover", "minimized", "attention", "progress"):
        hints(doc, cur, name, TASK_ICON_PAD)
    doc.w, doc.h = cur.max_w, cur.height + 4
    return doc


def tabbar(t):
    """Tab underline as a 3 px rounded accent bar (north = tabs on top, the bar
    under the label). south-active-tab is also the taskbar's "popup open"
    marker on the bar's top edge: left empty, the popup itself shows it."""
    doc, cur = SvgDoc(0, 0), Cursor()
    W = H = 26
    blank = np.zeros((H * SCALE, W * SCALE, 4), np.float32)
    edges = {"north": ("bottom", (6, H - 3, W - 12, 3)), "south": (None, None),
             "west": ("right", (W - 3, 6, 3, H - 12)), "east": ("left", (0, 6, 3, H - 12))}
    for side, (edge, box) in edges.items():
        ov = {}
        if edge:
            bx, by, bw, bh = box
            # one piece holds the whole bar: the edge piece on that side
            ov = {edge: hl_rect(bx, by, bw, bh, 1.5)}
        nine_slice(doc, cur, f"{side}-active-tab", blank, 6, 6, 6, 6, overlays=ov or None)
        hints(doc, cur, f"{side}-active-tab", (6, 10, 6, 10))
    doc.w, doc.h = cur.max_w, cur.height + 4
    return doc


def lineedit(t):
    """Text fields in Plasma (popup search fields, the lock and login
    screens' password field): a sunken well (.field), accent ring on focus."""
    doc, cur = SvgDoc(0, 0), Cursor()
    r = 10
    sz = 2 * r + 8

    def well(fill):
        def inner(img):
            a = downsample(coverage(sdf_roundrect(sz, sz, 0, 1, sz, sz, r, SCALE, SS)), SS)
            b = downsample(coverage(sdf_roundrect(sz, sz, 0, 2, sz, sz, r, SCALE, SS)), SS)
            return over(img, rgba(tokens.rgba_str(t["well_shadow"])), np.clip(a - b, 0, 1))
        return render_box(sz, sz, (0, 0, sz, sz), r, fill=tokens.rgba_str(fill),
                          border=tokens.rgba_str(t["well_ring"]), extra=inner)
    for name, fill in (("base", t["well"]), ("hover", t["well_strong"])):
        nine_slice(doc, cur, name, well(fill), r, r, r, r)
        hints(doc, cur, name, (12, 6, 12, 6))
    blank = np.zeros((sz * SCALE, sz * SCALE, 4), np.float32)
    # the focus ring: four straight accent edges + four vector corner arcs
    for name in ("focus", "focusframe"):
        ov = {}
        sw = 2
        # filled quarter rings (a stroke's bounds would spill out of the cell)
        for piece, (cx, cy, sx, sy) in {"topleft": (r, r, -1, -1), "topright": (sz - r, r, 1, -1),
                                        "bottomleft": (r, sz - r, -1, 1), "bottomright": (sz - r, sz - r, 1, 1)}.items():
            ov[piece] = quarter_ring(cx, cy, sx, sy, r, sw)
        ov["top"] = hl_rect(r, 0, sz - 2 * r, sw)
        ov["bottom"] = hl_rect(r, sz - sw, sz - 2 * r, sw)
        ov["left"] = hl_rect(0, r, sw, sz - 2 * r)
        ov["right"] = hl_rect(sz - sw, r, sw, sz - 2 * r)
        nine_slice(doc, cur, name, blank, r, r, r, r, overlays=ov)
        hints(doc, cur, name, (12, 6, 12, 6))
    x, y = cur.place(4, 4)
    doc.rect("hint-focus-over-base", x, y, 2, 2)
    doc.w, doc.h = cur.max_w, cur.height + 4
    return doc


def arrows(t):
    """widgets/arrows (the tray's overflow arrow, spin and combo arrows): the
    mockups' line chevrons (lucent.js, 1.8 stroke, round) in the text
    colour, instead of Breeze's filled triangles."""
    doc, cur = SvgDoc(0, 0), Cursor()
    S = 22
    pts = {"up": "6.5,13.5 11,9 15.5,13.5", "down": "6.5,8.5 11,13 15.5,8.5",
           "left": "13.5,6.5 9,11 13.5,15.5", "right": "8.5,6.5 13,11 8.5,15.5"}
    for d, p in pts.items():
        x, y = cur.place(S, S)
        doc.raw(f'<g id="{d}-arrow" transform="translate({x},{y})">'
                f'<rect width="{S}" height="{S}" style="fill:#000;fill-opacity:0;stroke:none"/>'
                f'<polyline class="ColorScheme-Text" points="{p}" style="fill:none;stroke:currentColor;'
                f'stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round"/></g>')
    doc.w, doc.h = cur.max_w, cur.height + 4
    return doc


def viewitem(t):
    """Popup list highlights: hover --state-hover, selection --accent-soft."""
    doc, cur = SvgDoc(0, 0), Cursor()
    r = 10
    s = 2 * r + 8
    blank = np.zeros((s * SCALE, s * SCALE, 4), np.float32)

    def pieces(opacity):
        """A rounded accent rect cut into 9 vector pieces."""
        out = {}
        def corner(cx, cy, sx, sy):
            # quarter disc of radius r with its centre at (cx, cy), facing (sx, sy)
            x0, y0 = cx + sx * r, cy
            x1, y1 = cx, cy + sy * r
            sweep = 1 if sx * sy > 0 else 0
            return (f'<path class="ColorScheme-Highlight" d="M{cx},{cy} L{x0},{y0} A{r},{r} 0 0 {sweep} {x1},{y1} Z" '
                    f'style="fill:currentColor;fill-opacity:{opacity:g};stroke:none"/>')
        out["topleft"] = corner(r, r, -1, -1)
        out["topright"] = corner(s - r, r, 1, -1)
        out["bottomleft"] = corner(r, s - r, -1, 1)
        out["bottomright"] = corner(s - r, s - r, 1, 1)
        out["top"] = hl_rect(r, 0, s - 2 * r, r, 0, opacity)
        out["bottom"] = hl_rect(r, s - r, s - 2 * r, r, 0, opacity)
        out["left"] = hl_rect(0, r, r, s - 2 * r, 0, opacity)
        out["right"] = hl_rect(s - r, r, r, s - 2 * r, 0, opacity)
        out["center"] = hl_rect(r, r, s - 2 * r, s - 2 * r, 0, opacity)
        return out
    img = render_box(s, s, (0, 0, s, s), r)
    nine_slice(doc, cur, "normal", img, r, r, r, r)
    hints(doc, cur, "normal", (8, 4, 8, 4))
    nine_slice(doc, cur, "hover", render_box(s, s, (0, 0, s, s), r, fill=tokens.rgba_str(t["hover"])), r, r, r, r)
    hints(doc, cur, "hover", (8, 4, 8, 4))
    for name, a in (("selected", t["soft_a"]), ("selected+hover", t["soft_strong_a"])):
        nine_slice(doc, cur, name, blank, r, r, r, r, overlays=pieces(a))
        hints(doc, cur, name, (8, 4, 8, 4))
    doc.w, doc.h = cur.max_w, cur.height + 4
    return doc


def main():
    tk = tokens.load()
    for tid, t in (("lucent", theme(tk.light, False)), ("lucent-dark", theme(tk.dark, True))):
        base = OUT / tid
        if base.exists():
            shutil.rmtree(base)
        # translucent/ is what Plasma picks when KWin can blur; without blur
        # (QPainter / software rendering) the base files apply: the opaque twin.
        for sub in ("translucent/",):
            write(base / f"{sub}widgets/panel-background.svgz", panel_background(t, False))
            write(base / f"{sub}dialogs/background.svgz", dialog_background(t, False))
            write(base / f"{sub}widgets/tooltip.svgz", dialog_background(t, False, margins=(12, 12, 12, 12)))
        for sub in ("", "solid/", "opaque/"):
            write(base / f"{sub}widgets/panel-background.svgz", panel_background(t, True))
            write(base / f"{sub}dialogs/background.svgz", dialog_background(t, True))
            write(base / f"{sub}widgets/tooltip.svgz", dialog_background(t, True, margins=(12, 12, 12, 12)))
        write(base / "widgets/tasks.svgz", tasks(t))
        write(base / "widgets/viewitem.svgz", viewitem(t))
        write(base / "widgets/tabbar.svgz", tabbar(t))
        write(base / "widgets/lineedit.svgz", lineedit(t))
        write(base / "widgets/arrows.svgz", arrows(t))
        meta = {
            "KPlugin": {
                "Authors": [{"Name": "Lucent OS contributors"}],
                "Description": "Lucent (Glass Card): floating glass dock and popovers",
                "Id": tid, "License": "Apache-2.0", "Name": t["name"],
                "Version": "2.0", "Website": "https://github.com/sidun-av/lucent-os",
            },
            "X-Plasma-API-Minimum-Version": "6.0",
        }
        (base / "metadata.json").write_text(json.dumps(meta, indent=4) + "\n")
        # No `colors` file: text and the accent follow the active colour scheme.
        (base / "plasmarc").write_text(
            "[ContrastEffect]\n# Pebble Drift: surfaces are >= 93 % opaque; the light blur behind them\n"
            "# gets no saturation or contrast boost.\nenabled=false\n\n"
            "[AdaptiveTransparency]\nenabled=true\n")
        print("wrote", base)


if __name__ == "__main__":
    main()
