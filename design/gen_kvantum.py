#!/usr/bin/env python3
"""Generate the Lucent Kvantum theme (widget style for Qt apps), light + dark.

Breeze has no knobs for radii, field shapes or menu metrics, so native Qt
apps (Dolphin, System Settings' widgets, Konsole, Ark, Okular...) are drawn
with Kvantum, an SVG-driven Qt style. This script writes one theme folder
with both variants (Kvantum's "Dark in the light folder" layout):

  Lucent/Lucent.kvconfig + Lucent.svg            widgetStyle=kvantum
  Lucent/LucentDark.kvconfig + LucentDark.svg    widgetStyle=kvantum-dark

Shapes and colours come from docs/mockups/lucent.css:
  fields and push buttons   --field, radius 10, no border (buttons: 1 px --line)
  tool buttons              flat; grouped toolbar buttons form a segmented
                            control (.seg): --field track, raised --win-bg segment
  menus / combo popups      --popup-bg, radius 12, 1 px line, soft shadow
  menu items, list items    radius 8 pills: hover --hover, selection --sel
  scrollbars                thin overlay pills (transient)
  checkboxes / radios       .chk: 18 px, radius 6, accent when on
Every element Kvantum's built-in default theme would otherwise supply is
generated here, so nothing falls back to its dark "Enlightenment" look.

Run: python3 design/gen_kvantum.py
Output: system_files/usr/share/Kvantum/Lucent/
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "system_files/usr/share/Kvantum/Lucent"

LIGHT = dict(
    name="Lucent", dark=False,
    text="#1b1f27", text2="#4c5463", text3="#6a7282", disabled="#9aa1ae",
    window="#f4f5f8", base="#ffffff", alt_base="#f7f8fa", field="#eceef3",
    field_hover="#e4e7ee", field_press="#dce0e8", seg_on="#ffffff",
    line="rgba(20,28,45,.10)", line_strong="rgba(20,28,45,.16)", line_btn="rgba(20,28,45,.12)",
    hover="rgba(20,28,45,.05)", press="rgba(20,28,45,.09)",
    sel="rgba(59,110,245,.14)", sel_soft="rgba(59,110,245,.10)", sel_hover="rgba(59,110,245,.20)", sel_press="rgba(59,110,245,.24)",
    accent="#3b6ef5", accent_hover="#2f5fe0", accent_text="#ffffff",
    # Selections (text, Dolphin's items) are a light accent tint with normal
    # text, like the mockups' --sel; apps that paint selected text with the
    # palette's HighlightedText (Dolphin) then stay readable on the tinted pill.
    text_sel="#c9d7fd",
    popup="rgba(250,251,253,.92)", popup_line="rgba(20,28,45,.10)",
    shadow="rgba(10,15,30,.16)", tooltip="rgba(250,251,253,.97)",
    scroll="rgba(20,28,45,.30)", scroll_hover="rgba(20,28,45,.45)",
    check_border="rgba(20,28,45,.28)", check_bg="#ffffff",
    link="#2f5fe0", visited="#7c4dc4", focus="rgba(59,110,245,.55)",
)
DARK = dict(
    name="LucentDark", dark=True,
    text="#eef0f5", text2="#b4bac6", text3="#959cab", disabled="#6c7380",
    window="#191b21", base="#1f2229", alt_base="#23262d", field="#2b2f38",
    field_hover="#323743", field_press="#383e4b", seg_on="#3a404d",
    line="rgba(255,255,255,.09)", line_strong="rgba(255,255,255,.15)", line_btn="rgba(255,255,255,.08)",
    hover="rgba(255,255,255,.06)", press="rgba(255,255,255,.10)",
    sel="rgba(91,139,255,.22)", sel_soft="rgba(91,139,255,.16)", sel_hover="rgba(91,139,255,.28)", sel_press="rgba(91,139,255,.34)",
    accent="#5b8bff", accent_hover="#6e98ff", accent_text="#ffffff",
    text_sel="#2f4a8f",
    popup="rgba(34,37,45,.94)", popup_line="rgba(255,255,255,.10)",
    shadow="rgba(0,0,0,.38)", tooltip="rgba(34,37,45,.98)",
    scroll="rgba(255,255,255,.30)", scroll_hover="rgba(255,255,255,.45)",
    check_border="rgba(255,255,255,.30)", check_bg="#1f2229",
    link="#7ea4ff", visited="#b08cff", focus="rgba(91,139,255,.60)",
)
NONE = "none"


def css2svg(c):
    """'rgba(r,g,b,a)' -> ('#rrggbb', a); '#rrggbb' -> (c, 1)."""
    if c == NONE:
        return NONE, 0.0
    if c.startswith("#"):
        return c, 1.0
    r, g, b, a = (v.strip() for v in c[c.index("(") + 1:-1].split(","))
    return "#%02x%02x%02x" % (int(r), int(g), int(b)), float(a)


def paint(c, attr="fill"):
    col, a = css2svg(c)
    if col == NONE:
        return f'{attr}="none"'
    return f'{attr}="{col}"' + (f' {attr}-opacity="{a:g}"' if a < 1 else "")


def kvcolor(c):
    """Kvantum colours are #RRGGBB or #RRGGBBAA."""
    col, a = css2svg(c)
    return col if a >= 1 else col + "%02x" % round(a * 255)


