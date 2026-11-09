#!/usr/bin/env python3
"""Generate the Lucent Kvantum themes (widget style for Qt apps): Pebble Drift,
light + dark, one theme per accent swatch.

Breeze has no knobs for radii, field shapes or menu metrics, so native Qt
apps (Dolphin, System Settings' widgets, Konsole, Ark, Okular...) are drawn
with Kvantum, an SVG-driven Qt style. Every theme folder holds both variants
(Kvantum's "Dark in the light folder" layout); widgetStyle=lucent picks the
light one, lucent-dark the dark one:

  Lucent/Lucent{,Dark}.{kvconfig,svg}                  Indigo (the default)
  Lucent<Accent>/Lucent<Accent>{,Dark}.{kvconfig,svg}  Azure, Lagoon, ... Slate

Kvantum's SVGs can't follow the palette, so an accent is a theme; `lucent-theme`
switches between them (~/.config/Kvantum/kvantum.kvconfig).

Shapes and colours come from docs/mockups/concepts-2026/pebble-drift/
pebble-drift.css (design/tokens.py):
  push buttons, combos, the "on" segment and tab   raised pillow: --surface-raised
        -> -raised-2 gradient, 1 px ring, 1 px soft drop, top highlight, radius 10
  fields, spin boxes, segmented tracks, progress    sunken well: --surface-sunken,
        inner ring + top inner shadow (--shadow-sunken), radius 10
  menus / combo popups / tooltips                   --surface-popover, radius 12,
        hairline, long soft shadow
  menu items                                        --accent-soft pill
  item views                                        hover --state-hover; selected
        --surface-selected with a --accent-ring outline (.card.sel)
  checkboxes / radios                               18 px, radius 6, accent when on
Every element Kvantum's built-in default theme would otherwise supply is
generated here, so nothing falls back to its dark "Enlightenment" look.

Run: python3 design/gen_kvantum.py
Output: system_files/usr/share/Kvantum/Lucent*/
"""
import shutil
import sys
import math
from pathlib import Path

import tokens

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "system_files/usr/lib/lucent"))
from lucent_theme import accents  # noqa: E402

KV = ROOT / "system_files/usr/share/Kvantum"


def theme_name(accent_id: str) -> str:
    """Kvantum theme (= folder) for an accent: Indigo keeps the plain name."""
    return "Lucent" if accent_id == "indigo" else "Lucent" + accents.find(accent_id).name


def first_shadow(value: str, index: int = 0) -> str:
    return tokens.shadows(value)[index][4]


