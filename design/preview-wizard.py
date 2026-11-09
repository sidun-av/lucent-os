#!/usr/bin/env python3
"""Screenshots of the "Move from Windows" wizard, page by page, in a real
window (not Qt's offscreen platform) at scale 1, against a fake Windows disk.

    python3 design/preview-wizard.py OUT_DIR [--dark] [--lang ru]

Needs PySide6 and pytest (the fake disk reuses the tests' helpers). The
system palette is replaced by a plain light or dark one, the way Plasma's
Lucent Light / Lucent Dark would switch it, and the system font by Lucent's
default (11 pt), so the result doesn't depend on the desktop it runs on.
It captures the screen pixels under the window (QScreen.grabWindow), so the
window must be visible and on top; on macOS the terminal needs the Screen
Recording permission. The widget style underneath is Fusion, not Lucent's
Kvantum-based style: check the real thing in the VM.
"""
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "migration-wizard"), str(ROOT / "migration-wizard" / "tests")]

from PySide6.QtCore import QPoint, Qt  # noqa: E402
from PySide6.QtGui import QColor, QFont, QIcon, QPalette  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

import conftest  # noqa: E402  (the tests' fake-Windows helpers)
from lucent_migrate import app, copying, i18n, volumes, xdg  # noqa: E402
from lucent_migrate.volumes import Volume  # noqa: E402

GB = 1024 ** 3