class Svg:
    def __init__(self):
        self.items, self.defs = [], []
        self.x = self.y = self.rowh = 0
        self.ids = set()
        self.grad = 0

    def _slot(self, w, h):
        if self.x + w > 1600:
            self.x, self.y, self.rowh = 0, self.y + self.rowh + 8, 0
        x, y = self.x, self.y
        self.x += w + 8
        self.rowh = max(self.rowh, h)
        return x, y

    def add(self, eid, w, h, body=""):
        """An element `eid` of size w x h whose content is drawn in local
        coordinates. An invisible rect fixes its bounds, which Kvantum uses."""
        assert eid not in self.ids, eid
        self.ids.add(eid)
        x, y = self._slot(w, h)
        self.items.append(f'<g id="{eid}" transform="translate({x},{y})">'
                          f'<rect width="{w}" height="{h}" fill="#000000" fill-opacity="0"/>{body}</g>')

    def gradient(self, kind, stops, **attrs):
        self.grad += 1
        gid = f"g{self.grad}"
        st = "".join(f'<stop offset="{o:g}" stop-color="{css2svg(c)[0]}" stop-opacity="{css2svg(c)[1]:g}"/>'
                     for o, c in stops)
        a = " ".join(f'{k}="{v}"' for k, v in attrs.items())
        self.defs.append(f'<{kind} id="{gid}" {a}>{st}</{kind}>')
        return f"url(#{gid})"

    def text(self):
        return ('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
                f'width="1600" height="{self.y + self.rowh + 8}">\n'
                f'<defs>{"".join(self.defs)}</defs>\n' + "\n".join(self.items) + "\n</svg>\n")


# ---------------------------------------------------------------- frames ----
def corner_paths(S, R, ix, iy, sw):
    """Top-left corner in an S x S cell: shape starts at (ix, iy), radius R.
    Returns (fill path, stroke path or '')."""
    def outline(o):
        x0, y0, r = ix + o, iy + o, max(R - o, 0)
        return x0, y0, r
    x0, y0, r = outline(sw)
    fill = (f"M{x0},{S} L{x0},{iy + R} A{r},{r} 0 0 1 {ix + R},{y0} L{S},{y0} L{S},{S} Z" if r
            else f"M{x0},{S} L{x0},{y0} L{S},{y0} L{S},{S} Z")
    if not sw:
        return fill, ""
    stroke = (f"M{ix},{S} L{ix},{iy + R} A{R},{R} 0 0 1 {ix + R},{iy} L{S},{iy} L{S},{iy + sw} "
              f"L{ix + R},{iy + sw} A{R - sw},{R - sw} 0 0 0 {ix + sw},{iy + R} L{ix + sw},{S} Z")
    return fill, stroke


MIRROR = {  # corner -> transform of the top-left drawing inside an S x S cell
    "topleft": "", "topright": "translate({S},0) scale(-1,1)",
    "bottomleft": "translate(0,{S}) scale(1,-1)", "bottomright": "translate({S},{S}) scale(-1,-1)",
}


def frame(svg, name, S, R, fill, stroke=NONE, sw=1, ix=0, iy=0, interior=True, edge=24):
    """Nine objects of a rounded box: name-{corners,edges} and the interior
    `name`. S = frame thickness (= corner cell size), R = radius,
    ix/iy = transparent inset before the shape starts."""
    has_stroke = stroke != NONE
    s = sw if has_stroke else 0
    fpath, spath = corner_paths(S, R, ix, iy, s)
    body = f'<path d="{fpath}" {paint(fill)}/>' + (f'<path d="{spath}" {paint(stroke)}/>' if s else "")
    for pos, tr in MIRROR.items():
        t = tr.format(S=S)
        svg.add(f"{name}-{pos}", S, S, f'<g transform="{t}">{body}</g>' if t else body)
    # edges: top/bottom are S tall, left/right S wide; they get stretched
    def hedge(inset):
        b = f'<rect x="0" y="{inset + s}" width="{edge}" height="{S - inset - s}" {paint(fill)}/>'
        if s:
            b += f'<rect x="0" y="{inset}" width="{edge}" height="{s}" {paint(stroke)}/>'
        return b
    def vedge(inset):
        b = f'<rect x="{inset + s}" y="0" width="{S - inset - s}" height="{edge}" {paint(fill)}/>'
        if s:
            b += f'<rect x="{inset}" y="0" width="{s}" height="{edge}" {paint(stroke)}/>'
        return b
    svg.add(f"{name}-top", edge, S, hedge(iy))
    svg.add(f"{name}-bottom", edge, S, f'<g transform="translate(0,{S}) scale(1,-1)">{hedge(iy)}</g>')
    svg.add(f"{name}-left", S, edge, vedge(ix))
    svg.add(f"{name}-right", S, edge, f'<g transform="translate({S},0) scale(-1,1)">{vedge(ix)}</g>')
    if interior:
        svg.add(name, edge, edge, f'<rect width="{edge}" height="{edge}" {paint(fill)}/>')


def box(svg, el, state, R, fill, stroke=NONE, F=3, ix=0, iy=0, expand=True):
    """A state of a framed element: usual objects with F px frames (used by
    Kvantum in tight spots) plus `expand-` objects drawn with the real radius
    (frame.expansion = 2 * (R + inset) in the kvconfig)."""
    frame(svg, f"{el}-{state}", F, min(R, F), fill, stroke, ix=min(ix, 1), iy=min(iy, 1))
    if expand:
        S = R + max(ix, iy)
        frame(svg, f"expand-{el}-{state}", S, R, fill, stroke, ix=ix, iy=iy)


