#!/usr/bin/env python3
"""Render the Lucent logo (docs/mockups/lucent.js `logo()`) as the Plymouth
boot splash watermark: 112 px, transparent PNG. Needs playwright."""
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
JS = (ROOT / "docs/mockups/lucent.js").read_text()
OUT = ROOT / "system_files/usr/share/plymouth/themes/lucent/watermark.png"

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 112, "height": 112})
    pg.set_content(f"<html><body style='margin:0;background:transparent'><div id=l></div><script>{JS}</script>"
                   "<script>document.getElementById('l').innerHTML = Lucent.logo(112)</script></body></html>")
    pg.locator("svg").screenshot(path=str(OUT), omit_background=True)
    b.close()
print(OUT)
