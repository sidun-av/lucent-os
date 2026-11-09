#!/usr/bin/env python3
"""Export the Lucent icon theme from the mockups' own drawings.

docs/mockups/lucent.js draws every app tile and the Lucent logo, and the
Pebble Drift mockups (docs/mockups/concepts-2026/pebble-drift/drift-shell.js)
draw the folders in the accent's indigo family, as SVG (original artwork of
this repo, Apache-2.0). This script evaluates those functions in headless
Chromium and writes them as a freedesktop icon theme that sits on top of
Papirus (Fedora's papirus-icon-theme, GPL-3.0), which supplies every icon
Lucent doesn't draw itself (build_files/design.sh points Papirus's own
folders at its indigo colour, so they match).

  system_files/usr/share/icons/Lucent       (light: Inherits Papirus-Light)
  system_files/usr/share/icons/Lucent-Dark  (dark:  Inherits Papirus-Dark;
                                              the same apps, folders in the
                                              dark --folder-* tokens)

Run: python3 design/gen_icons.py   (needs playwright)
     python3 design/gen_icons.py --lines   (only the line icons; no browser)
"""
import os
import re
import shutil
import sys
from pathlib import Path

import lucent_extra_icons as extra

ROOT = Path(__file__).resolve().parents[1]
JS = (ROOT / "docs/mockups/lucent.js").read_text()
DRIFT = ROOT / "docs/mockups/concepts-2026/pebble-drift"
OUT = ROOT / "system_files/usr/share/icons"
sys.path.insert(0, str(ROOT / "migration-wizard"))
from lucent_migrate import tokens  # noqa: E402  (the pebble-drift.css token reader)

# mockup tile -> icon names it replaces (desktop-file Icon= values, Flatpak
# app ids, and the generic freedesktop names).
APPS = {
    "files": ["org.kde.dolphin", "system-file-manager", "dolphin"],
    "firefox": ["org.mozilla.firefox", "firefox"],
    "docs": ["org.onlyoffice.desktopeditors", "onlyoffice-desktopeditors"],
    "okular": ["org.kde.okular", "okular"],
    "pdfarranger": ["com.github.jeromerobert.pdfarranger", "pdfarranger"],
    "gimp": ["org.gimp.GIMP", "gimp"],
    "krita": ["org.kde.krita", "krita"],
    "inkscape": ["org.inkscape.Inkscape", "inkscape"],
    "darktable": ["org.darktable.Darktable", "darktable"],
    "kdenlive": ["org.kde.kdenlive", "kdenlive"],
    "settings": ["systemsettings", "preferences-system", "org.kde.systemsettings"],
    "store": ["org.kde.discover", "plasmadiscover", "system-software-install"],
    "terminal": ["org.kde.konsole", "utilities-terminal", "konsole"],
    "migrate": ["lucent-migrate", "org.lucent.Migrate"],
}
# drift-shell.js folder(kind) -> icon names it replaces (Papirus's blue and
# indigo names too, for apps that ask for a colour by name)
PLACES = {
    "": ["folder", "inode-directory", "folder-blue", "folder-indigo"],
    "doc": ["folder-documents", "folder-blue-documents", "folder-indigo-documents"],
    "dl": ["folder-download", "folder-downloads", "folder-blue-download", "folder-indigo-download"],
    "img": ["folder-pictures", "folder-images", "folder-blue-pictures", "folder-indigo-pictures"],
    "music": ["folder-music", "folder-blue-music", "folder-indigo-music"],
    "video": ["folder-videos", "folder-video", "folder-blue-videos", "folder-indigo-videos"],
    "desk": ["user-desktop", "folder-desktop", "folder-blue-desktop", "folder-indigo-desktop"],
    "home": ["user-home", "folder-home", "folder-blue-home", "folder-indigo-home"],
}

INDEX = """[Icon Theme]
Name={name}
Comment=Lucent OS icons on top of {parent}
Inherits={parent},breeze{dark},hicolor
Example=folder
DisplayDepth=32
Directories=scalable/apps,scalable/places,scalable/status,scalable/actions

[scalable/apps]
Size=64
MinSize=16
MaxSize=512
Context=Applications
Type=Scalable

[scalable/places]
Size=64
MinSize=32
MaxSize=512
Context=Places
Type=Scalable

[scalable/status]
Size=24
MinSize=16
MaxSize=512
Context=Status
Type=Scalable

[scalable/actions]
Size=24
MinSize=16
MaxSize=512
Context=Actions
Type=Scalable
"""


def qtsvg_safe(svg):
    """QtSvg doesn't understand rgba() colours: split them into rgb + opacity."""
    def fix(m):
        attr, r, g, b, a = m.group(1), *m.group(2).split(",")
        return f'{attr}="rgb({r.strip()},{g.strip()},{b.strip()})" {attr}-opacity="{a.strip()}"'
    return re.sub(r'(fill|stroke)="rgba\(([^)]*)\)"', fix, svg)


def drift_folder(svg, tok):
    """drift-shell.js folder() as a standalone icon: its --folder-* CSS
    variables filled in from the light or dark tokens, and the glyph's nested
    <svg> (which repeats stroke-width, invalid XML for QtSvg) as a plain <g>."""
    svg = re.sub(r'style="(fill|stroke|stop-color):var\(--([\w-]+)\)"', lambda m: f'{m[1]}="{tok[m[2]]}"', svg)
    svg = svg.replace('<g style="color:var(--folder-glyph)"', "<g")

    def group(m):
        attrs = {}
        for name, value in re.findall(r'([\w-]+)="([^"]*)"', m[1]):
            attrs.setdefault(name, value)           # the first one wins, as in the browser
        for name in ("width", "height", "viewBox"):
            attrs.pop(name, None)
        body = " ".join(f'{k}="{v}"' for k, v in attrs.items())
        return f"<g {body}>{m[2]}</g>"
    svg = re.sub(r'<svg width="24" height="24"([^>]*)>(.*?)</svg>', group, svg, flags=re.S)
    svg = svg.replace("currentColor", tok["folder-glyph"])
    svg = re.sub(r">\s+<", "><", svg)
    assert "var(" not in svg and svg.count("<svg") == 1, svg
    return svg


