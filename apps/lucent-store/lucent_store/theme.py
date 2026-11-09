"""All of the store's look in one place: Lucent design tokens
(docs/mockups/lucent.css) for QML, light and dark, plus sizes and radii.
The QML views use only `store.t.<token>` for colours, type sizes, radii
and the main layout measures.

QML colours are "#AARRGGBB", so the CSS rgba() values are converted here.
Light or dark follows the system colour scheme (Plasma's Lucent Light /
Lucent Dark), and switches live when the user changes it.
"""

from __future__ import annotations

import os
import re

LIGHT = {
    "accent": "#3b6ef5", "accentHover": "#2f5fe0", "accentSoft": "rgba(59,110,245,.12)", "accentText": "#ffffff",
    "text": "#1b1f27", "text2": "#4c5463", "text3": "#6a7282",
    "line": "rgba(20,28,45,.10)", "lineStrong": "rgba(20,28,45,.16)",
    "winBg": "#ffffff", "side": "#f4f5f8", "field": "#eceef3", "hover": "rgba(20,28,45,.05)",
    "sel": "rgba(59,110,245,.14)", "card": "#ffffff", "card2": "#f7f8fa",
    "ok": "#1f9d55", "okSoft": "rgba(31,157,85,.12)", "warn": "#b86e00", "warnSoft": "#fff3df",
    "danger": "#d23b3b", "shadow": "rgba(15,20,35,.04)",
    # Next generation · beta panel
    "betaA": "rgba(255,181,71,.12)", "betaB": "rgba(236,63,134,.08)", "betaC": "rgba(124,92,255,.10)",
    "betaLine": "rgba(240,122,30,.25)", "betaNoteBg": "rgba(255,255,255,.65)", "betaNoteText": "#6b4300",
    "alphaBg": "#fff1d6", "alphaText": "#9a5800", "alphaLine": "#f3cf8e",
    "scrim": "rgba(15,20,35,.28)",
}
DARK = {
    **LIGHT,
    "accent": "#5b8bff", "accentHover": "#6e98ff", "accentSoft": "rgba(91,139,255,.18)",
    "text": "#eef0f5", "text2": "#b4bac6", "text3": "#959cab",
    "line": "rgba(255,255,255,.09)", "lineStrong": "rgba(255,255,255,.15)",
    "winBg": "#1f2229", "side": "#191b21", "field": "#2b2f38", "hover": "rgba(255,255,255,.05)",
    "sel": "rgba(91,139,255,.22)", "card": "#262a32", "card2": "#23262d",
    "ok": "#3cc47a", "okSoft": "rgba(60,196,122,.14)", "warn": "#f0b04a", "warnSoft": "#3a2e17",
    "danger": "#ff6b6b", "shadow": "rgba(0,0,0,.20)",
    "betaA": "rgba(255,181,71,.10)", "betaB": "rgba(236,63,134,.07)", "betaC": "rgba(124,92,255,.10)",
    "betaLine": "rgba(240,160,70,.28)", "betaNoteBg": "rgba(0,0,0,.22)", "betaNoteText": "#f3c784",
    "alphaBg": "#3a2e17", "alphaText": "#f0b04a", "alphaLine": "rgba(240,176,74,.40)",
    "scrim": "rgba(0,0,0,.45)",
}

# Everything that isn't a colour: type sizes (points = CSS px * 0.75, so
# Plasma's font DPI setting still applies), corner radii and the layout
# measures of the mockup. A restyle swaps these values, not the views.
METRICS = {
    "font": "Inter",
    "fontH1": 22.5, "fontH2": 16.5, "fontDialog": 15, "fontTitle": 12.75, "fontName": 12.375,
    "fontLead": 12, "fontBody": 11.625, "fontText": 11.25, "fontSmall": 10.875, "fontCaption": 10.5,
    "fontMeta": 10.125, "fontLabel": 9.75, "fontBadge": 9.375,
    "radiusBadge": 6, "radiusChip": 8, "radiusItem": 9, "radiusButton": 10, "radiusField": 12,
    "radiusShot": 14, "radiusRow": 16, "radiusCard": 18, "radiusPanel": 20,
    "paneX": 56, "paneTop": 34, "sectionGap": 34, "gridGap": 18, "rowGap": 16,
    "sidebarWidth": 290, "sideItemHeight": 44, "buttonHeight": 40, "buttonSmallHeight": 36,
    "searchWidth": 460, "searchHeight": 44, "iconCard": 64, "iconCraft": 60, "iconRow": 56, "iconPage": 104,
    "cardPadX": 22, "cardPadY": 20, "homeCards": 6,
}

_RGBA = re.compile(r"rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)")


def qml_color(css: str) -> str:
    m = _RGBA.fullmatch(css.replace(" ", ""))
    if not m:
        return css
    r, g, b, a = int(m[1]), int(m[2]), int(m[3]), float(m[4])
    return f"#{round(a * 255):02x}{r:02x}{g:02x}{b:02x}"


def tokens(dark: bool) -> dict:
    return {**METRICS, **{k: qml_color(v) for k, v in (DARK if dark else LIGHT).items()}}


def forced_scheme() -> str | None:
    """LUCENT_STORE_THEME=light|dark overrides the system (previews, screenshots)."""
    v = os.environ.get("LUCENT_STORE_THEME", "").lower()
    return v if v in ("light", "dark") else None
