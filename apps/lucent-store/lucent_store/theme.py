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

# Tokens of docs/mockups/concepts-2026/pebble-drift/pebble-drift.css (the
# source of truth): Pebble's materials with Prism's cool palette. Comments
# name the CSS variable each value comes from.
LIGHT = {
    "accent": "#4257e8", "accentHover": "#3549d6",           # --accent, --accent-hover
    "accentSoft": "rgba(66,87,232,.12)", "accentText": "#3346cf", "onAccent": "#ffffff",
    "text": "#171a2b", "text2": "#474d66", "text3": "#5c637c",  # --text-primary/secondary/tertiary
    "line": "rgba(40,50,110,.10)", "lineStrong": "rgba(40,50,110,.17)",
    "winBg": "#f2f3fa",                                        # --surface-window-solid
    "raised": "#fdfdff", "raised2": "#f3f4fb",                 # --surface-raised(-2)
    "well": "rgba(48,58,120,.065)", "wellStrong": "rgba(48,58,120,.11)",   # --surface-sunken(-strong)
    "wellShade": "rgba(25,35,90,.10)", "wellRing": "rgba(30,40,100,.05)",  # --shadow-sunken
    "hover": "rgba(48,58,120,.065)",                           # --state-hover
    # --shadow-raised / --shadow-lift / --shadow-accent, drawn by Shadow.qml
    "shadow": "#19235a", "shadowRing": "rgba(30,40,100,.08)", "topLight": "rgba(255,255,255,.90)",
    "shadowNear": 0.10, "shadowMid": 0.08, "shadowLift": 0.22, "accentShadowNear": 0.30, "accentShadow": 0.40,
    "accentShadowColor": "#1e288c",
    "grain": "grain-dark.png", "grainOpacity": 0.07,           # --grain-*, multiply
    "ok": "#2f8a5c", "okSoft": "rgba(47,138,92,.12)",          # --status-success
    "warn": "#b7791f", "warnSoft": "rgba(183,121,31,.13)",     # --status-warning
    "danger": "#cf3a48",                                       # --status-danger
    # artwork: the "Next generation · beta" panel and alpha badges
    "betaA": "rgba(255,181,71,.12)", "betaB": "rgba(236,63,134,.07)", "betaC": "rgba(122,85,224,.10)",
    "betaLine": "rgba(183,121,31,.24)", "betaNoteBg": "rgba(253,253,255,.72)", "betaNoteText": "#6b4300",
    "alphaBg": "#fff1d6", "alphaText": "#8f5a0c", "alphaLine": "#f0c98a",
    "scrim": "rgba(23,26,43,.28)",
}
DARK = {
    **LIGHT,
    "accent": "#7088ff", "accentHover": "#8297ff",
    "accentSoft": "rgba(112,136,255,.18)", "accentText": "#9aabff", "onAccent": "#0e1230",
    "text": "#eef0fa", "text2": "#bcc1d6", "text3": "#9ca2bb",
    "line": "rgba(220,228,255,.08)", "lineStrong": "rgba(220,228,255,.14)",
    "winBg": "#1d1f2e",
    "raised": "#33364d", "raised2": "#2c2f44",
    "well": "rgba(0,0,10,.20)", "wellStrong": "rgba(0,0,10,.30)",
    "wellShade": "rgba(0,0,0,.35)", "wellRing": "rgba(220,228,255,.04)",
    "hover": "rgba(220,228,255,.07)",
    "shadow": "#000000", "shadowRing": "rgba(0,0,0,.35)", "topLight": "rgba(220,228,255,.08)",
    "shadowNear": 0.30, "shadowMid": 0.25, "shadowLift": 0.50, "accentShadowNear": 0.40, "accentShadow": 0.35,
    "accentShadowColor": "#000000",
    "grain": "grain-light.png", "grainOpacity": 0.09,          # screen
    "ok": "#56c08a", "okSoft": "rgba(86,192,138,.14)",
    "warn": "#e3a547", "warnSoft": "rgba(227,165,71,.16)",
    "danger": "#ef5f6b",
    "betaA": "rgba(255,181,71,.08)", "betaB": "rgba(236,63,134,.06)", "betaC": "rgba(160,132,255,.10)",
    "betaLine": "rgba(227,165,71,.26)", "betaNoteBg": "rgba(0,0,10,.22)", "betaNoteText": "#f0c784",
    "alphaBg": "#3a2e17", "alphaText": "#e3a547", "alphaLine": "rgba(227,165,71,.40)",
    "scrim": "rgba(0,0,10,.50)",
}

# Everything that isn't a colour: type sizes (points = CSS px * 0.75, so
# Plasma's font DPI setting still applies), corner radii and the layout
# measures. Pebble nests radii window 18 -> card 14 -> control 10 -> chip 7.
METRICS = {
    # --font-sans; the app font falls back in this order (app.py)
    "fontFamilies": ["Figtree", "Inter", "Noto Sans"],
    # --type-*: display 32, heading 19, subhead 17, body 15.5, small 14.5, caption 14 (never below)
    "fontH1": 24, "fontH2": 14.25, "fontDialog": 15, "fontTitle": 12.75, "fontName": 12.375,
    "fontLead": 12, "fontBody": 11.625, "fontText": 11.25, "fontSmall": 10.875, "fontCaption": 10.5,
    "fontMeta": 10.5, "fontLabel": 10.5, "fontBadge": 10.5,
    # --radius-*: window 18 -> card 14 -> control 10 -> chip 6
    "radiusBadge": 6, "radiusChip": 6, "radiusItem": 10, "radiusButton": 10, "radiusField": 10,
    "radiusShot": 10, "radiusRow": 14, "radiusCard": 14, "radiusPanel": 18,
    # --space-* (4 px grid) applied to the 06-store layout
    "paneX": 44, "paneTop": 24, "sectionGap": 32, "gridGap": 16, "rowGap": 16,
    "sideInset": 12, "sidebarWidth": 268, "sideItemHeight": 40, "buttonHeight": 40, "buttonSmallHeight": 36,
    "searchWidth": 440, "searchHeight": 40, "iconCard": 64, "iconCraft": 56, "iconRow": 52, "iconPage": 104,
    "cardPadX": 20, "cardPadY": 20, "homeCards": 6,
}

_RGBA = re.compile(r"rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)")


def qml_color(css):
    if not isinstance(css, str):     # numbers and lists pass through
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
