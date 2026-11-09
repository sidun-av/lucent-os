#!/usr/bin/env python3
"""Generate the Lucent Plasma desktop themes (light and dark).

Only the parts that define the Lucent look are generated; everything else
falls back to Plasma's default (Breeze) theme:

  widgets/panel-background   floating taskbar: radius 20, translucent, blurred
  dialogs/background         popups (tray, calendar, launcher menus): radius 16
  widgets/tooltip            hover previews: radius 16
  widgets/tasks              taskbar buttons: active tile + accent pill, running dot
  widgets/viewitem           list highlights in popups: radius 9
  widgets/tabbar             tab underline; no "popup open" line on the taskbar
  widgets/lineedit           text fields (login/lock password, popup search)

Values come from docs/mockups/lucent.css (#taskbar, .preview, .di ...).
Output: system_files/usr/share/plasma/desktoptheme/lucent{,-dark}/
Run: python3 design/gen_plasma_theme.py   (numpy + pillow)
"""
import gzip
import json
import shutil
from pathlib import Path

import numpy as np

from framekit import (SCALE, Cursor, SvgDoc, crop, hints, nine_slice, over,
                      render_box, rgba, sdf_roundrect, downsample, coverage, SS)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "system_files/usr/share/plasma/desktoptheme"

THEMES = {
    "lucent": dict(
        name="Lucent", dark=False,
        bar="rgba(248,249,252,.70)", bar_solid="rgba(246,247,250,1)", bar_line="rgba(255,255,255,.65)",
        popup="rgba(250,251,253,.86)", popup_solid="rgba(250,251,253,1)", popup_line="rgba(255,255,255,.65)",
        ring="rgba(10,15,30,.08)",
        bar_shadow=("rgba(10,15,30,.20)", 44, 0, 14, 0),
        popup_shadow=("rgba(10,15,30,.24)", 44, 0, 16, 0),
        task_active="rgba(255,255,255,.80)", task_active_line="rgba(20,28,45,.10)",
        hover="rgba(20,28,45,.06)", accent="#3b6ef5", dot="#6a7282", attention="#d98a00",
        sel="rgba(59,110,245,.14)", sel_hover="rgba(59,110,245,.20)", item_hover="rgba(20,28,45,.05)",
    ),
    "lucent-dark": dict(
        name="Lucent Dark", dark=True,
        bar="rgba(30,33,41,.58)", bar_solid="rgba(30,33,41,1)", bar_line="rgba(255,255,255,.12)",
        popup="rgba(34,37,45,.86)", popup_solid="rgba(34,37,45,1)", popup_line="rgba(255,255,255,.12)",
        ring="rgba(0,0,0,.45)",
        bar_shadow=("rgba(0,0,0,.40)", 44, 0, 14, 0),
        popup_shadow=("rgba(0,0,0,.45)", 48, 0, 16, 0),
        task_active="rgba(255,255,255,.12)", task_active_line="rgba(255,255,255,.09)",
        hover="rgba(255,255,255,.07)", accent="#5b8bff", dot="#959cab", attention="#f0b04a",
        sel="rgba(91,139,255,.24)", sel_hover="rgba(91,139,255,.30)", item_hover="rgba(255,255,255,.06)",
    ),
}

# Taskbar geometry (lucent.css #taskbar): 64 px tall, radius 20, 14/12 px from
# the screen edges, 10 px inner padding. Applets get 7 px top/bottom padding
# (the system tray stays on one row only below 52 px). The task manager fills
# the full 64 px, so each task cell is 64x64 with the mockup's 54 px tile
# drawn inside; icons are 48 px (Kirigami snaps to 16/22/32/48) and Lucent's
# app icons keep their tile on an 80 % grid, so the tile shows at ~38 px.
PANEL_R = 20
PANEL_PAD = (10, 7, 10, 7)
FLOAT_GAP = (14, 12, 14, 12)          # left, top, right, bottom
TASK_W = TASK_H = 64
TASK_TILE = (5, 5, 54, 54)
TASK_R = 13
TASK_ICON_PAD = (0, 8, 0, 8)