def empty(svg, eid, w=8, h=8):
    svg.add(eid, w, h)


def empty_frame(svg, name):
    for pos in list(MIRROR) + ["top", "bottom", "left", "right"]:
        empty(svg, f"{name}-{pos}")
    empty(svg, name)


# ------------------------------------------------------------ indicators ----
def chevron(svg, eid, direction, color, size=16, w=1.6):
    pts = {"down": "4.5,6.5 8,10 11.5,6.5", "up": "4.5,9.5 8,6 11.5,9.5",
           "right": "6.5,4.5 10,8 6.5,11.5", "left": "9.5,4.5 6,8 9.5,11.5"}[direction]
    col, a = css2svg(color)
    op = f' stroke-opacity="{a:g}"' if a < 1 else ""
    svg.add(eid, size, size, f'<polyline points="{pts}" fill="none" stroke="{col}"{op} stroke-width="{w}" '
                             f'stroke-linecap="round" stroke-linejoin="round"/>')


def plusminus(svg, eid, plus, color, size=16):
    col, a = css2svg(color)
    op = f' stroke-opacity="{a:g}"' if a < 1 else ""
    d = "M4.5,8 H11.5" + (" M8,4.5 V11.5" if plus else "")
    svg.add(eid, size, size, f'<path d="{d}" fill="none" stroke="{col}"{op} stroke-width="1.6" stroke-linecap="round"/>')


def arrows(svg, base, t, flat=False):
    states = {"normal": t["text2"], "focused": t["text"], "pressed": t["text"],
              "toggled": t["text"], "disabled": t["disabled"]}
    for d in ("up", "down", "left", "right"):
        for st, c in states.items():
            chevron(svg, f"{base}-{d}-{st}", d, c)
    for st in ("normal", "focused", "pressed", "disabled"):
        plusminus(svg, f"{base}-plus-{st}", True, states[st])
        plusminus(svg, f"{base}-minus-{st}", False, states[st])


def checkbox(svg, t, prefix=""):
    S = 18
    def sq(fill, stroke, mark=""):
        b = f'<rect x="0.75" y="0.75" width="16.5" height="16.5" rx="5.25" {paint(fill)} {paint(stroke, "stroke")} stroke-width="1.5"/>'
        return b + mark
    tick = '<polyline points="5,9.3 7.8,12 13,6.4" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
    dash = '<path d="M5.5,9 H12.5" stroke="#ffffff" stroke-width="2" stroke-linecap="round"/>'
    on = lambda c: f'<rect width="18" height="18" rx="6" {paint(c)}/>'
    p = prefix
    svg.add(f"{p}checkbox-normal", S, S, sq(t["check_bg"], t["check_border"]))
    svg.add(f"{p}checkbox-focused", S, S, sq(t["check_bg"], t["accent"]))
    svg.add(f"{p}checkbox-pressed", S, S, sq(t["field"], t["accent"]))
    svg.add(f"{p}checkbox-disabled", S, S, sq(t["field"], t["line_strong"]))
    for st, c in (("normal", t["accent"]), ("focused", t["accent_hover"]), ("pressed", t["accent_hover"]),
                  ("disabled", t["disabled"])):
        svg.add(f"{p}checkbox-checked-{st}", S, S, on(c) + tick)
        svg.add(f"{p}checkbox-tristate-{st}", S, S, on(c) + dash)


def radio(svg, t, prefix=""):
    S = 18
    ring = lambda fill, stroke: f'<circle cx="9" cy="9" r="8.25" {paint(fill)} {paint(stroke, "stroke")} stroke-width="1.5"/>'
    p = prefix
    svg.add(f"{p}radio-normal", S, S, ring(t["check_bg"], t["check_border"]))
    svg.add(f"{p}radio-focused", S, S, ring(t["check_bg"], t["accent"]))
    svg.add(f"{p}radio-pressed", S, S, ring(t["field"], t["accent"]))
    svg.add(f"{p}radio-disabled", S, S, ring(t["field"], t["line_strong"]))
    for st, c in (("normal", t["accent"]), ("focused", t["accent_hover"]), ("pressed", t["accent_hover"]),
                  ("disabled", t["disabled"])):
        svg.add(f"{p}radio-checked-{st}", S, S, f'<circle cx="9" cy="9" r="9" {paint(c)}/>'
                                              f'<circle cx="9" cy="9" r="3.6" fill="#ffffff"/>')


