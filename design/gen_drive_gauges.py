#!/usr/bin/env python3
"""Ring gauges for the drives on Files' "This PC" page (kio_thispc).

docs/mockups/concepts-2026/pebble-drift/01-desktop: each drive has a ring
showing how full it is, in --gauge-1 (accent) for the system drive, --gauge-2
(slate) for the read-only Windows drive and --gauge-3 (violet) for USB drives,
on a --gauge-track ring. Dolphin draws item icons, so the ring is the icon:
lucent-drive-<kind>-<used %, in steps of 5> plus lucent-drive-<kind> (usage
not known yet: track only), with the drive's glyph in the middle.

KDE recolours the "ColorScheme-*" classes from the palette (light/dark, and
the user's accent for the system drive); slate and violet sit between their
light and dark token values so they read on both.

Writes system_files/usr/share/icons/hicolor/scalable/devices/. Run from the
repo root: python3 design/gen_drive_gauges.py
"""
import math
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "system_files/usr/share/icons/hicolor/scalable/devices"

# lucent.js glyphs (24 px grid)
DRIVE = '<rect x="3.5" y="7" width="17" height="10" rx="2.5"/><path d="M7 12h5"/>'
DRIVE_DOT = '<circle cx="16.5" cy="12" r="1"/>'
HOME = '<path d="M4 11l8-7 8 7v8a1.5 1.5 0 0 1-1.5 1.5H15v-6H9v6H5.5A1.5 1.5 0 0 1 4 19z"/>'

KINDS = {
    # kind: (ring colour class or fixed colour, glyph, glyph dot)
    "system": ("ColorScheme-Highlight", HOME, ""),
    "windows": ("#848ca6", DRIVE, DRIVE_DOT),   # --gauge-2: #7c84a0 light, #8d94ad dark
    "usb": ("#8c6cf0", DRIVE, DRIVE_DOT),       # --gauge-3: #7a55e0 light, #a084ff dark
    "other": ("#5f8fb0", DRIVE, DRIVE_DOT),
}

STYLE = ('<style type="text/css" id="current-color-scheme">'
         '.ColorScheme-Text{color:#171a2b;}.ColorScheme-Highlight{color:#4257e8;}</style>')
R, W, C = 25.5, 7.0, 32.0


def ring(color: str, step: int | None) -> str:
    track = (f'<circle class="ColorScheme-Text" cx="{C}" cy="{C}" r="{R}" fill="none" '
             f'stroke="currentColor" stroke-opacity=".13" stroke-width="{W}"/>')
    if not step:
        return track
    length = 2 * math.pi * R
    dash = length * step / 100
    attrs = (f'class="{color}" stroke="currentColor"' if color.startswith("ColorScheme")
             else f'stroke="{color}"')
    arc = (f'<circle {attrs} cx="{C}" cy="{C}" r="{R}" fill="none" stroke-width="{W}" '
           f'stroke-linecap="round" stroke-dasharray="{dash:.2f} {length:.2f}" '
           f'transform="rotate(-90 {C} {C})"/>')
    return track + arc


def icon(kind: str, step: int | None) -> str:
    color, glyph, dot = KINDS[kind]
    # glyph: 24 px grid scaled to 22 px, centred
    g = (f'<g class="ColorScheme-Text" transform="translate(20.5 20.5) scale(0.9583)" fill="none" '
         f'stroke="currentColor" stroke-opacity=".78" stroke-width="1.9" stroke-linecap="round" '
         f'stroke-linejoin="round">{glyph}'
         + (f'<g fill="currentColor" stroke="none" fill-opacity=".78">{dot}</g>' if dot else "")
         + '</g>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">'
            f'{STYLE}{ring(color, step)}{g}</svg>\n')


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    n = 0
    for kind in KINDS:
        (OUT / f"lucent-drive-{kind}.svg").write_text(icon(kind, None))
        n += 1
        for step in range(0, 101, 5):
            (OUT / f"lucent-drive-{kind}-{step}.svg").write_text(icon(kind, step))
            n += 1
    print(f"{n} icons in {OUT}")


if __name__ == "__main__":
    main()