def safe_area(svg, ratio=0.8):
    """Shrink a 64-unit app tile onto an 80 % grid (macOS-style safe area):
    the tile then reads at the mockups' size in the 48 px taskbar slot and
    the 128 px launcher grid, and sits evenly next to Papirus icons."""
    full = 60 / ratio                       # tile spans 2..62 in the mockups
    off = 32 - full / 2
    return svg.replace('viewBox="0 0 64 64"', f'viewBox="{off:g} {off:g} {full:g} {full:g}"', 1)


def write_lines(base):
    """Line icons for the tray and session actions (lucent_extra_icons.LINES)."""
    session = {"shutdown", "reboot", "sleep", "log-out", "lock", "users"}
    for sub in ("status", "actions"):
        d = base / f"scalable/{sub}"
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
    for key, (svg, names) in extra.LINES.items():
        d = base / "scalable" / ("actions" if key in session else "status")
        (d / f"{names[0]}.svg").write_text(svg + "\n")
        for alias in names[1:] + [n + "-symbolic" for n in names]:
            (d / f"{alias}.svg").symlink_to(f"{names[0]}.svg")
    # Dolphin sidebar glyphs (named in /usr/libexec/lucent/design-defaults)
    for name, svg in extra.sidebar_icons().items():
        (base / "scalable/status" / f"{name}.svg").write_text(svg + "\n")


def write_lines_dark(base, dark):
    """The same line icons in a light default colour for dark surfaces."""
    for sub in ("status", "actions"):
        src = base / "scalable" / sub
        out_dir = dark / "scalable" / sub
        if out_dir.exists():
            shutil.rmtree(out_dir)
        out_dir.mkdir()
        for f in sorted(src.iterdir()):
            out = out_dir / f.name
            if f.is_symlink():
                out.symlink_to(os.readlink(f))
            else:
                out.write_text(extra.recolor(f.read_text(), "#eef0f5").replace(extra.ACCENT, extra.ACCENT_DARK))


def write_places(d, folders, tok):
    d.mkdir(parents=True)
    for kind, names in PLACES.items():
        (d / f"{names[0]}.svg").write_text(drift_folder(folders[kind], tok) + "\n")
        for alias in names[1:]:
            (d / f"{alias}.svg").symlink_to(f"{names[0]}.svg")


def main():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.set_content(f"<html><body><script>{JS}</script></body></html>")
        apps = pg.evaluate("names => Object.fromEntries(names.map(n => [n, Lucent.APPS[n]()]))", list(APPS))
        logo = pg.evaluate("Lucent.logo(64)")
        pg.set_content(f"<html><body><script>{JS}</script>"
                       f"<script>{(DRIFT / 'drift-shell.js').read_text()}</script></body></html>")
        folders = pg.evaluate("kinds => Object.fromEntries(kinds.map(k => [k, LucentDrift.folder(k)]))", list(PLACES))
        b.close()
    light, dark_overrides = tokens.parse((DRIFT / "pebble-drift.css").read_text())
    folder_tokens = {"": tokens.resolve(light), "-Dark": tokens.resolve({**light, **dark_overrides})}

    base = OUT / "Lucent"
    if base.exists():
        shutil.rmtree(base)
    d = base / "scalable/apps"
    d.mkdir(parents=True)
    for key, names in APPS.items():
        svg = apps[key]
        if 'xmlns="' not in svg:
            svg = svg.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ', 1)
        (d / f"{names[0]}.svg").write_text(qtsvg_safe(safe_area(svg)) + "\n")
        for alias in names[1:]:
            (d / f"{alias}.svg").symlink_to(f"{names[0]}.svg")
    write_places(base / "scalable/places", folders, folder_tokens[""])
    # Tiles for the rest of the launcher's apps, and line icons for the tray
    # and session actions (design/lucent_extra_icons.py).
    for key, (svg, names) in extra.TILES.items():
        (base / f"scalable/apps/{names[0]}.svg").write_text(safe_area(svg) + "\n")
        for alias in names[1:]:
            (base / f"scalable/apps/{alias}.svg").symlink_to(f"{names[0]}.svg")
    write_lines(base)
    logo = logo.replace(' width="64" height="64"', "")
    (base / "scalable/apps/lucent-start.svg").write_text(logo + "\n")
    for alias in ("start-here", "start-here-kde", "start-here-kde-plasma"):
        (base / f"scalable/apps/{alias}.svg").symlink_to("lucent-start.svg")
    (base / "index.theme").write_text(INDEX.format(name="Lucent", parent="Papirus-Light", dark=""))

    dark = OUT / "Lucent-Dark"
    if dark.exists():
        shutil.rmtree(dark)
    dark.mkdir()
    (dark / "scalable").mkdir()
    (dark / "scalable/apps").symlink_to("../../Lucent/scalable/apps")
    write_places(dark / "scalable/places", folders, folder_tokens["-Dark"])
    write_lines_dark(base, dark)
    (dark / "index.theme").write_text(INDEX.format(name="Lucent Dark", parent="Papirus-Dark", dark="-dark"))
    print("wrote", base, dark)


if __name__ == "__main__":
    import sys
    if "--lines" in sys.argv[1:]:
        write_lines(OUT / "Lucent")
        write_lines_dark(OUT / "Lucent", OUT / "Lucent-Dark")
        print("wrote line icons")
    else:
        main()