# ----------------------------------------------------------------- popups ---
def popup(svg, name, d, F, fill, line, shadow, dy=0):
    """`name-shadow-*` frame (soft shadow d px + rounded body F px) and the
    `name-normal` interior, plus the shadow-hint rects Kvantum measures."""
    T = d + F
    sc, sa = css2svg(shadow)
    R = F
    # corners: radial falloff around the body's corner arc
    for pos, tr in MIRROR.items():
        g = svg.gradient("radialGradient",
                         [(0, "rgba(0,0,0,0)"), (R / (R + d) * 0.999, "rgba(0,0,0,0)"),
                          (R / (R + d), shadow), (R / (R + d) + (1 - R / (R + d)) * 0.45,
                                                  f"rgba({','.join(str(int(sc[i:i+2],16)) for i in (1,3,5))},{sa*0.35:.3f})"),
                          (1, "rgba(0,0,0,0)")],
                         cx=T, cy=T, r=R + d, gradientUnits="userSpaceOnUse")
        fpath, spath = corner_paths(T, R, d, d, 1)
        body = (f'<rect width="{T}" height="{T}" fill="{g}"/>'
                f'<path d="{fpath}" {paint(fill)}/><path d="{spath}" {paint(line)}/>')
        t = tr.format(S=T)
        svg.add(f"{name}-shadow-{pos}", T, T, f'<g transform="{t}">{body}</g>' if t else body)
    mid = f"rgba({','.join(str(int(sc[i:i+2],16)) for i in (1,3,5))},{sa*0.35:.3f})"
    def hedge():
        g = svg.gradient("linearGradient", [(0, "rgba(0,0,0,0)"), (0.55, mid), (1, shadow)],
                         x1=0, y1=0, x2=0, y2=d, gradientUnits="userSpaceOnUse")
        return (f'<rect width="24" height="{d}" fill="{g}"/>'
                f'<rect y="{d}" width="24" height="1" {paint(line)}/>'
                f'<rect y="{d + 1}" width="24" height="{F - 1}" {paint(fill)}/>')
    def vedge():
        g = svg.gradient("linearGradient", [(0, "rgba(0,0,0,0)"), (0.55, mid), (1, shadow)],
                         x1=0, y1=0, x2=d, y2=0, gradientUnits="userSpaceOnUse")
        return (f'<rect width="{d}" height="24" fill="{g}"/>'
                f'<rect x="{d}" width="1" height="24" {paint(line)}/>'
                f'<rect x="{d + 1}" width="{F - 1}" height="24" {paint(fill)}/>')
    svg.add(f"{name}-shadow-top", 24, T, hedge())
    svg.add(f"{name}-shadow-bottom", 24, T, f'<g transform="translate(0,{T}) scale(1,-1)">{hedge()}</g>')
    svg.add(f"{name}-shadow-left", T, 24, vedge())
    svg.add(f"{name}-shadow-right", T, 24, f'<g transform="translate({T},0) scale(-1,1)">{vedge()}</g>')
    for side in ("top", "bottom"):
        svg.add(f"{name}-shadow-hint-{side}", 24, d)
    for side in ("left", "right"):
        svg.add(f"{name}-shadow-hint-{side}", d, 24)
    # without compositing: plain rounded frame
    frame(svg, f"{name}-normal", F, R, fill, line)