def sparse(path: Path, size: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.truncate(size)


def fake_windows(base: Path) -> Path:
    root = base / "Windows disk"
    conftest.write(root / "Windows" / "System32" / "ntoskrnl.exe")
    anna = root / "Users" / "Anna"
    conftest.write(anna / "NTUSER.DAT")
    for i in range(212):
        sparse(anna / "Documents" / f"Document {i + 1}.docx", 16 * 1024 ** 2)
    for i in range(14):
        sparse(anna / "Desktop" / f"Note {i + 1}.txt", 90 * 1024 ** 2)
    for i in range(38):
        sparse(anna / "Downloads" / f"setup-{i + 1}.exe", 160 * 1024 ** 2)
    for i in range(431):
        sparse(anna / "Pictures" / "Camera" / f"IMG_{i + 1:04}.jpg", 42 * 1024 ** 2)
    for i in range(102):
        sparse(anna / "Music" / f"Track {i + 1}.mp3", 96 * 1024 ** 2)
    for i in range(6):
        sparse(anna / "Videos" / f"Holiday {i + 1}.mp4", 7 * GB)
    local = anna / "AppData" / "Local"
    conftest.write(local / "Microsoft" / "Edge" / "User Data" / "Default" / "Bookmarks",
                   json.dumps(conftest.CHROME_BOOKMARKS))
    conftest.write(local / "Google" / "Chrome" / "User Data" / "Default" / "Bookmarks",
                   json.dumps(conftest.CHROME_BOOKMARKS))
    ifaces = root / "ProgramData" / "Microsoft" / "Wlansvc" / "Profiles" / "Interfaces" / "{5E2A7A1B}"
    for i, (ssid, auth) in enumerate([("Home_5G", "WPA2PSK"), ("Cottage", "WPA2PSK"),
                                      ("Office guests", "open"), ("Office", "WPA2")]):
        conftest.write(ifaces / f"{{{i}}}.xml", conftest.wlan_profile(ssid, auth, with_key=auth != "open"))
    return root


def plain_palette(dark: bool) -> QPalette:
    pal = QPalette()
    roles = QPalette.ColorRole
    colours = ({roles.Window: "#1d1f2e", roles.WindowText: "#eef0fa", roles.Base: "#232536",
                roles.Text: "#eef0fa", roles.Button: "#2c2f44", roles.ButtonText: "#eef0fa",
                roles.Highlight: "#7088ff", roles.HighlightedText: "#0e1230"} if dark else
               {roles.Window: "#f2f3fa", roles.WindowText: "#171a2b", roles.Base: "#fdfdff",
                roles.Text: "#171a2b", roles.Button: "#f3f4fb", roles.ButtonText: "#171a2b",
                roles.Highlight: "#4257e8", roles.HighlightedText: "#ffffff"})
    for role, colour in colours.items():
        pal.setColor(role, QColor(colour))
    return pal


def settle(qapp, seconds=0.6):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        qapp.processEvents()
        time.sleep(0.02)


def shoot(qapp, wiz, path: Path) -> None:
    wiz.raise_()
    wiz.activateWindow()
    settle(qapp)
    top_left = wiz.mapToGlobal(QPoint(0, 0))
    screen = wiz.screen()
    shot = screen.grabWindow(0, top_left.x() - screen.geometry().x(), top_left.y() - screen.geometry().y(),
                             wiz.width(), wiz.height())
    if shot.isNull():
        shot = wiz.grab()
    shot.save(str(path))
    print(path, shot.width(), "x", shot.height(), "dpr", shot.devicePixelRatio())


def main() -> int:
    out = Path(sys.argv[1])
    dark = "--dark" in sys.argv[2:]
    lang = sys.argv[sys.argv.index("--lang") + 1] if "--lang" in sys.argv else "en"
    suffix = ("dark" if dark else "light") + ("" if lang == "en" else f"-{lang}")
    out.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="wizard-preview-"))
    if lang != "en":                                    # the image compiles po/*.po the same way
        i18n.compile_po(ROOT / f"migration-wizard/po/{lang}.po", tmp / f"locale/{lang}/LC_MESSAGES/{i18n.DOMAIN}.mo")
        i18n.setup([lang], localedir=tmp / "locale")
    root = fake_windows(tmp)
    home = tmp / "home"
    os.environ["XDG_CONFIG_HOME"] = str(home / ".config")
    volumes.mount_readonly = lambda v: str(root)
    xdg.target_dirs = lambda *a, **k: {k: Path("/home/anna") / n for k, n in xdg.DEFAULTS.items()}

    qapp = QApplication(sys.argv[:1])
    qapp.setStyle("Fusion")
    qapp.setPalette(plain_palette(dark))
    qapp.setFont(QFont("Inter", 11))
    QIcon.setThemeSearchPaths([str(ROOT / "system_files/usr/share/icons")] + QIcon.themeSearchPaths())
    QIcon.setThemeName("Lucent-Dark" if dark else "Lucent")

    wiz = app.MigrationWizard([Volume(path="/dev/nvme0n1p3", fstype="ntfs", size=476 * GB, uuid="U",
                                      label="Windows")])
    wiz.move(200, 120)
    wiz.show()
    shoot(qapp, wiz, out / f"wizard-1-welcome-{suffix}.png")
    wiz.next()
    shoot(qapp, wiz, out / f"wizard-2-account-{suffix}.png")
    wiz.next()
    settle(qapp, 1.5)                                   # folder sizes are measured in a thread
    tree = wiz.currentPage().tree
    tree.topLevelItem(tree.topLevelItemCount() - 1).setCheckState(0, Qt.CheckState.Unchecked)  # one box off
    shoot(qapp, wiz, out / f"wizard-3-folders-{suffix}.png")
    wiz.next()
    shoot(qapp, wiz, out / f"wizard-4-browsers-wifi-{suffix}.png")

    # Copying: show the page mid-way instead of copying the fake disk.
    app.run_in_thread = lambda owner, fn, on_done, on_progress=None: type("W", (), {"cancel": False})()
    wiz.next()
    page = wiz.currentPage()
    page._progress(620, 1000, "IMG_0268.jpg")
    shoot(qapp, wiz, out / f"wizard-5-copying-{suffix}.png")
    page._finished((copying.Result(copied=1203, skipped=4), ["Bookmarks were saved to “/home/anna/Documents/Bookmarks from Windows”.",
                             "Wi-Fi networks added: 2 of 2."]))
    shoot(qapp, wiz, out / f"wizard-6-done-{suffix}.png")
    wiz.close()
    shutil.rmtree(tmp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
