"""The eight accent swatches of Pebble Drift and the colours derived from them.

Swatches and names: docs/mockups/concepts-2026/pebble-drift/04-settings.html
(tested against it). Indigo is the design's own accent and uses the tokens of
pebble-drift.css as they are (light #4257e8, dark #7088ff). Every other
swatch is used as is in both modes, with the same derived shades as Lucent
Settings (apps/lucent-settings/.../Theme.qml): hover = Qt.lighter(1.08),
pressed = Qt.darker(1.12), accent as text = Qt.darker(1.15) in light and
Qt.lighter(1.35) in dark, white text on it. Qt's lighter/darker are
reproduced exactly, so the shell and Settings show the same colours.
"""
from __future__ import annotations

import colorsys
from dataclasses import dataclass

U16 = 0xFFFF


@dataclass(frozen=True)
class Accent:
    id: str
    name: str
    hex: str


ACCENTS = [
    Accent("indigo", "Indigo", "#4257e8"),
    Accent("azure", "Azure", "#2f7ae0"),
    Accent("lagoon", "Lagoon", "#1f96a8"),
    Accent("violet", "Violet", "#7a55e0"),
    Accent("orchid", "Orchid", "#a54fc4"),
    Accent("rose", "Rose", "#cf4f86"),
    Accent("pine", "Pine", "#3f8f68"),
    Accent("slate", "Slate", "#5f6684"),
]
DEFAULT = ACCENTS[0]

# Indigo, straight from pebble-drift.css part 1 (:root / .dark).
INDIGO = {
    False: {"accent": "#4257e8", "accent-hover": "#3549d6", "accent-pressed": "#2c3dbb",
            "accent-text": "#3346cf", "text-on-accent": "#ffffff", "accent-ring": "#4257e8"},
    True: {"accent": "#7088ff", "accent-hover": "#8297ff", "accent-pressed": "#5f77f0",
           "accent-text": "#9aabff", "text-on-accent": "#0e1230", "accent-ring": "#7f95ff"},
}
SOFT_ALPHA = {False: (0.12, 0.20), True: (0.18, 0.28)}   # --accent-soft, --accent-soft-strong


def _rgb16(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.strip().lstrip("#")
    if len(h) != 6:
        raise ValueError(f"not a #rrggbb colour: {hex_color!r}")
    return tuple(int(h[i:i + 2], 16) * 0x101 for i in (0, 2, 4))


def _name(r16: int, g16: int, b16: int) -> str:
    def div257(x: int) -> int:     # QColor::red() etc.: qt_div_257
        return (x + 128 - ((x + 128) >> 8)) >> 8
    return "#%02x%02x%02x" % (div257(r16), div257(g16), div257(b16))


def _to_hsv(rgb16):
    r, g, b = (c / U16 for c in rgb16)
    mx, mn = max(r, g, b), min(r, g, b)
    delta = mx - mn
    v = round(mx * U16)
    if abs(delta) < 1e-12:
        return U16, 0, v                     # achromatic: hue undefined
    s = round(delta / mx * U16)
    if r == mx:
        hue = (g - b) / delta
    elif g == mx:
        hue = 2.0 + (b - r) / delta
    else:
        hue = 4.0 + (r - g) / delta
    hue *= 60.0
    if hue < 0:
        hue += 360.0
    return round(hue * 100), s, v


def _from_hsv(h, s, v):
    if s == 0 or h == U16:
        return v, v, v
    hh = 0.0 if h == 36000 else h / 6000.0
    sf, vf = s / U16, v / U16
    i = int(hh)
    f = hh - i
    p = vf * (1.0 - sf)
    if i & 1:
        q = vf * (1.0 - sf * f)
        r, g, b = {1: (q, vf, p), 3: (p, q, vf), 5: (vf, p, q)}[i]
    else:
        t = vf * (1.0 - sf * (1.0 - f))
        r, g, b = {0: (vf, t, p), 2: (p, vf, t), 4: (t, p, vf)}[i]
    return round(r * U16), round(g * U16), round(b * U16)


def qt_lighter(hex_color: str, factor: float) -> str:
    """QML Qt.lighter(color, factor) == QColor::lighter(round(factor * 100))."""
    f = round(factor * 100)
    if f < 100:
        return qt_darker(hex_color, 100 / f)
    h, s, v = _to_hsv(_rgb16(hex_color))
    v = (f * v) // 100
    if v > U16:
        s = max(0, s - (v - U16))
        v = U16
    return _name(*_from_hsv(h, s, v))


def qt_darker(hex_color: str, factor: float) -> str:
    """QML Qt.darker(color, factor) == QColor::darker(round(factor * 100))."""
    f = round(factor * 100)
    if f < 100:
        return qt_lighter(hex_color, 100 / f)
    h, s, v = _to_hsv(_rgb16(hex_color))
    return _name(*_from_hsv(h, s, (v * 100) // f))


def find(key: str) -> Accent | None:
    """An accent by id, display name or exact #rrggbb."""
    k = key.strip().lower()
    for a in ACCENTS:
        if k in (a.id, a.name.lower(), a.hex):
            return a
    return None


def nearest(hex_color: str) -> Accent:
    """The swatch closest in hue to any colour (e.g. Plasma's accent taken
    from the wallpaper); greys go to Slate."""
    r, g, b = (c / 0x101 / 255 for c in _rgb16(hex_color))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    if s < 0.18:
        return find("slate")
    def dist(a: Accent) -> float:
        ar, ag, ab = (c / 0x101 / 255 for c in _rgb16(a.hex))
        ah, al, as_ = colorsys.rgb_to_hls(ar, ag, ab)
        d = abs(ah - h)
        return min(d, 1 - d) + (0.5 if as_ < 0.18 else 0)
    return min(ACCENTS, key=dist)


def _rgba(hex_color: str, alpha: float) -> str:
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r}, {g}, {b}, {alpha:g})"


def palette(accent_id: str, dark: bool) -> dict[str, str]:
    """The accent tokens (pebble-drift.css names) for one swatch and mode."""
    a = find(accent_id)
    if a is None:
        raise KeyError(accent_id)
    if a.id == "indigo":
        out = dict(INDIGO[dark])
    else:
        c = a.hex
        out = {"accent": c, "accent-hover": qt_lighter(c, 1.08), "accent-pressed": qt_darker(c, 1.12),
               "accent-text": qt_lighter(c, 1.35) if dark else qt_darker(c, 1.15),
               "text-on-accent": "#ffffff", "accent-ring": qt_lighter(c, 1.08) if dark else c}
    soft, strong = SOFT_ALPHA[dark]
    out["accent-soft"] = _rgba(out["accent"], soft)
    out["accent-soft-strong"] = _rgba(out["accent"], strong)
    return out
