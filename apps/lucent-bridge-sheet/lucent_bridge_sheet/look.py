"""Pebble Drift for the launch sheet: colours and sizes from the design
tokens (docs/mockups/concepts-2026/pebble-drift/pebble-drift.css part 1,
read through the migration wizard's `lucent_migrate.tokens`, the copy the
image ships in /usr/lib/lucent), light or dark following the system.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtGui import QColor, QFont, QFontDatabase, QGuiApplication, QPalette

from lucent_migrate import tokens

HERE = Path(__file__).parent
# Figtree (--font-sans) ships with Lucent Settings (SIL OFL 1.1); the sheet
# uses that copy when it is there and falls back to the system's Inter.
FONT_DIRS = [
    HERE.parent / "lucent_settings" / "fonts",                                   # /usr/lib/lucent
    HERE.parents[2] / "apps" / "lucent-settings" / "lucent_settings" / "fonts",  # checkout
]
BASE_POINTS = 11.0   # Lucent's UI font size (kdeglobals); the tokens' px are for it


def color(css: str) -> QColor:
    """'#4257e8' or 'rgba(48, 58, 120, .065)' -> QColor."""
    css = css.strip()
    if css.startswith("#"):
        return QColor(css)
    m = re.fullmatch(r"rgba?\(([^)]*)\)", css)
    if not m:
        raise ValueError(f"not a colour: {css!r}")
    parts = [float(p) for p in m.group(1).split(",")]
    c = QColor(int(parts[0]), int(parts[1]), int(parts[2]))
    if len(parts) > 3:
        c.setAlphaF(parts[3])
    return c


def gradient(css: str) -> tuple[QColor, QColor]:
    """'linear-gradient(#fdfdff, #f3f4fb)' -> (top, bottom)."""
    m = re.fullmatch(r"linear-gradient\((.*)\)", css.strip())
    if not m:
        c = color(css)
        return c, c
    top, bottom = re.split(r",\s*(?![^()]*\))", m.group(1))
    return color(top), color(bottom)


def over(top: QColor, bottom: QColor) -> QColor:
    """`top` (possibly translucent) composited over opaque `bottom`."""
    a = top.alphaF()
    return QColor.fromRgbF(top.redF() * a + bottom.redF() * (1 - a),
                           top.greenF() * a + bottom.greenF() * (1 - a),
                           top.blueF() * a + bottom.blueF() * (1 - a))


def system_is_dark() -> bool:
    """LUCENT_SHEET_THEME=light|dark wins (previews, tests); else the palette
    Plasma gives Qt apps for the current colour scheme."""
    forced = os.environ.get("LUCENT_SHEET_THEME", "").lower()
    if forced in ("light", "dark"):
        return forced == "dark"
    app = QGuiApplication.instance()
    palette = app.palette() if app else QPalette()
    return palette.color(QPalette.ColorRole.Window).lightness() < 128


@dataclass
class Look:
    dark: bool
    scale: float
    card: QColor
    text: QColor
    text2: QColor
    text3: QColor
    accent: QColor
    on_accent: QColor
    well: QColor            # --surface-sunken, opaque over the card
    track: QColor           # --surface-sunken-strong, opaque over the card
    raised: tuple[QColor, QColor]
    line: QColor
    line_strong: QColor
    highlight: QColor       # the pillow's top light
    shadow: QColor          # the long soft drop of --shadow-window
    warning: QColor
    radius_window: float
    radius_card: float
    radius_control: float
    radius_chip: float

    def px(self, v: float) -> float:
        return v * self.scale


def load(dark: bool | None = None, scale: float | None = None) -> Look:
    if dark is None:
        dark = system_is_dark()
    t = tokens.load(dark)
    if scale is None:
        app = QGuiApplication.instance()
        points = app.font().pointSizeF() if app else BASE_POINTS
        scale = 1.0 if points <= 0 else max(0.8, min(2.0, points / BASE_POINTS))
    card = color(t["surface-window-solid"])
    highlight = re.search(r"rgba?\([^)]*\)", t["highlight-top"]).group(0)
    shadows = re.findall(r"rgba?\([^)]*\)", t["shadow-window"])
    return Look(
        dark=dark, scale=scale, card=card,
        text=color(t["text-primary"]), text2=color(t["text-secondary"]), text3=color(t["text-tertiary"]),
        accent=color(t["accent"]), on_accent=color(t["text-on-accent"]),
        well=over(color(t["surface-sunken"]), card), track=over(color(t["surface-sunken-strong"]), card),
        raised=(color(t["surface-raised"]), color(t["surface-raised-2"])),
        line=over(color(t["line"]), card), line_strong=over(color(t["line-strong"]), card),
        highlight=color(highlight), shadow=color(shadows[-1]),
        warning=color(t["status-warning"]),
        radius_window=tokens.px(t["radius-window"]), radius_card=tokens.px(t["radius-card"]),
        radius_control=tokens.px(t["radius-control"]), radius_chip=tokens.px(t["radius-chip"]),
    )


def load_fonts() -> list[str]:
    """Families from the bundled Figtree files that could be registered."""
    families: list[str] = []
    for folder in FONT_DIRS:
        for ttf in sorted(folder.glob("*.ttf")):
            font_id = QFontDatabase.addApplicationFont(str(ttf))
            families += [f for f in QFontDatabase.applicationFontFamilies(font_id) if f not in families]
        if families:
            break
    return families


def font(px: float, weight: int, base: QFont | None = None) -> QFont:
    """--font-sans (Figtree, then Inter, then the system font) at px / weight."""
    f = QFont(base or QFont())
    wanted = [x.strip().strip('"') for x in tokens.load(False)["font-sans"].split(",")]
    f.setFamilies([x for x in wanted if x not in ("system-ui", "sans-serif")] + f.families())
    f.setPixelSize(max(1, round(px)))
    f.setWeight(QFont.Weight(weight))
    return f
