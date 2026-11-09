#!/usr/bin/env python3
"""Contact sheet of the Pebble Drift wallpaper packages as shipped: Drift,
Tide and Aurora, day (images/) and night (images_dark/), from their
2560x1440 files, with the package's file list under each name.

    python3 design/preview-wallpapers.py OUT.jpg
Needs Pillow.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
WALLS = ROOT / "system_files/usr/share/wallpapers"
NAMES = ["Drift", "Tide", "Aurora"]
TILE = (800, 450)
PAD, LABEL = 32, 64


def font(size: int):
    for path in ("/System/Library/Fonts/Supplemental/Arial.ttf", "/usr/share/fonts/rsms-inter-fonts/Inter.ttc",
                 "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf"):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def main() -> None:
    out = Path(sys.argv[1])
    w = PAD + len(NAMES) * (TILE[0] + PAD)
    h = PAD + 2 * (TILE[1] + LABEL + PAD)
    sheet = Image.new("RGB", (w, h), "#f2f3fa")
    d = ImageDraw.Draw(sheet)
    big, small = font(22), font(16)
    for col, name in enumerate(NAMES):
        for row, sub in enumerate(("images", "images_dark")):
            x = PAD + col * (TILE[0] + PAD)
            y = PAD + row * (TILE[1] + LABEL + PAD)
            img = Image.open(WALLS / name / "contents" / sub / "2560x1440.jpg").convert("RGB")
            sheet.paste(img.resize(TILE, Image.Resampling.LANCZOS), (x, y))
            sizes = ", ".join(sorted(p.stem for p in (WALLS / name / "contents" / sub).glob("*.jpg")))
            d.text((x, y + TILE[1] + 10), f"{name} {'night' if row else 'day'}{'  (default)' if name == 'Drift' else ''}",
                   fill="#171a2b", font=big)
            d.text((x, y + TILE[1] + 38), f"{name}/contents/{sub}/: {sizes}", fill="#474d66", font=small)
    sheet.save(out, quality=90)
    print(out, sheet.size)


if __name__ == "__main__":
    main()
