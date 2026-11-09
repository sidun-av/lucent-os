"""Pebble Drift design tokens, read from the source of truth:
docs/mockups/concepts-2026/pebble-drift/pebble-drift.css, part 1
(`:root` = light, `.dark` = what dark mode overrides).

    t = tokens.load()
    t.light["surface-window"]   -> "rgba(244, 245, 251, .93)"
    t.dark["accent"]            -> "#7088ff"

Names drop the leading "--". var() references are resolved per mode, so a
token declared once in :root (e.g. --gauge-1: var(--accent)) follows the dark
accent in .dark. Helpers turn values into numbers the generators need.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "docs/mockups/concepts-2026/pebble-drift/pebble-drift.css"
# Glass Card (the November direction): the dock, cards and fields read these.
GLASS = ROOT / "docs/mockups/concepts-2026/glass/glass.css"

_COMMENT = re.compile(r"/\*.*?\*/", re.S)
_DECL = re.compile(r"--([\w-]+)\s*:\s*((?:[^;\"']|\"[^\"]*\"|'[^']*')+?)\s*;")
_VAR = re.compile(r"var\(--([\w-]+)\)")


@dataclass
class Tokens:
    light: dict[str, str]
    dark: dict[str, str]

    def mode(self, dark: bool) -> dict[str, str]:
        return self.dark if dark else self.light


def _block(css: str, selector: str) -> str:
    m = re.search(r"(?:^|[\s}])" + re.escape(selector) + r"\s*\{", css)
    if not m:
        return ""
    depth, i = 1, m.end()
    while depth:
        depth += {"{": 1, "}": -1}.get(css[i], 0)
        i += 1
    return css[m.end():i - 1]


def _decls(block: str) -> dict[str, str]:
    return {name: " ".join(value.split()) for name, value in _DECL.findall(block)}


def _resolve(raw: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}

    def get(name: str, seen: tuple[str, ...] = ()) -> str:
        if name in out:
            return out[name]
        if name not in raw:
            raise KeyError(f"--{name} is not defined")
        if name in seen:
            raise ValueError("var() cycle: " + " -> ".join(seen + (name,)))
        val = _VAR.sub(lambda m: get(m.group(1), seen + (name,)), raw[name])
        out[name] = val
        return val

    for n in raw:
        get(n)
    return out


def parse(css: str) -> Tokens:
    css = _COMMENT.sub("", css)
    root = _decls(_block(css, ":root"))
    dark = {**root, **_decls(_block(css, ".dark"))}
    return Tokens(_resolve(root), _resolve(dark))


def load(path: Path = CSS) -> Tokens:
    return parse(Path(path).read_text(encoding="utf-8"))


# ------------------------------------------------------------- values ----
def color(value: str) -> tuple[float, float, float, float]:
    """'#rrggbb' / 'rgb(...)' / 'rgba(r, g, b, a)' -> (r, g, b, a) in 0..1."""
    v = value.strip()
    if re.fullmatch(r"#[0-9a-fA-F]{6}", v):
        return tuple(int(v[i:i + 2], 16) / 255 for i in (1, 3, 5)) + (1.0,)
    m = re.fullmatch(r"rgba?\(([^)]*)\)", v)
    if not m:
        raise ValueError(f"not a colour: {value!r}")
    parts = [p.strip() for p in m.group(1).split(",")]
    r, g, b = (float(p) / 255 for p in parts[:3])
    a = float(parts[3]) if len(parts) > 3 else 1.0
    return (r, g, b, a)


def px(value: str) -> float:
    m = re.fullmatch(r"\s*(-?[\d.]+)px\s*", value)
    if not m:
        raise ValueError(f"not a px length: {value!r}")
    f = float(m.group(1))
    return int(f) if f.is_integer() else f


def hexcolor(rgb) -> str:
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(c * 255))) for c in rgb[:3])


def flatten(value: str, under: str) -> str:
    """A (translucent) colour composited over an opaque one, as #rrggbb.
    For places that can't take alpha (KDE colour schemes, Kvantum's palette)."""
    r, g, b, a = color(value)
    br, bg, bb, _ = color(under)
    return hexcolor((r * a + br * (1 - a), g * a + bg * (1 - a), b * a + bb * (1 - a)))


def rgba_str(value: str, alpha: float | None = None) -> str:
    """Normalised 'rgba(r,g,b,a)' (optionally with a new alpha)."""
    r, g, b, a = color(value)
    a = a if alpha is None else alpha
    return f"rgba({round(r * 255)},{round(g * 255)},{round(b * 255)},{a:g})"


def shadows(value: str) -> list[tuple]:
    """CSS box-shadow list -> [(dx, dy, blur, spread, colour[, 'inset'])]."""
    out = []
    for part in re.split(r",(?![^(]*\))", value):
        part = part.strip()
        inset = part.startswith("inset ")
        if inset:
            part = part[6:].strip()
        m = re.fullmatch(r"(.*?)\s*((?:rgba?\([^)]*\))|#[0-9a-fA-F]{6})", part)
        if not m:
            raise ValueError(f"unsupported shadow: {part!r}")
        nums = [px(n) if n.endswith("px") else float(n) for n in m.group(1).split()]
        nums += [0] * (4 - len(nums))
        dx, dy, blur, spread = (int(n) if float(n).is_integer() else n for n in nums[:4])
        out.append((dx, dy, blur, spread, m.group(2)) + (("inset",) if inset else ()))
    return out