def shadow_tiles(doc, cur, r, shadow, ring, prefix="shadow"):
    """Window shadow as 8 tiles around a rounded rect, interior cut out.
    Returns the outward margins (l, t, r, b)."""
    col, blur, dx, dy, spread = shadow
    sigma = blur / 2
    ext = int(round(2.6 * sigma))
    ml, mr = ext - dx, ext + dx
    mt, mb = max(ext - dy, 2), ext + dy
    inset = r + 2                      # how far the tiles reach under the frame
    bw = 2 * (inset + ext) + 8         # wide enough that edges are uniform
    bh = 2 * (inset + ext) + 8
    W, H = ml + bw + mr, mt + bh + mb
    img = render_box(W, H, (ml, mt, bw, bh), r, ring=ring, shadows=[shadow])
    cx = ml + bw // 2
    cy = mt + bh // 2
    tl = crop(img, 0, 0, ml + inset, mt + inset)
    tr = crop(img, W - mr - inset, 0, mr + inset, mt + inset)
    bl = crop(img, 0, H - mb - inset, ml + inset, mb + inset)
    br = crop(img, W - mr - inset, H - mb - inset, mr + inset, mb + inset)
    top = crop(img, cx, 0, 4, mt + inset)
    bottom = crop(img, cx, H - mb - inset, 4, mb + inset)
    left = crop(img, 0, cy, ml + inset, 4)
    right = crop(img, W - mr - inset, cy, mr + inset, 4)
    for name, part in (("topleft", tl), ("top", top), ("topright", tr), ("left", left),
                       ("right", right), ("bottomleft", bl), ("bottom", bottom), ("bottomright", br)):
        h, w = part.shape[0] // SCALE, part.shape[1] // SCALE
        x, y = cur.place(w, h)
        doc.image(f"{prefix}-{name}", x, y, part)
    x, y = cur.place(4, 4)
    doc.rect(f"{prefix}-center", x, y, 4, 4)
    hints(doc, cur, prefix, (ml, mt, mr, mb))
    return ml, mt, mr, mb


def frame(doc, cur, prefix, r, fill, line, size=None, mask=True):
    s = size or (2 * r + 8)
    img = render_box(s, s, (0, 0, s, s), r, fill=fill, border=line)
    m = render_box(s, s, (0, 0, s, s), r, fill="#000000") if mask else None
    nine_slice(doc, cur, prefix, img, r, r, r, r, mask=m)


def write(path, doc):
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.GzipFile(path, "wb", mtime=0) as f:
        f.write(doc.svg().encode())


def panel_background(t, solid):
    doc, cur = SvgDoc(0, 0), Cursor()
    fill = t["bar_solid"] if solid else t["bar"]
    frame(doc, cur, "", PANEL_R, fill, t["bar_line"])
    # Same frame under the prefixes Plasma probes for floating / thick panels.
    for pre in ("floating", "thick"):
        img = render_box(48, 48, (0, 0, 48, 48), PANEL_R, fill=fill, border=t["bar_line"])
        nine_slice(doc, cur, pre, img, PANEL_R, PANEL_R, PANEL_R, PANEL_R)
    hints(doc, cur, "", PANEL_PAD)
    # Panel.qml: applet padding = thick margins + smallSpacing (4 px).
    hints(doc, cur, "thick", PANEL_PAD)
    # Panel.qml: the floating gap = floating-hint-*-margin.
    hints(doc, cur, "floating", FLOAT_GAP)
    shadow_tiles(doc, cur, PANEL_R, t["bar_shadow"], t["ring"])
    doc.w, doc.h = cur.max_w, cur.height + 4
    return doc


def dialog_background(t, solid, r=16, margins=(10, 10, 10, 10)):
    doc, cur = SvgDoc(0, 0), Cursor()
    frame(doc, cur, "", r, t["popup_solid"] if solid else t["popup"], t["popup_line"])
    hints(doc, cur, "", margins)
    shadow_tiles(doc, cur, r, t["popup_shadow"], t["ring"])
    doc.w, doc.h = cur.max_w, cur.height + 4
    return doc


