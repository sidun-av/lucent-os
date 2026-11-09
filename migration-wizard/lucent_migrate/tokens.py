"""Pebble Drift design tokens, read from tokens.css.

tokens.css is a verbatim copy of part 1 of the design's source of truth,
docs/mockups/concepts-2026/pebble-drift/pebble-drift.css (a test keeps the
two identical; refresh it with `python3 design/sync-wizard-tokens.py`).
`load(dark)` returns the CSS custom properties without their leading `--`,
light from `:root`, dark as `:root` overridden by `.dark`, with every
`var(--name)` resolved in that mode.
"""

from __future__ import annotations

import functools
import re
from pathlib import Path

TOKENS_CSS = Path(__file__).with_name("tokens.css")

_COMMENT = re.compile(r"/\*.*?\*/", re.S)
_DECL = re.compile(r"--([\w-]+)\s*:\s*((?:[^;\"']|\"[^\"]*\"|'[^']*')+);")
_VAR = re.compile(r"var\(--([\w-]+)\)")
_PART1 = re.compile(r"/\* =+\s*PART 1.*?(?=/\* =+\s*PART 2)", re.S)


def _block(css: str, selector: str) -> str:
    """Body of the rule whose selector is exactly `selector` ('' if none)."""
    m = re.search(r"(?:^|[}\s])" + re.escape(selector) + r"\s*\{([^}]*)\}", css)
    return m.group(1) if m else ""


def parse(css: str) -> tuple[dict[str, str], dict[str, str]]:
    """(light, dark-overrides): the custom properties of `:root` and `.dark`."""
    css = _COMMENT.sub("", css)
    light, dark = ({name: value.strip() for name, value in _DECL.findall(_block(css, sel))}
                   for sel in (":root", ".dark"))
    return light, dark


def resolve(props: dict[str, str]) -> dict[str, str]:
    """Replace every var(--name) by its value; unknown names raise KeyError."""
    def value(name: str, seen: tuple[str, ...] = ()) -> str:
        if name in seen:
            raise ValueError(f"var() cycle: {' -> '.join(seen + (name,))}")
        return _VAR.sub(lambda m: value(m.group(1), seen + (name,)), props[name])
    return {name: value(name) for name in props}


@functools.cache
def load(dark: bool) -> dict[str, str]:
    light, overrides = parse(TOKENS_CSS.read_text(encoding="utf-8"))
    return resolve({**light, **overrides} if dark else light)


def extract(css: str) -> str:
    """Part 1 (the tokens) of pebble-drift.css, from its banner to part 2's."""
    m = _PART1.search(css)
    if not m:
        raise ValueError("no PART 1 / PART 2 banners in the stylesheet")
    return m.group(0).rstrip() + "\n"


def px(value: str) -> float:
    """'15.5px' -> 15.5"""
    return float(value.strip().removesuffix("px"))


def qss(value: str) -> str:
    """A CSS colour token as a Qt style sheet value: rgba() alpha gets its
    leading zero, a vertical linear-gradient() becomes a qlineargradient."""
    value = value.strip()
    m = re.fullmatch(r"linear-gradient\((.*)\)", value)
    if m:
        top, bottom = (qss(c) for c in re.split(r",\s*(?![^()]*\))", m.group(1)))
        return f"qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {top}, stop:1 {bottom})"
    return re.sub(r"(?<![\d.])\.(\d)", r"0.\1", value)
