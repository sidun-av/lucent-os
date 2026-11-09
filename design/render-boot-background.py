#!/usr/bin/env python3
"""Plymouth background for the `lucent` boot splash: Drift night as the login
screen shows it (blurred and dimmed, system_files/usr/share/sddm/themes/
lucent/Main.qml), so boot hands over to the login screen without a jump.

Blurred artwork has no detail to lose, so it ships small (640x360, a few
tens of KB in the initramfs) and two-step scales it to the screen once
(ScaleBackgroundImage=true in lucent.plymouth). Also prints the top and
bottom averages that lucent.plymouth uses as its fallback gradient.
Needs Pillow and numpy. Run: python3 design/render-boot-background.py
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "system_files/usr/share/wallpapers/Drift/contents/images_dark/2560x1440.jpg"
OUT = ROOT / "system_files/usr/share/plymouth/themes/lucent/background.png"
BLUR = 0.9 * 64                     # Main.qml: MultiEffect blurMax 64, blur 0.9
SCRIM, SCRIM_OPACITY = (0x0e, 0x10, 0x20), 0.45   # Main.qml: the Drift-night veil over it
SIZE = (640, 360)


def main() -> None:
    blurred = Image.open(SOURCE).convert("RGB").filter(ImageFilter.GaussianBlur(BLUR))
    a = np.asarray(blurred).astype(np.float32) * (1 - SCRIM_OPACITY) + np.array(SCRIM) * SCRIM_OPACITY
    small = Image.fromarray(np.clip(a + 0.5, 0, 255).astype(np.uint8)).resize(SIZE, Image.Resampling.LANCZOS)
    small.save(OUT, optimize=True)
    px = np.asarray(small).astype(float)
    band = SIZE[1] * 15 // 100
    top, bottom = (px[:band].reshape(-1, 3).mean(0), px[-band:].reshape(-1, 3).mean(0))
    print(OUT, small.size, OUT.stat().st_size // 1024, "KiB")
    print("BackgroundStartColor=0x%02x%02x%02x" % tuple(int(round(v)) for v in top))
    print("BackgroundEndColor=0x%02x%02x%02x" % tuple(int(round(v)) for v in bottom))


if __name__ == "__main__":
    main()