# ------------------------------------------------------------------ theme ----
def build(t):
    svg = Svg()
    # push buttons (.btn): field, 1 px line, radius 10; default = accent ring
    for st, fill, line in (("normal", t["field"], t["line_btn"]), ("focused", t["field_hover"], t["line_btn"]),
                           ("pressed", t["field_press"], t["line_strong"]), ("toggled", t["field_press"], t["line_strong"])):
        box(svg, "button", st, 10, fill, line)
    frame(svg, "button-default", 3, 3, NONE, t["accent"], sw=1)
    frame(svg, "expand-button-default", 10, 10, NONE, t["accent"], sw=1.5)
    empty(svg, "button-default-indicator")
    # tool buttons (flat): hover/press tints, toggled = soft "on" (.tbtn.on)
    for st, fill in (("normal", NONE), ("focused", t["hover"]), ("pressed", t["press"]), ("toggled", t["press"])):
        box(svg, "tbutton", st, 8, fill)
    # grouped toolbar buttons = segmented control (.seg): track + raised segment
    for st, fill, line in (("normal", t["field"], NONE), ("focused", t["field_hover"], NONE),
                           ("pressed", t["field_press"], NONE), ("toggled", t["seg_on"], t["line_btn"])):
        box(svg, "seg", st, 9, fill, line)
    sep = f'<rect x="1" y="0" width="1" height="24" {paint(t["line_strong"])}/>'
    svg.add("seg-separator-normal", 3, 24, sep)
    svg.add("seg-separator-top", 3, 3, "")
    svg.add("seg-separator-bottom", 3, 3, "")
    # line edits / spin boxes (.search, .crumbs): field, radius 10, accent ring on focus
    for el in ("lineedit", "spin"):
        box(svg, el, "normal", 10, t["field"])
        box(svg, el, "focused", 10, t["base"], t["focus"])
        box(svg, el, "pressed", 10, t["field_press"])
    # combo boxes: like push buttons
    for st, fill, line in (("normal", t["field"], t["line_btn"]), ("focused", t["field_hover"], t["line_btn"]),
                           ("pressed", t["field_press"], t["line_strong"]), ("toggled", t["field_press"], t["line_strong"])):
        box(svg, "combo", st, 10, fill, line)
    # item views (.si / file items): radius 8 pills
    # Kvantum: "pressed" = selected in the focused view, "toggled" = selected elsewhere
    for st, fill in (("normal", NONE), ("focused", t["hover"]), ("pressed", t["sel"]), ("toggled", t["sel_soft"])):
        box(svg, "itemview", st, 8, fill, ix=4, iy=1)
    # menus (popups): radius 12, line, soft shadow
    popup(svg, "menu", 14, 12, t["popup"], t["popup_line"], t["shadow"])
    popup(svg, "tooltip", 8, 8, t["tooltip"], t["popup_line"], t["shadow"])
    # menu items: inset pill on hover (menu items are spread to the menu edge)
    for st, fill in (("normal", NONE), ("focused", t["sel"]), ("pressed", t["sel_press"]), ("toggled", t["sel"])):
        box(svg, "menuitem", st, 8, fill, ix=6, iy=1)
    sepw = 300
    svg.add("menuitem-separator", sepw, 9, f'<rect x="12" y="4" width="{sepw - 24}" height="1" {paint(t["line"])}/>')
    empty(svg, "menuitem-tearoff-normal", 20, 8)
    empty(svg, "menuitem-tearoff-focused", 20, 8)
    # menubar items: pill on hover/open
    for st, fill in (("normal", NONE), ("focused", t["hover"]), ("pressed", t["press"]), ("toggled", t["press"])):
        box(svg, "menubaritem", st, 7, fill)
    # tabs: pills (.seg-like), selected = raised
    for st, fill, line in (("normal", NONE, NONE), ("focused", t["hover"], NONE),
                           ("pressed", t["press"], NONE), ("toggled", t["seg_on"], t["line_btn"])):
        box(svg, "tab", st, 8, fill, line)
    frame(svg, "tabframe-normal", 6, 6, t["base"], t["line"])
    frame(svg, "expand-tabframe-normal", 12, 12, t["base"], t["line"])
    # group boxes / generic frames: cards with a hairline
    frame(svg, "group-normal", 6, 6, t["alt_base"], t["line"])
    frame(svg, "common-normal", 4, 4, NONE, t["line"], interior=False)
    empty(svg, "common-normal")
    frame(svg, "common-focused", 4, 4, NONE, t["focus"], interior=False)
    empty(svg, "common-focused")
    # header sections (details view): flat, bottom line, thin separators
    for st, fill in (("normal", t["base"]), ("focused", t["alt_base"]), ("pressed", t["field"]), ("toggled", t["base"])):
        for pos in ("topleft", "top", "topright", "left", "right"):
            empty(svg, f"header-{st}-{pos}", 3, 3)
        for pos in ("bottomleft", "bottom", "bottomright"):
            svg.add(f"header-{st}-{pos}", 3, 3, f'<rect width="3" height="3" {paint(t["line"])}/>')
        svg.add(f"header-{st}", 8, 8, f'<rect width="8" height="8" {paint(fill)}/>')
    svg.add("header-separator", 3, 24, f'<rect x="0" y="6" width="3" height="12" {paint(t["line"])}/>')
    # scrollbars: transient overlay pills
    for st, c in (("normal", t["scroll"]), ("focused", t["scroll_hover"]), ("pressed", t["scroll_hover"])):
        frame(svg, f"scrollbarslider-{st}", 5, 3, c, ix=2, iy=0)
    for st in ("normal", "focused", "pressed"):
        empty(svg, f"grip-{st}")
    frame(svg, "scrollgroove-normal", 5, 3, NONE)
    # sliders (volume etc.): 4 px track, accent fill, white knob
    for st, c in (("normal", t["field_press"]), ("toggled", t["accent"])):
        frame(svg, f"slider-{st}", 2, 2, c)
    empty(svg, "slider-tick-normal", 5, 1)
    for st, ring in (("normal", t["line_strong"]), ("focused", t["accent"]), ("pressed", t["accent"]),
                     ("disabled", t["line"])):
        svg.add(f"slidercursor-{st}", 20, 20,
                f'<circle cx="10" cy="10.6" r="9" fill="#000000" fill-opacity="0.10"/>'
                f'<circle cx="10" cy="10" r="8.5" fill="#ffffff" {paint(ring, "stroke")} stroke-width="1"/>')
    # progress bars: field track, accent bar
    frame(svg, "progress-normal", 3, 3, t["field"])
    frame(svg, "expand-progress-normal", 4, 4, t["field"])
    frame(svg, "progress-pattern-normal", 3, 3, t["accent"])
    frame(svg, "expand-progress-pattern-normal", 4, 4, t["accent"])
    frame(svg, "progress-pattern-disabled", 3, 3, t["disabled"])
    frame(svg, "expand-progress-pattern-disabled", 4, 4, t["disabled"])
    # toolbars, docks, title bars, status bar: flat (window colour)
    for el in ("toolbar-normal", "dock-normal", "dock-focused", "titlebar-normal", "titlebar-focused"):
        empty_frame(svg, el)
    empty(svg, "toolbar-handle", 8, 8)
    svg.add("toolbar-separator", 9, 24, f'<rect x="4" y="4" width="1" height="16" {paint(t["line"])}/>')
    # splitters: a hairline like the mockup's sidebar border
    for st in ("normal", "focused", "pressed"):
        svg.add(f"splitter-{st}", 8, 8, f'<rect x="0" width="8" height="8" {paint(t["line"] if st == "normal" else t["focus"])}/>')
        empty(svg, f"splitter-grip-{st}", 16, 16)
    # focus rectangle: none (Lucent shows focus through field rings)
    for pos in ("top", "bottom", "left", "right", "topleft", "topright", "bottomleft", "bottomright"):
        empty(svg, f"focus-{pos}", 1, 1)
    # indicators
    arrows(svg, "arrow", t)
    arrows(svg, "flat-arrow", t)
    for st, c in (("normal", t["text3"]), ("focused", t["text"]), ("pressed", t["text"]), ("disabled", t["disabled"])):
        chevron(svg, f"tree-plus-{st}", "right", c)
        chevron(svg, f"tree-minus-{st}", "down", c)
    for st, c in (("normal", t["text3"]), ("focused", t["text"]), ("pressed", t["text"]),
                  ("toggled", t["text2"]), ("disabled", t["disabled"])):
        svg.add(f"tab-close-{st}", 16, 16,
                (f'<circle cx="8" cy="8" r="8" {paint(t["press"])}/>' if st in ("focused", "pressed") else "") +
                f'<path d="M5.5,5.5 L10.5,10.5 M10.5,5.5 L5.5,10.5" stroke="{css2svg(c)[0]}" stroke-width="1.5" stroke-linecap="round"/>')
    svg.add("tab-close-toggledFocused", 16, 16, f'<circle cx="8" cy="8" r="8" {paint(t["press"])}/>'
            f'<path d="M5.5,5.5 L10.5,10.5 M10.5,5.5 L5.5,10.5" stroke="{css2svg(t["text"])[0]}" stroke-width="1.5" stroke-linecap="round"/>')
    svg.add("tab-close-toggledPressed", 16, 16, f'<circle cx="8" cy="8" r="8" {paint(t["press"])}/>'
            f'<path d="M5.5,5.5 L10.5,10.5 M10.5,5.5 L5.5,10.5" stroke="{css2svg(t["text"])[0]}" stroke-width="1.5" stroke-linecap="round"/>')
    empty(svg, "tab-tear", 2, 16)
    checkbox(svg, t)
    radio(svg, t)
    for st in ("normal", "focused"):
        svg.add(f"sizegrip-{st}", 13, 13)
    for b in ("close", "maximize", "minimize", "restore", "shade"):
        for st in ("normal", "focused", "pressed", "disabled"):
            chevron(svg, f"mdi-{b}-{st}", "down", t["text2"])
    chevron(svg, "mdi-menu-normal", "down", t["text2"])
    # dial (rare): plain circles
    svg.add("dial", 64, 64, f'<circle cx="32" cy="32" r="31" {paint(t["field"])} {paint(t["line"], "stroke")}/>')
    svg.add("dial-notches", 64, 64, "")
    svg.add("dial-handle", 8, 8, f'<circle cx="4" cy="4" r="4" {paint(t["accent"])}/>')
    return svg