def pill(img, cx, y, w, h, color):
    """Draw a rounded pill into a SCALE-resolution premultiplied image."""
    H, W = img.shape[0] // SCALE, img.shape[1] // SCALE
    d = sdf_roundrect(W, H, cx - w / 2, y, w, h, h / 2, SCALE, SS)
    return over(img, rgba(color), downsample(coverage(d), SS))


def task_state(bg=None, line=None, pill_w=0, pill_color=None):
    def draw(img):
        if pill_w:
            x, y, w, h = TASK_TILE
            img = pill(img, x + w / 2, y + h - 3 - 4, pill_w, 4, pill_color)
        return img
    return render_box(TASK_W, TASK_H, TASK_TILE, TASK_R, fill=bg, border=line, extra=draw)


def tasks(t):
    doc, cur = SvgDoc(0, 0), Cursor()
    active = dict(bg=t["task_active"], line=t["task_active_line"], pill_w=18, pill_color=t["accent"])
    running = dict(pill_w=6, pill_color=t["dot"])
    states = {
        "normal": task_state(**running),
        "normal-hover": task_state(bg=t["hover"], **running),
        "minimized": task_state(**running),
        "minimized-hover": task_state(bg=t["hover"], **running),
        "focus": task_state(**active),
        "focus-hover": task_state(**active),
        "attention": task_state(pill_w=18, pill_color=t["attention"]),
        "attention-hover": task_state(bg=t["hover"], pill_w=18, pill_color=t["attention"]),
        "launcher-hover": task_state(bg=t["hover"]),
        "hover": task_state(bg=t["hover"]),
        "progress": task_state(bg=rgba_str(t["accent"], .18)),
    }
    for name, img in states.items():
        # Slice so the bottom-middle piece is exactly the pill's width: then a
        # cell of the designed width shows an un-stretched pill.
        pw = 18 if name.startswith(("focus", "attention")) else 6
        side = (TASK_W - pw) // 2
        nine_slice(doc, cur, name, img, side, TASK_R + 5, TASK_W - side - pw, TASK_R + 5)
    hints(doc, cur, "normal", TASK_ICON_PAD)
    for name in ("focus", "hover", "minimized", "attention", "progress"):
        hints(doc, cur, name, TASK_ICON_PAD)
    doc.w, doc.h = cur.max_w, cur.height + 4
    return doc


def rgba_str(hexcol, a):
    r, g, b, _ = rgba(hexcol)
    return f"rgba({int(r*255)},{int(g*255)},{int(b*255)},{a})"


def tabbar(t):
    """Tab underline as a 3 px rounded accent bar (north = tabs on top, the bar
    under the label). south-active-tab is also the taskbar's "popup open"
    marker on the bar's top edge: left empty, the popup itself shows it."""
    doc, cur = SvgDoc(0, 0), Cursor()
    W = H = 26
    edges = {"north": "bottom", "south": None, "west": "right", "east": "left"}
    for side, edge in edges.items():
        def draw(img, edge=edge):
            if edge is None:
                return img
            Hh, Ww = img.shape[0] // SCALE, img.shape[1] // SCALE
            if edge == "bottom":
                box = (4, Hh - 3, Ww - 8, 3)
            elif edge == "right":
                box = (Ww - 3, 4, 3, Hh - 8)
            else:
                box = (0, 4, 3, Hh - 8)
            d = sdf_roundrect(Ww, Hh, *box, 1.5, SCALE, SS)
            return over(img, rgba(t["accent"]), downsample(coverage(d), SS))
        img = render_box(W, H, (0, 0, W, H), 0, extra=draw)
        nine_slice(doc, cur, f"{side}-active-tab", img, 6, 6, 6, 6)
        hints(doc, cur, f"{side}-active-tab", (6, 10, 6, 10))
    doc.w, doc.h = cur.max_w, cur.height + 4
    return doc


