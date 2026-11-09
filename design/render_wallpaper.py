#!/usr/bin/env python3
"""Render the Lucent wallpaper ("Lucent Flow") from the mockups' own SVG.

Source of truth: `wallpaper()` in docs/mockups/lucent.js. This renders it in
headless Chromium at 4K (16:9 and 16:10), light and dark, adds +-1 LSB noise
so the soft gradients don't band, and writes JPEGs into the Plasma wallpaper
package. Run on a dev machine (needs `pip install playwright numpy pillow`);
the outputs are committed, the image build doesn't run this.
"""
import io
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
JS = (ROOT / "docs/mockups/lucent.js").read_text()
OUT = ROOT / "system_files/usr/share/wallpapers/Lucent/contents"
SIZES = [(3840, 2160), (3840, 2400)]

PAGE = """<!doctype html><html class="%s"><head><style>
html,body{margin:0;width:%dpx;height:%dpx;overflow:hidden}#wall{position:absolute;inset:0}
#wall svg{width:100%%;height:100%%;display:block}</style></head>
<body><div id="wall"></div><script>%s</script>
<script>document.getElementById('wall').innerHTML = Lucent.wallpaper();</script></body></html>"""


def main():
    rng = np.random.default_rng(7)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for dark, folder in ((False, "images"), (True, "images_dark")):
            (OUT / folder).mkdir(parents=True, exist_ok=True)
            for w, h in SIZES:
                # Lay out at the mockups' 2560-wide logical size, render at 1.5x.
                lw, lh = 2560, round(2560 * h / w)
                page = browser.new_page(viewport={"width": lw, "height": lh}, device_scale_factor=w / lw)
                page.set_content(PAGE % ("dark" if dark else "", lw, lh, JS))
                png = page.screenshot(type="png")
                page.close()
                img = np.asarray(Image.open(io.BytesIO(png)).convert("RGB")).astype(np.float32)
                img += rng.uniform(-1.0, 1.0, img.shape[:2])[..., None]
                img = Image.fromarray(np.clip(img + 0.5, 0, 255).astype(np.uint8))
                dest = OUT / folder / f"{w}x{h}.jpg"
                img.save(dest, quality=93, optimize=True, subsampling=0)
                print(dest, img.size, dest.stat().st_size // 1024, "KiB")
        browser.close()


if __name__ == "__main__":
    sys.exit(main())