def kvconfig(t):
    dark = t["dark"]
    tx, tx2 = t["text"], t["text2"]
    gc = dict(
        window=t["window"], base=t["base"], alt_base=t["alt_base"], button=t["field"],
        light=t["field_hover"] if dark else "#ffffff", mid_light=t["field_hover"],
        dark="#0d0f13" if dark else "#c3c8d2", mid="#2b2f38" if dark else "#dfe3ea",
    )
    return f"""# Lucent{' Dark' if dark else ''}: Kvantum theme generated by design/gen_kvantum.py
# from docs/mockups/lucent.css. Do not edit by hand.
[%General]
author=Lucent OS contributors
comment=Lucent{' Dark' if dark else ''}: rounded fields, segmented toolbar buttons, soft menus
x11drag=menubar_and_primary_toolbar
alt_mnemonic=true
respect_DE=true
dark_titlebar={str(dark).lower()}
composite=true
translucent_windows=false
blurring=false
popup_blurring=true
menu_blur_radius=10
tooltip_blur_radius=8
menu_shadow_depth=14
tooltip_shadow_depth=8
spread_menuitems=true
menu_separator_height=9
submenu_overlap=0
submenu_delay=200
scrollable_menu=true
combo_menu=true
combo_as_lineedit=true
combo_focus_rect=false
left_tabs=true
center_doc_tabs=false
attach_active_tab=false
joined_inactive_tabs=false
embedded_tabs=false
no_active_tab_separator=true
mirror_doc_tabs=true
group_toolbar_buttons=true
toolbar_item_spacing=2
toolbar_interior_spacing=4
toolbar_separator_thickness=12
center_toolbar_handle=true
slim_toolbars=false
toolbutton_style=0
spread_progressbar=true
progressbar_thickness=6
spread_header=true
menubar_mouse_tracking=true
merge_menubar_with_toolbar=false
transient_scrollbar=true
transient_groove=false
scroll_width=10
scroll_min_extent=40
scroll_arrows=false
scrollbar_in_view=true
tree_branch_line=false
groupbox_top_label=true
slider_width=4
slider_handle_width=20
slider_handle_length=20
check_size=18
vertical_spin_indicators=true
inline_spin_indicators=true
spin_button_width=18
square_combo_button=false
animate_states=true
no_inactiveness=true
no_window_pattern=true
splitter_width=1
layout_spacing=6
layout_margin=10
small_icon_size=16
large_icon_size=32
button_icon_size=16
toolbar_icon_size=20
dialog_button_layout=0
fill_rubberband=false
remove_extra_frames=true
shadowless_popup=false
click_behavior=0
tooltip_delay=-1
opaque=kaffeine,kmplayer,subtitlecomposer,kdenlive,vlc,smplayer,avidemux,kamoso,dragon,haruna,mpv

[GeneralColors]
window.color={t['window']}
base.color={t['base']}
# no zebra stripes in lists (the mockups have none)
alt.base.color={t['base']}
button.color={gc['button']}
light.color={gc['light']}
mid.light.color={gc['mid_light']}
dark.color={gc['dark']}
mid.color={gc['mid']}
shadow.color=#000000
highlight.color={t['text_sel']}
inactive.highlight.color={t['text_sel']}
text.color={tx}
window.text.color={tx}
button.text.color={tx}
disabled.text.color={t['disabled']}
tooltip.base.color={kvcolor(t['tooltip'])[:7]}
tooltip.text.color={tx}
highlight.text.color={tx}
link.color={t['link']}
link.visited.color={t['visited']}
progress.indicator.text.color={t['accent_text']}

[Hacks]
respect_darkness=true
transparent_dolphin_view=false
transparent_ktitle_label=true
transparent_menutitle=true
tint_on_mouseover=0
no_selection_tint=true
normal_default_pushbutton=true
iconless_pushbutton=false
transparent_arrow_button=true
iconless_menu=false
single_top_toolbar=false
style_vertical_toolbars=false
disabled_icon_opacity=45
middle_click_scroll=false
kinetic_scrolling=false
force_size_grip=false

[PanelButtonCommand]
frame=true
frame.element=button
frame.top=4
frame.bottom=4
frame.left=4
frame.right=4
frame.expansion=20
interior=true
interior.element=button
indicator.element=arrow
indicator.size=12
text.margin.top=4
text.margin.bottom=4
text.margin.left=10
text.margin.right=10
text.iconspacing=6
text.normal.color={tx}
text.focus.color={tx}
text.press.color={tx}
text.toggle.color={tx}
text.shadow=false
min_width=+1font
min_height=+0.5font

[PanelButtonTool]
inherits=PanelButtonCommand
frame.element=tbutton
interior.element=tbutton
frame.expansion=16
text.margin.left=6
text.margin.right=6
text.normal.color={tx}
text.focus.color={tx}
text.press.color={tx}
text.toggle.color={tx}
min_width=0
min_height=0

[ToolbarButton]
frame.element=seg
interior.element=seg
frame.expansion=18
indicator.element=flat-arrow
text.normal.color={tx2}
text.focus.color={tx}
text.press.color={tx}
text.toggle.color={tx}

[Dock]
inherits=PanelButtonCommand
frame=false
interior=false

[DockTitle]
inherits=PanelButtonCommand
frame=false
interior=false
text.bold=true
text.normal.color={tx}
text.focus.color={tx}

[IndicatorSpinBox]
inherits=PanelButtonCommand
frame=false
interior=false
indicator.element=flat-arrow
indicator.size=12

[RadioButton]
inherits=PanelButtonCommand
frame=false
interior.element=radio
text.margin.top=2
text.margin.bottom=2
text.margin.left=6
text.margin.right=4
min_width=0
min_height=0

[CheckBox]
inherits=PanelButtonCommand
frame=false
interior.element=checkbox
text.margin.top=2
text.margin.bottom=2
text.margin.left=6
text.margin.right=4
min_width=0
min_height=0

[Focus]
inherits=PanelButtonCommand
frame=true
frame.element=focus
frame.top=1
frame.bottom=1
frame.left=1
frame.right=1
frame.expansion=0
interior=false

[GenericFrame]
inherits=PanelButtonCommand
frame=true
frame.element=common
frame.top=1
frame.bottom=1
frame.left=1
frame.right=1
frame.expansion=0
interior=false

[LineEdit]
inherits=PanelButtonCommand
frame.element=lineedit
interior.element=lineedit
frame.top=4
frame.bottom=4
frame.left=6
frame.right=6
frame.expansion=20
text.margin.left=4
text.margin.right=4
min_height=+0.6font

[ToolbarLineEdit]
inherits=LineEdit

[DropDownButton]
inherits=PanelButtonCommand
indicator.element=flat-arrow
frame=false
interior=false

[IndicatorArrow]
indicator.element=flat-arrow
indicator.size=12

[ToolboxTab]
inherits=PanelButtonCommand
frame.element=tab
interior.element=tab

[Tab]
inherits=PanelButtonCommand
frame.element=tab
interior.element=tab
indicator.element=tab
indicator.size=16
frame.top=3
frame.bottom=3
frame.left=3
frame.right=3
frame.expansion=16
text.margin.top=5
text.margin.bottom=5
text.margin.left=12
text.margin.right=12
text.normal.color={tx2}
text.focus.color={tx}
text.press.color={tx}
text.toggle.color={tx}
min_width=0
min_height=0

[TabFrame]
inherits=PanelButtonCommand
frame.element=tabframe
interior.element=tabframe
frame.top=6
frame.bottom=6
frame.left=6
frame.right=6
frame.expansion=24

[TabBarFrame]
inherits=GenericFrame
frame=false
interior=false

[TreeExpander]
inherits=PanelButtonCommand
frame=false
interior=false
indicator.element=tree
indicator.size=14

[HeaderSection]
inherits=PanelButtonCommand
frame.element=header
interior.element=header
indicator.element=flat-arrow
indicator.size=10
frame.top=0
frame.bottom=1
frame.left=0
frame.right=1
frame.expansion=0
text.margin.top=6
text.margin.bottom=6
text.margin.left=10
text.margin.right=10
text.normal.color={tx2}
text.focus.color={tx}
text.press.color={tx}
text.toggle.color={tx}
min_width=0
min_height=0

[SizeGrip]
indicator.element=sizegrip

[Toolbar]
inherits=PanelButtonCommand
frame=false
interior=false
frame.element=toolbar
interior.element=toolbar
indicator.element=toolbar
indicator.size=8
text.normal.color={tx}
text.focus.color={tx}

[Slider]
inherits=PanelButtonCommand
frame.element=slider
interior.element=slider
frame.top=2
frame.bottom=2
frame.left=2
frame.right=2
frame.expansion=0

[SliderCursor]
inherits=PanelButtonCommand
frame=false
interior.element=slidercursor

[Progressbar]
inherits=PanelButtonCommand
frame.element=progress
interior.element=progress
frame.top=3
frame.bottom=3
frame.left=3
frame.right=3
frame.expansion=8
text.margin=false
text.normal.color={tx2}
text.focus.color={tx}
text.bold=false

[ProgressbarContents]
inherits=PanelButtonCommand
frame=true
frame.element=progress-pattern
interior.element=progress-pattern
frame.top=3
frame.bottom=3
frame.left=3
frame.right=3
frame.expansion=8

[ItemView]
inherits=PanelButtonCommand
frame.element=itemview
interior.element=itemview
frame.top=2
frame.bottom=2
frame.left=6
frame.right=6
frame.expansion=24
text.margin.top=2
text.margin.bottom=2
text.margin.left=4
text.margin.right=4
text.normal.color={tx}
text.focus.color={tx}
text.press.color={tx}
text.toggle.color={tx}
min_width=0
min_height=+0.6font

[Splitter]
inherits=PanelButtonCommand
frame=false
interior=true
interior.element=splitter
indicator.element=splitter-grip
indicator.size=0

[Scrollbar]
inherits=PanelButtonCommand
frame=false
interior=false
indicator.element=flat-arrow
indicator.size=0

[ScrollbarSlider]
inherits=PanelButtonCommand
frame.element=scrollbarslider
interior=false
frame.top=5
frame.bottom=5
frame.left=5
frame.right=5
frame.expansion=0
indicator.element=grip
indicator.size=0

[ScrollbarGroove]
inherits=PanelButtonCommand
frame=false
interior=false
frame.element=scrollgroove
interior.element=scrollgroove

[MenuItem]
inherits=PanelButtonCommand
frame=true
frame.element=menuitem
interior.element=menuitem
indicator.element=menuitem
indicator.size=14
frame.top=3
frame.bottom=3
frame.left=4
frame.right=4
frame.expansion=28
text.margin.top=3
text.margin.bottom=3
text.margin.left=14
text.margin.right=14
text.iconspacing=10
text.normal.color={tx}
text.focus.color={tx}
text.press.color={tx}
text.toggle.color={tx}
min_width=+1font
min_height=+0.35font

[MenuBar]
inherits=PanelButtonCommand
frame=false
interior=false
frame.element=toolbar
interior.element=toolbar
text.normal.color={tx}

[MenuBarItem]
inherits=PanelButtonCommand
frame.element=menubaritem
interior.element=menubaritem
frame.top=3
frame.bottom=3
frame.left=3
frame.right=3
frame.expansion=14
text.margin.top=4
text.margin.bottom=4
text.margin.left=8
text.margin.right=8
text.normal.color={tx}
text.focus.color={tx}
text.press.color={tx}
text.toggle.color={tx}
min_width=0
min_height=0

[TitleBar]
inherits=PanelButtonCommand
frame=false
interior=false
indicator.element=mdi
indicator.size=12
text.normal.color={tx2}
text.focus.color={tx}

[ComboBox]
inherits=PanelButtonCommand
frame.element=combo
interior.element=combo
indicator.element=flat-arrow
indicator.size=12
text.margin.left=10
text.margin.right=6

[ToolbarComboBox]
inherits=ComboBox

[Menu]
inherits=PanelButtonCommand
frame.element=menu
interior.element=menu
frame.top=12
frame.bottom=12
frame.left=12
frame.right=12
frame.expansion=0
text.normal.color={tx}

[GroupBox]
inherits=GenericFrame
frame=true
frame.element=group
interior=true
interior.element=group
frame.top=6
frame.bottom=6
frame.left=6
frame.right=6
text.margin.top=2
text.margin.bottom=4
text.margin.left=4
text.margin.right=4
text.bold=true
text.normal.color={tx}
text.focus.color={tx}

[ToolTip]
inherits=GenericFrame
frame=true
frame.element=tooltip
interior=true
interior.element=tooltip
frame.top=8
frame.bottom=8
frame.left=8
frame.right=8
text.margin.top=2
text.margin.bottom=2
text.margin.left=4
text.margin.right=4
text.normal.color={tx}

[StatusBar]
inherits=GenericFrame
frame=false
interior=false

[Window]
interior=false

[Dialog]
inherits=Window
"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for t in (LIGHT, DARK):
        (OUT / f"{t['name']}.svg").write_text(build(t).text(), encoding="utf-8")
        (OUT / f"{t['name']}.kvconfig").write_text(kvconfig(t), encoding="utf-8")
        print("wrote", OUT / t["name"])


if __name__ == "__main__":
    main()