def theme_dict(tk: dict, accent_id: str, dark: bool) -> dict:
    """The colours this generator draws with, from one mode's tokens and accent."""
    a = accents.palette(accent_id, dark)
    win = tk["surface-window-solid"]
    flat = lambda v, under=win: tokens.flatten(v, under)
    if accent_id == "indigo":
        selected, selected2 = tk["surface-selected"], tk["surface-selected-2"]
    else:   # the same accent tint as Indigo's --surface-selected, in this accent
        k = .16 if dark else .08
        selected = flat(tokens.rgba_str(a["accent"], k), tk["surface-raised"])
        selected2 = flat(tokens.rgba_str(a["accent"], k), tk["surface-raised-2"])
    raised, raised2 = tk["surface-raised"], tk["surface-raised-2"]
    sh_raised = tokens.shadows(tk["shadow-raised"])
    sh_sunken = tokens.shadows(tk["shadow-sunken"])
    return dict(
        name=theme_name(accent_id) + ("Dark" if dark else ""), dark=dark, accent_id=accent_id,
        text=tk["text-primary"], text2=tk["text-secondary"], text3=tk["text-tertiary"],
        disabled=tk["text-disabled"],
        window=win, base=raised2 if dark else raised, alt_base=raised2 if dark else raised,
        raised=raised, raised2=raised2,
        hover_top=flat(tk["state-hover"], raised), hover_bottom=flat(tk["state-hover"], raised2),
        press_fill=flat(tk["state-pressed"], raised2),
        ring=sh_raised[0][4],                          # 0 0 0 1px ring of --shadow-raised
        drop=sh_raised[1][4],                          # 0 1px 2px drop
        highlight=tokens.shadows(tk["highlight-top"])[0][4],
        well=tk["surface-sunken"], well_strong=tk["surface-sunken-strong"],
        well_shadow=sh_sunken[0][4], well_ring=sh_sunken[1][4],
        well_hover=tokens.rgba_str(tk["surface-sunken"], tokens.color(tk["surface-sunken"])[3] * 1.5),
        line=tk["line"], line_strong=tk["line-strong"], line_control=tk["line-control"],
        hover=tk["state-hover"], press=tk["state-pressed"],
        selected=selected, selected2=selected2,
        accent=a["accent"], accent_hover=a["accent-hover"], accent_pressed=a["accent-pressed"],
        accent_ink=a["accent-text"], on_accent=a["text-on-accent"], accent_ring=a["accent-ring"],
        accent_soft=a["accent-soft"], accent_soft_strong=a["accent-soft-strong"],
        popup=tk["surface-popover"], popup_line=tk["line-strong"] if dark else tk["line"],
        shadow=tokens.rgba_str(first_shadow(tk["shadow-popover"], -1), .30 if not dark else .55),
        tooltip=tk["surface-popover"],
        scroll=tk["line-control"], scroll_hover=tokens.rgba_str(tk["line-control"], .55 if not dark else .6),
        check_border=tk["line-control"],
        knob_top=tk["knob"].split("(")[1].split(",")[0].strip(), knob_bottom=tk["knob"].rsplit(",", 1)[1].strip(" )"),
        link=a["accent-text"], visited=tk["accent-2"], danger=tk["status-danger"],
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


# ------------------------------------------------- layered (Pebble) frames ----
def rr_poly(x0, y0, x1, y1, r, seg=8):
    """A rounded rectangle as a polygon (arcs in `seg` steps per corner)."""
    r = max(0.0, min(r, (x1 - x0) / 2, (y1 - y0) / 2))
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for k in range(seg + 1 if r else 1):
            a = math.radians(a0 + 90 * k / seg)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def clip(poly, x0, y0, x1, y1):
    """Sutherland-Hodgman: a convex polygon cut to a rectangle."""
    def cut(pts, inside, inter):
        out = []
        for i, cur in enumerate(pts):
            prev = pts[i - 1]
            if inside(cur):
                if not inside(prev):
                    out.append(inter(prev, cur))
                out.append(cur)
            elif inside(prev):
                out.append(inter(prev, cur))
        return out

    def at_x(p, q, x):
        t = (x - p[0]) / (q[0] - p[0])
        return (x, p[1] + t * (q[1] - p[1]))

    def at_y(p, q, y):
        t = (y - p[1]) / (q[1] - p[1])
        return (p[0] + t * (q[0] - p[0]), y)

    pts = poly
    for inside, inter in ((lambda p: p[0] >= x0 - 1e-9, lambda p, q: at_x(p, q, x0)),
                          (lambda p: p[0] <= x1 + 1e-9, lambda p, q: at_x(p, q, x1)),
                          (lambda p: p[1] >= y0 - 1e-9, lambda p, q: at_y(p, q, y0)),
                          (lambda p: p[1] <= y1 + 1e-9, lambda p, q: at_y(p, q, y1))):
        if len(pts) < 3:
            return []
        pts = cut(pts, inside, inter)
    # drop slivers (a polygon reduced to a line on the cell edge)
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    if len(pts) < 3 or max(xs) - min(xs) < 1e-6 or max(ys) - min(ys) < 1e-6:
        return []
    return pts


def poly_d(pts, ox, oy):
    def n(v):
        return f"{v:.2f}".rstrip("0").rstrip(".")
    return "M" + " L".join(f"{n(x - ox)},{n(y - oy)}" for x, y in pts) + " Z"


def layered(svg, name, R, layers, inset=(0, 0, 0, 0), E=24, interior=True):
    """Nine Kvantum objects (name-topleft ... name, like frame()) cut from one
    nominal rounded box drawn in layers. Each piece only holds geometry inside
    its own cell (QtSvg sizes elements by their unclipped content), so the
    pieces are clipped polygons, not one shape under a clip-path. Gradients
    use user-space coordinates of the whole nominal box.

    inset = (left, top, right, bottom): transparent room around the shape
    (e.g. 1 px at the bottom for the drop shadow). Layers, drawn in order:
      ("shape", paint, inset_px, dy)          the box, shrunk and/or moved
      ("band", paint, outer_inset, inner_inset) a ring between two boxes
      ("topline", paint, inset_px, height)    a line along the inside top
    paint: css colour, or ("vgrad", top, bottom) over the box's height.
    """
    il, it, ir, ib = inset
    S = R + max(inset)
    N = 2 * S + E
    x0, y0, x1, y1 = il, it, N - ir, N - ib

    def box(d, dy=0):
        return rr_poly(x0 + d, y0 + d + dy, x1 - d, y1 - d + dy, max(R - d, 0))

    shapes = []
    for kind, pnt, a, b in layers:
        if kind == "shape":
            shapes.append(([box(a, b)], pnt, False))
        elif kind == "band":
            shapes.append(([box(a), box(b)], pnt, True))
        elif kind == "topline":
            shapes.append(([clip(box(a), -1, y0 + a, N + 1, y0 + a + b)], pnt, False))
    cells = {"topleft": (0, 0, S, S), "top": (S, 0, S + E, S), "topright": (S + E, 0, N, S),
             "left": (0, S, S, S + E), name: (S, S, S + E, S + E), "right": (S + E, S, N, S + E),
             "bottomleft": (0, S + E, S, N), "bottom": (S, S + E, S + E, N), "bottomright": (S + E, S + E, N, N)}
    for pos, (cx0, cy0, cx1, cy1) in cells.items():
        if pos == name and not interior:
            continue
        body = []
        for polys, pnt, evenodd in shapes:
            cut = [clip(pl, cx0, cy0, cx1, cy1) for pl in polys]
            cut = [c for c in cut if c]
            if not cut:
                continue
            # (a band whose inner box covers the whole cell cancels out under evenodd)
            d = " ".join(poly_d(c, cx0, cy0) for c in cut)
            if isinstance(pnt, tuple):
                g = svg.gradient("linearGradient", [(0, pnt[1]), (1, pnt[2])], x1=0, y1=y0 - cy0, x2=0, y2=y1 - cy0,
                                 gradientUnits="userSpaceOnUse")
                fill = f'fill="{g}"'
            else:
                fill = paint(pnt)
            rule = ' fill-rule="evenodd"' if evenodd else ""
            body.append(f'<path d="{d}" {fill}{rule}/>')
        eid = pos if pos == name else f"{name}-{pos}"
        svg.add(eid, cx1 - cx0, cy1 - cy0, "".join(body))


def lbox(svg, el, state, R, layers, inset=(0, 0, 0, 0), expand=True):
    """A state of an element drawn with layered(): tight frames (radius 3,
    for frame.expansion=0 uses) plus `expand-` frames with the real radius."""
    layered(svg, f"{el}-{state}", min(R, 3), layers, inset)
    if expand:
        layered(svg, f"expand-{el}-{state}", R, layers, inset)


def pillow(t, top, bottom=None, drop=True, highlight=True):
    """Raised pillow control (.pb.raised / .btn): ring, soft 1 px drop, fill, top light."""
    fill = ("vgrad", top, bottom) if bottom and bottom != top else top
    layers = []
    if drop:
        layers.append(("shape", t["drop"], 0, 1))
    layers += [("band", t["ring"], 0, 1), ("shape", fill, 1, 0)]
    if highlight:
        layers.append(("topline", t["highlight"], 1, 1))
    return layers


def well(t, fill, ring=None):
    """Sunken well (.field / .seg / tracks): fill, inner hairline, inner top shadow."""
    return [("shape", fill, 0, 0), ("band", ring or t["well_ring"], 0, 1), ("topline", t["well_shadow"], 1, 1)]


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
    """18 px, radius 6 (--radius-chip): a small pillow; accent fill + tick when on."""
    S = 18
    g = svg.gradient("linearGradient", [(0, t["raised"]), (1, t["raised2"])], x1=0, y1=0, x2=0, y2=1)
    def sq(fill, stroke, w=1.25):
        return (f'<rect x="{w / 2}" y="{w / 2}" width="{S - w}" height="{S - w}" rx="{6 - w / 2}" '
                f'fill="{fill}" {paint(stroke, "stroke")} stroke-width="{w}"/>')
    ink = css2svg(t["on_accent"])[0]
    tick = f'<polyline points="5,9.3 7.8,12 13,6.4" fill="none" stroke="{ink}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
    dash = f'<path d="M5.5,9 H12.5" stroke="{ink}" stroke-width="2" stroke-linecap="round"/>'
    on = lambda c: f'<rect width="18" height="18" rx="6" {paint(c)}/>'
    p = prefix
    svg.add(f"{p}checkbox-normal", S, S, sq(g, t["line_control"]))
    svg.add(f"{p}checkbox-focused", S, S, sq(g, t["accent"], 1.5))
    svg.add(f"{p}checkbox-pressed", S, S, sq(css2svg(t["press_fill"])[0], t["accent"], 1.5))
    svg.add(f"{p}checkbox-disabled", S, S, sq(css2svg(t["window"])[0], t["line_strong"]))
    for st, c in (("normal", t["accent"]), ("focused", t["accent_hover"]), ("pressed", t["accent_pressed"]),
                  ("disabled", t["disabled"])):
        svg.add(f"{p}checkbox-checked-{st}", S, S, on(c) + tick)
        svg.add(f"{p}checkbox-tristate-{st}", S, S, on(c) + dash)


def radio(svg, t, prefix=""):
    S = 18
    g = svg.gradient("linearGradient", [(0, t["raised"]), (1, t["raised2"])], x1=0, y1=0, x2=0, y2=1)
    ring = lambda fill, stroke, w=1.25: (f'<circle cx="9" cy="9" r="{9 - w / 2}" fill="{fill}" '
                                         f'{paint(stroke, "stroke")} stroke-width="{w}"/>')
    p = prefix
    dot = css2svg(t["on_accent"])[0]
    svg.add(f"{p}radio-normal", S, S, ring(g, t["line_control"]))
    svg.add(f"{p}radio-focused", S, S, ring(g, t["accent"], 1.5))
    svg.add(f"{p}radio-pressed", S, S, ring(css2svg(t["press_fill"])[0], t["accent"], 1.5))
    svg.add(f"{p}radio-disabled", S, S, ring(css2svg(t["window"])[0], t["line_strong"]))
    for st, c in (("normal", t["accent"]), ("focused", t["accent_hover"]), ("pressed", t["accent_pressed"]),
                  ("disabled", t["disabled"])):
        svg.add(f"{p}radio-checked-{st}", S, S, f'<circle cx="9" cy="9" r="9" {paint(c)}/>'
                                              f'<circle cx="9" cy="9" r="3.6" fill="{dot}"/>')


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
    raised = pillow(t, t["raised"], t["raised2"])
    hovered = pillow(t, t["hover_top"], t["hover_bottom"])
    pressed = pillow(t, t["press_fill"], drop=False, highlight=False)
    PI = (0, 0, 0, 1)        # pillow inset: 1 px at the bottom for the drop shadow
    # push buttons (.btn): raised pillow, radius 10; default = accent ring
    for st, layers in (("normal", raised), ("focused", hovered), ("pressed", pressed), ("toggled", pressed)):
        lbox(svg, "button", st, 10, layers, PI)
    frame(svg, "button-default", 3, 3, NONE, t["accent"], sw=1)
    frame(svg, "expand-button-default", 10, 10, NONE, t["accent"], sw=1.5)
    empty(svg, "button-default-indicator")
    # tool buttons (.pb.flat): flat; hover/press tint; "on" = raised pillow
    for st, fill in (("normal", NONE), ("focused", t["hover"]), ("pressed", t["press"])):
        box(svg, "tbutton", st, 10, fill)
    lbox(svg, "tbutton", "toggled", 10, raised, PI)
    # grouped toolbar buttons = segmented control (.seg): sunken track, raised "on" segment
    lbox(svg, "seg", "normal", 10, well(t, t["well"]))
    lbox(svg, "seg", "focused", 10, well(t, t["well_hover"]))
    lbox(svg, "seg", "pressed", 10, well(t, t["well_strong"]))
    lbox(svg, "seg", "toggled", 9, raised, PI)
    sep = f'<rect x="1" y="4" width="1" height="16" {paint(t["line_strong"])}/>'
    svg.add("seg-separator-normal", 3, 24, sep)
    svg.add("seg-separator-top", 3, 3, "")
    svg.add("seg-separator-bottom", 3, 3, "")
    # line edits / spin boxes (.field): sunken well, radius 10; focus = raised + 2 px accent ring
    focus = [("shape", t["raised"], 0, 0), ("band", t["accent_ring"], 0, 2)]
    for el in ("lineedit", "spin"):
        lbox(svg, el, "normal", 10, well(t, t["well"]))
        lbox(svg, el, "focused", 10, focus)
        lbox(svg, el, "pressed", 10, well(t, t["well_strong"]))
    # combo boxes: pillow controls like push buttons
    for st, layers in (("normal", raised), ("focused", hovered), ("pressed", pressed), ("toggled", pressed)):
        lbox(svg, "combo", st, 10, layers, PI)
    # item views: hover --state-hover; selected = .card.sel (--surface-selected + accent outline)
    # Kvantum: "pressed" = selected in the focused view, "toggled" = selected elsewhere
    box(svg, "itemview", "normal", 10, NONE, ix=4, iy=1)
    box(svg, "itemview", "focused", 10, t["hover"], ix=4, iy=1)
    IV = (4, 1, 4, 1)
    lbox(svg, "itemview", "pressed", 10, [("shape", t["selected"], 0, 0), ("band", t["accent_ring"], 0, 1.5)], IV)
    lbox(svg, "itemview", "toggled", 10, [("shape", t["selected"], 0, 0), ("band", t["line_strong"], 0, 1)], IV)
    # menus (popups): --surface-popover, radius 12, hairline, long soft shadow
    popup(svg, "menu", 14, 12, t["popup"], t["popup_line"], t["shadow"])
    popup(svg, "tooltip", 8, 10, t["tooltip"], t["popup_line"], t["shadow"])
    # menu items: accent-soft pill on hover (menu items are spread to the menu edge)
    for st, fill in (("normal", NONE), ("focused", t["accent_soft"]), ("pressed", t["accent_soft_strong"]),
                     ("toggled", t["accent_soft"])):
        box(svg, "menuitem", st, 8, fill, ix=6, iy=1)
    sepw = 300
    svg.add("menuitem-separator", sepw, 9, f'<rect x="12" y="4" width="{sepw - 24}" height="1" {paint(t["line"])}/>')
    empty(svg, "menuitem-tearoff-normal", 20, 8)
    empty(svg, "menuitem-tearoff-focused", 20, 8)
    # menubar items (.menus span): radius 8 pill on hover/open
    for st, fill in (("normal", NONE), ("focused", t["hover"]), ("pressed", t["press"]), ("toggled", t["press"])):
        box(svg, "menubaritem", st, 8, fill)
    # tabs: flat; the selected tab is a raised pillow (like .tabs span.on)
    for st, fill in (("normal", NONE), ("focused", t["hover"]), ("pressed", t["press"])):
        box(svg, "tab", st, 9, fill)
    lbox(svg, "tab", "toggled", 9, raised, PI)
    card = [("shape", ("vgrad", t["raised"], t["raised2"]), 0, 0), ("band", t["ring"], 0, 1)]
    layered(svg, "tabframe-normal", 3, card)
    layered(svg, "expand-tabframe-normal", 14, card)
    # group boxes: cards (raised fill + ring), generic frames: hairline
    layered(svg, "group-normal", 10, card)
    frame(svg, "common-normal", 4, 4, NONE, t["line"], interior=False)
    empty(svg, "common-normal")
    frame(svg, "common-focused", 4, 4, NONE, t["accent_ring"], interior=False)
    empty(svg, "common-focused")
    # header sections (details view): flat, bottom hairline, thin separators
    for st, fill in (("normal", NONE), ("focused", t["hover"]), ("pressed", t["press"]), ("toggled", NONE)):
        for pos in ("topleft", "top", "topright", "left", "right"):
            empty(svg, f"header-{st}-{pos}", 3, 3)
        for pos in ("bottomleft", "bottom", "bottomright"):
            svg.add(f"header-{st}-{pos}", 3, 3, f'<rect y="2" width="3" height="1" {paint(t["line"])}/>')
        svg.add(f"header-{st}", 8, 8, f'<rect width="8" height="8" {paint(fill)}/>' if fill != NONE else "")
    svg.add("header-separator", 3, 24, f'<rect x="1" y="6" width="1" height="12" {paint(t["line"])}/>')
    # scrollbars: transient overlay pills
    for st, c in (("normal", t["scroll"]), ("focused", t["scroll_hover"]), ("pressed", t["scroll_hover"])):
        frame(svg, f"scrollbarslider-{st}", 5, 3, c, ix=2, iy=0)
    for st in ("normal", "focused", "pressed"):
        empty(svg, f"grip-{st}")
    frame(svg, "scrollgroove-normal", 5, 3, NONE)
    # sliders: sunken track, accent fill, knob (--knob) with a soft shadow
    frame(svg, "slider-normal", 3, 3, t["well_strong"])
    frame(svg, "slider-toggled", 3, 3, t["accent"])
    empty(svg, "slider-tick-normal", 5, 1)
    kg = svg.gradient("linearGradient", [(0, t["knob_top"]), (1, t["knob_bottom"])], x1=0, y1=0, x2=0, y2=1)
    for st, ring in (("normal", t["ring"]), ("focused", t["accent"]), ("pressed", t["accent"]),
                     ("disabled", t["line"])):
        svg.add(f"slidercursor-{st}", 20, 20,
                f'<circle cx="10" cy="10.8" r="9" fill="#141e50" fill-opacity="0.22"/>'
                f'<circle cx="10" cy="10" r="8.5" fill="{kg}" {paint(ring, "stroke")} stroke-width="1"/>')
    # progress bars (.prog): sunken strong track, flat accent fill, radius 5
    frame(svg, "progress-normal", 3, 3, t["well_strong"])
    frame(svg, "expand-progress-normal", 5, 5, t["well_strong"])
    frame(svg, "progress-pattern-normal", 3, 3, t["accent"])
    frame(svg, "expand-progress-pattern-normal", 5, 5, t["accent"])
    frame(svg, "progress-pattern-disabled", 3, 3, t["disabled"])
    frame(svg, "expand-progress-pattern-disabled", 5, 5, t["disabled"])
    # toolbars, docks, title bars, status bar: flat (window colour, one-row header)
    for el in ("toolbar-normal", "dock-normal", "dock-focused", "titlebar-normal", "titlebar-focused"):
        empty_frame(svg, el)
    empty(svg, "toolbar-handle", 8, 8)
    svg.add("toolbar-separator", 13, 26, f'<rect x="6" y="0" width="1" height="26" {paint(t["line_strong"])}/>')
    # splitters: a hairline
    for st in ("normal", "focused", "pressed"):
        svg.add(f"splitter-{st}", 8, 8, f'<rect x="0" width="8" height="8" {paint(t["line"] if st == "normal" else t["accent_ring"])}/>')
        empty(svg, f"splitter-grip-{st}", 16, 16)
    # focus rectangle: none (focus shows as field rings)
    for pos in ("top", "bottom", "left", "right", "topleft", "topright", "bottomleft", "bottomright"):
        empty(svg, f"focus-{pos}", 1, 1)
    # indicators
    arrows(svg, "arrow", t)
    arrows(svg, "flat-arrow", t)
    for st, c in (("normal", t["text3"]), ("focused", t["text"]), ("pressed", t["text"]), ("disabled", t["disabled"])):
        chevron(svg, f"tree-plus-{st}", "right", c)
        chevron(svg, f"tree-minus-{st}", "down", c)
    xp = 'M5.5,5.5 L10.5,10.5 M10.5,5.5 L5.5,10.5'
    for st, c in (("normal", t["text3"]), ("focused", t["text"]), ("pressed", t["text"]),
                  ("toggled", t["text2"]), ("disabled", t["disabled"])):
        svg.add(f"tab-close-{st}", 16, 16,
                (f'<rect width="16" height="16" rx="5" {paint(t["press"])}/>' if st in ("focused", "pressed") else "") +
                f'<path d="{xp}" {paint(c, "stroke")} stroke-width="1.5" stroke-linecap="round"/>')
    for st in ("toggledFocused", "toggledPressed"):
        svg.add(f"tab-close-{st}", 16, 16, f'<rect width="16" height="16" rx="5" {paint(t["press"])}/>'
                f'<path d="{xp}" {paint(t["text"], "stroke")} stroke-width="1.5" stroke-linecap="round"/>')
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
    svg.add("dial", 64, 64, f'<circle cx="32" cy="32" r="31" {paint(t["raised"])} {paint(t["line"], "stroke")}/>')
    svg.add("dial-notches", 64, 64, "")
    svg.add("dial-handle", 8, 8, f'<circle cx="4" cy="4" r="4" {paint(t["accent"])}/>')
    return svg


def kvconfig(t):
    dark = t["dark"]
    tx, tx2 = t["text"], t["text2"]
    accent = accents.find(t["accent_id"]).name
    gc = dict(
        button=t["raised"], light=t["raised"] if dark else "#ffffff", mid_light=t["raised2"],
        dark=tokens.flatten(t["line_control"], t["window"]), mid=tokens.flatten(t["line_strong"], t["window"]),
    )
    return f"""# {t['name']}: Lucent's Kvantum theme ({'dark' if dark else 'light'}, accent {accent}), generated by
# design/gen_kvantum.py from docs/mockups/concepts-2026/pebble-drift/pebble-drift.css. Do not edit by hand.
[%General]
author=Lucent OS contributors
comment=Lucent Pebble Drift{' Dark' if dark else ''} ({accent}): raised pillow controls, sunken fields, matte menus
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
progressbar_thickness=8
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
highlight.color={t['accent']}
inactive.highlight.color={t['accent']}
text.color={tx}
window.text.color={tx}
button.text.color={tx}
disabled.text.color={t['disabled']}
tooltip.base.color={tokens.flatten(t['tooltip'], t['window'])}
tooltip.text.color={tx}
highlight.text.color={t['on_accent']}
link.color={t['link']}
link.visited.color={t['visited']}
progress.indicator.text.color={t['on_accent']}

[Hacks]
respect_darkness=true
transparent_dolphin_view=true
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
frame.expansion=22
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
frame.expansion=22
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
frame.expansion=20
indicator.element=flat-arrow
text.normal.color={tx2}
text.focus.color={tx}
text.press.color={tx}
text.toggle.color={t['accent_ink']}

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
frame.expansion=20
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
frame.expansion=28

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
frame.expansion=10
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
frame.expansion=10

[ItemView]
inherits=PanelButtonCommand
frame.element=itemview
interior.element=itemview
frame.top=2
frame.bottom=2
frame.left=6
frame.right=6
frame.expansion=28
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
frame.expansion=16
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


def themes(tk=None):
    """(folder, theme dict) for every accent and mode."""
    tk = tk or tokens.load()
    for a in accents.ACCENTS:
        for dark in (False, True):
            yield theme_name(a.id), theme_dict(tk.mode(dark), a.id, dark)


def main():
    for old in KV.glob("Lucent*"):
        shutil.rmtree(old)
    for folder, t in themes():
        out = KV / folder
        out.mkdir(parents=True, exist_ok=True)
        (out / f"{t['name']}.svg").write_text(build(t).text(), encoding="utf-8")
        (out / f"{t['name']}.kvconfig").write_text(kvconfig(t), encoding="utf-8")
        print("wrote", out / t["name"])


if __name__ == "__main__":
    main()