def lineedit(t):
    """Text fields in Plasma (popup search fields, the lock and login screens'
    password field): a translucent rounded field, accent ring on focus."""
    doc, cur = SvgDoc(0, 0), Cursor()
    r = 14
    sz = 2 * r + 8
    dark = t["dark"]
    fill = "rgba(255,255,255,.12)" if dark else "rgba(255,255,255,.78)"
    line = "rgba(255,255,255,.20)" if dark else "rgba(20,28,45,.14)"
    line_hover = "rgba(255,255,255,.32)" if dark else "rgba(20,28,45,.24)"
    for name, col in (("base", line), ("hover", line_hover)):
        img = render_box(sz, sz, (0, 0, sz, sz), r, fill=fill, border=col)
        nine_slice(doc, cur, name, img, r, r, r, r)
        hints(doc, cur, name, (12, 6, 12, 6))
    ring = render_box(sz, sz, (0, 0, sz, sz), r, border=t["accent"], border_w=2)
    nine_slice(doc, cur, "focus", ring, r, r, r, r)
    hints(doc, cur, "focus", (12, 6, 12, 6))
    nine_slice(doc, cur, "focusframe", ring, r, r, r, r)
    hints(doc, cur, "focusframe", (12, 6, 12, 6))
    x, y = cur.place(4, 4)
    doc.rect("hint-focus-over-base", x, y, 2, 2)
    doc.w, doc.h = cur.max_w, cur.height + 4
    return doc


def viewitem(t):
    doc, cur = SvgDoc(0, 0), Cursor()
    r = 9
    for name, col in (("normal", None), ("hover", t["item_hover"]), ("selected", t["sel"]),
                      ("selected+hover", t["sel_hover"])):
        s = 2 * r + 8
        img = render_box(s, s, (0, 0, s, s), r, fill=col)
        nine_slice(doc, cur, name, img, r, r, r, r)
        hints(doc, cur, name, (8, 4, 8, 4))
    doc.w, doc.h = cur.max_w, cur.height + 4
    return doc


def main():
    for tid, t in THEMES.items():
        base = OUT / tid
        if base.exists():
            shutil.rmtree(base)
        for sub in ("", "translucent/"):
            write(base / f"{sub}widgets/panel-background.svgz", panel_background(t, False))
            write(base / f"{sub}dialogs/background.svgz", dialog_background(t, False))
            write(base / f"{sub}widgets/tooltip.svgz", dialog_background(t, False, r=16, margins=(12, 12, 12, 12)))
        for sub in ("solid/", "opaque/"):
            write(base / f"{sub}widgets/panel-background.svgz", panel_background(t, True))
            write(base / f"{sub}dialogs/background.svgz", dialog_background(t, True))
            write(base / f"{sub}widgets/tooltip.svgz", dialog_background(t, True, r=16, margins=(12, 12, 12, 12)))
        write(base / "widgets/tasks.svgz", tasks(t))
        write(base / "widgets/viewitem.svgz", viewitem(t))
        write(base / "widgets/tabbar.svgz", tabbar(t))
        write(base / "widgets/lineedit.svgz", lineedit(t))
        meta = {
            "KPlugin": {
                "Authors": [{"Name": "Lucent OS contributors"}],
                "Description": "Lucent: floating translucent taskbar and rounded popups",
                "Id": tid, "License": "Apache-2.0", "Name": t["name"],
                "Version": "1.0", "Website": "https://github.com/sidun-av/lucent-os",
            },
            "X-Plasma-API-Minimum-Version": "6.0",
        }
        (base / "metadata.json").write_text(json.dumps(meta, indent=4) + "\n")
        # No `colors` file: text follows the active colour scheme.
        (base / "plasmarc").write_text(
            "[ContrastEffect]\n# Behind the translucent taskbar/popups: blur + a little more\n"
            "# saturation, like `backdrop-filter: blur() saturate(1.7)` in the mockups.\n"
            "enabled=true\ncontrast=%s\nintensity=%s\nsaturation=1.7\n\n"
            "[AdaptiveTransparency]\nenabled=true\n" % (("0.25", "1.6") if t["dark"] else ("0.2", "2.0")))
        print("wrote", base)


if __name__ == "__main__":
    main()
