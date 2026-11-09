#!/usr/bin/env python3
"""A simulated frame of the `lucent` Plymouth splash, composed the way the
two-step plugin does it from lucent.plymouth: the background.png scaled to the
screen (over the fallback gradient), the watermark and a throbber frame at
their alignments. Not a capture of a real boot: check that in the VM.

    python3 design/preview-bootsplash.py OUT.png [WIDTHxHEIGHT] [throbber.png]

The throbber frames come from Fedora's plymouth-theme-spinner at image build
time; pass one (e.g. plymouth's themes/spinner/throbber-0001.png) to see it.
Needs Pillow and numpy.
"""
import configparser
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "system_files/usr/share/plymouth/themes/lucent"


def colour(value: str) -> np.ndarray:
    v = int(value, 16)
    return np.array([(v >> 16) & 255, (v >> 8) & 255, v & 255], dtype=np.float32)


def main() -> None:
    out = Path(sys.argv[1])
    w, h = (int(v) for v in (sys.argv[2] if len(sys.argv) > 2 else "2560x1440").split("x"))
    throbber = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    cfg = configparser.ConfigParser(inline_comment_prefixes=None)
    cfg.read(THEME / "lucent.plymouth")
    ts = cfg["two-step"]

    t = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    frame = (colour(ts["BackgroundStartColor"]) * (1 - t) + colour(ts["BackgroundEndColor"]) * t)
    frame = Image.fromarray(np.repeat(frame, w, axis=1).astype(np.uint8))
    if (THEME / "background.png").exists() and ts.getboolean("ScaleBackgroundImage", False):
        frame = Image.open(THEME / "background.png").convert("RGB").resize((w, h), Image.Resampling.BILINEAR)

    def place(img: Image.Image, hx: float, vy: float) -> None:
        x = round(w * hx - img.width * hx)
        y = round(h * vy - img.height * vy)
        frame.paste(img, (x, y), img)

    place(Image.open(THEME / "watermark.png").convert("RGBA"),
          float(ts["WatermarkHorizontalAlignment"]), float(ts["WatermarkVerticalAlignment"]))
    if throbber:
        place(Image.open(throbber).convert("RGBA"), float(ts["HorizontalAlignment"]), float(ts["VerticalAlignment"]))
    frame.save(out)
    print(out, frame.size)


if __name__ == "__main__":
    main()
