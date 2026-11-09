#!/usr/bin/env python3
"""Contact sheets of the Lucent icon theme as Plasma draws it (QtSvg):

    python3 design/preview-icons.py OUT_DIR

folders.png  the Pebble Drift folders (Lucent, Lucent-Dark) at 16-128 px on
             the window surface of each mode;
tiles.png    every app tile in the theme on the light and dark taskbar well,
             at the taskbar's 38 px and the launcher's 96 px.
Needs PySide6 (QtSvg). Colours come from pebble-drift.css.
"""
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "migration-wizard"))

from PySide6.QtCore import QRectF, Qt  # noqa: E402
from PySide6.QtGui import QColor, QFont, QGuiApplication, QImage, QPainter  # noqa: E402
from PySide6.QtSvg import QSvgRenderer  # noqa: E402

from lucent_migrate import tokens  # noqa: E402

ICONS = ROOT / "system_files/usr/share/icons"
FOLDERS = ["folder", "folder-documents", "folder-download", "folder-pictures", "folder-music",
           "folder-videos", "user-desktop", "user-home"]
SIZES = [16, 22, 32, 48, 64, 128]


def solid(token: str) -> QColor:
    return QColor(token)


def draw_svg(p: QPainter, path: Path, x: float, y: float, size: int) -> None:
    r = QSvgRenderer(str(path))
    assert r.isValid(), path
    r.render(p, QRectF(x, y, size, size))


def folders(out: Path) -> None:
    pad, col = 24, max(SIZES) + 24
    w = pad * 2 + 150 + col * len(FOLDERS)
    row_h = [s + 30 for s in SIZES]
    h = 60 + 2 * (sum(row_h) + 50)
    img = QImage(w, h, QImage.Format.Format_ARGB32)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    y = 0
    for theme, dark in (("Lucent", False), ("Lucent-Dark", True)):
        t = tokens.load(dark)
        block = sum(row_h) + 50
        p.fillRect(0, y, w, block + (60 if not dark else 60), solid(t["surface-window-solid"]))
        p.setPen(solid(t["text-secondary"]))
        p.setFont(QFont("Helvetica", 13))
        p.drawText(pad, y + 30, f"{theme}  (/usr/share/icons/{theme}/scalable/places), QtSvg")
        yy = y + 50
        for s, rh in zip(SIZES, row_h):
            p.drawText(pad, yy + s // 2 + 5, f"{s} px")
            for i, name in enumerate(FOLDERS):
                draw_svg(p, ICONS / theme / "scalable/places" / f"{name}.svg",
                         pad + 150 + i * col + (col - s) / 2, yy, s)
            yy += rh
        for i, name in enumerate(FOLDERS):
            p.drawText(pad + 150 + i * col, yy + 4, col - 8, 30, Qt.AlignmentFlag.AlignHCenter, name.split("-")[-1])
        y += block + 60
    p.end()
    img.save(str(out / "folders.png"))
    print(out / "folders.png")


def tiles(out: Path) -> None:
    apps = sorted(f for f in (ICONS / "Lucent/scalable/apps").iterdir() if not f.is_symlink())
    pad, col = 20, 120
    per_row = 9
    rows = (len(apps) + per_row - 1) // per_row
    block = 60 + rows * 170
    w, h = pad * 2 + per_row * col, 2 * block
    img = QImage(w, h, QImage.Format.Format_ARGB32)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    for k, dark in enumerate((False, True)):
        t = tokens.load(dark)
        y0 = k * block
        p.fillRect(0, y0, w, block, solid(t["surface-window-solid"]))
        p.setPen(solid(t["text-secondary"]))
        p.setFont(QFont("Helvetica", 12))
        p.drawText(pad, y0 + 30, f"App tiles on the {'dark' if dark else 'light'} window surface: "
                                 "96 px (launcher), 38 px (taskbar)")
        for i, f in enumerate(apps):
            x = pad + (i % per_row) * col
            y = y0 + 50 + (i // per_row) * 170
            draw_svg(p, f, x + (col - 96) / 2, y, 96)
            draw_svg(p, f, x + (col - 38) / 2, y + 104, 38)
            p.drawText(int(x), int(y + 146), col, 20, Qt.AlignmentFlag.AlignHCenter,
                       f.stem.split(".")[-1][:16])
    p.end()
    img.save(str(out / "tiles.png"))
    print(out / "tiles.png")


if __name__ == "__main__":
    app = QGuiApplication(sys.argv[:1])
    target = Path(sys.argv[1])
    target.mkdir(parents=True, exist_ok=True)
    folders(target)
    tiles(target)
