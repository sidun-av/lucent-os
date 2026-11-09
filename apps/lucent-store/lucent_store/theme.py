"""All of the store's look in one place, as tokens for QML.

Materials are the "Pebble" direction (docs/mockups/concepts-2026/pebble/
pebble.css): matte near-opaque surfaces with a fine grain, depth from soft
long shadows, raised "pillow" controls and recessed wells. The
layout keeps docs/mockups/06-store. QML views use only `store.t.<token>`
for colours, type, radii, shadows and the main measures, so a restyle
swaps this file, not the views.

QML colours are "#AARRGGBB", so CSS rgba() values are converted here.
Light or dark follows the system colour scheme and switches live.
"""

from __future__ import annotations

import os
import re

# Interim palette: Prism's cool neutrals and blue/indigo accent
# (concepts-2026/prism/prism.css) on Pebble's materials; to be replaced by
# concepts-2026/pebble-drift/pebble-drift.css.
LIGHT = {
    "accent": "#3d6bff", "accentHover": "#2f5af0", "accentSoft": "rgba(61,107,255,.14)",
    "accentText": "#2c55e0", "onAccent": "#ffffff",
    "text": "#10131c", "text2": "#444b5c", "text3": "#626a7d",
    "line": "rgba(16,24,48,.08)", "lineStrong": "rgba(16,24,48,.14)",
    # surfaces: matte frost, opaque here (looks the same without a compositor)
    "winBg": "#f2f4fa", "raised": "#ffffff", "raised2": "#f6f8fc",
    "well": "rgba(60,70,110,.065)", "wellStrong": "rgba(60,70,110,.10)",
    "wellShade": "rgba(20,30,80,.10)", "wellRing": "rgba(16,24,48,.05)",
    "hover": "rgba(60,70,110,.06)",
    # shadows (colour + strength of each layer; see Raised.qml)
    "shadow": "#1e286e", "shadowRing": "rgba(10,18,50,.09)", "topLight": "rgba(255,255,255,.90)",
    "shadowNear": 0.10, "shadowMid": 0.08, "shadowLift": 0.20,
    "grain": "grain-dark.png", "grainOpacity": 0.06,
    "ok": "#1f9d55", "okSoft": "rgba(31,157,85,.12)", "warn": "#b86e00", "warnSoft": "rgba(255,181,71,.18)",
    "danger": "#d23b3b",
    # Next generation · beta panel
    "betaA": "rgba(255,181,71,.12)", "betaB": "rgba(236,63,134,.07)", "betaC": "rgba(124,92,255,.10)",
    "betaLine": "rgba(240,122,30,.22)", "betaNoteBg": "rgba(255,255,255,.70)", "betaNoteText": "#6b4300",
    "alphaBg": "#fff1d6", "alphaText": "#9a5800", "alphaLine": "#f3cf8e",
    "scrim": "rgba(16,19,28,.28)",
}
DARK = {
    **LIGHT,
    "accent": "#6f93ff", "accentHover": "#86a4ff", "accentSoft": "rgba(111,147,255,.20)",
    "accentText": "#9db4ff", "onAccent": "#ffffff",
    "text": "#f2f4fb", "text2": "#b9c0d2", "text3": "#9aa2b6",
    "line": "rgba(255,255,255,.08)", "lineStrong": "rgba(255,255,255,.13)",
    "winBg": "#1b1e2b", "raised": "#2b2f42", "raised2": "#262a3a",
    "well": "rgba(0,0,0,.20)", "wellStrong": "rgba(0,0,0,.28)",
    "wellShade": "rgba(0,0,0,.35)", "wellRing": "rgba(255,255,255,.04)",
    "hover": "rgba(255,255,255,.06)",
    "shadow": "#000000", "shadowRing": "rgba(0,0,0,.40)", "topLight": "rgba(255,255,255,.07)",
    "shadowNear": 0.30, "shadowMid": 0.25, "shadowLift": 0.45,
    "grain": "grain-light.png", "grainOpacity": 0.07,
    "ok": "#4cd38a", "okSoft": "rgba(76,211,138,.14)", "warn": "#f0b04a", "warnSoft": "rgba(240,176,74,.16)",
    "danger": "#ff7b7b",
    "betaA": "rgba(255,181,71,.09)", "betaB": "rgba(236,63,134,.07)", "betaC": "rgba(124,92,255,.11)",
    "betaLine": "rgba(240,160,70,.26)", "betaNoteBg": "rgba(0,0,0,.22)", "betaNoteText": "#f3c784",
    "alphaBg": "#3a2e17", "alphaText": "#f0b04a", "alphaLine": "rgba(240,176,74,.40)",
    "scrim": "rgba(0,0,0,.45)",
}

# Everything that isn't a colour: type sizes (points = CSS px * 0.75, so
# Plasma's font DPI setting still applies), corner radii and the layout
# measures. Pebble nests radii window 18 -> card 14 -> control 10 -> chip 7.
METRICS = {
    "font": "Inter", "fontFallback": "Noto Sans",
    "fontH1": 22.5, "fontH2": 14.25, "fontDialog": 15, "fontTitle": 12.75, "fontName": 12.375,
    "fontLead": 12, "fontBody": 11.625, "fontText": 11.25, "fontSmall": 10.875, "fontCaption": 10.5,
    "fontMeta": 10.125, "fontLabel": 10.125, "fontBadge": 9.375,
    "radiusBadge": 6, "radiusChip": 7, "radiusItem": 10, "radiusButton": 10, "radiusField": 10,
    "radiusShot": 12, "radiusRow": 14, "radiusCard": 14, "radiusPanel": 18,
    "paneX": 44, "paneTop": 26, "sectionGap": 30, "gridGap": 16, "rowGap": 14,
    "sideInset": 12, "sidebarWidth": 268, "sideItemHeight": 40, "buttonHeight": 40, "buttonSmallHeight": 36,
    "searchWidth": 440, "searchHeight": 42, "iconCard": 64, "iconCraft": 58, "iconRow": 54, "iconPage": 104,
    "cardPadX": 22, "cardPadY": 20, "homeCards": 6,
}

_RGBA = re.compile(r"rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)")


def qml_color(css):
    if not isinstance(css, str):
        return css
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
