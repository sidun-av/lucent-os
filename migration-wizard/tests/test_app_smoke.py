"""End-to-end smoke test of the thin GUI, offscreen, against the fake tree.

Skipped when PySide6 is not installed (the core tests do not need it).
"""

import os
import time

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from lucent_migrate import app, volumes, xdg  # noqa: E402
from lucent_migrate.volumes import Volume  # noqa: E402


def wait_until(cond, timeout=10.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        QApplication.processEvents()
        if cond():
            return
        time.sleep(0.01)
    raise AssertionError("timeout")


def test_wizard_walkthrough(windows_root, tmp_path, monkeypatch):
    home = tmp_path / "home"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.setattr(volumes, "mount_readonly", lambda v: str(windows_root))
    monkeypatch.setattr(xdg, "target_dirs", lambda *a, **k: {k: home / n for k, n in xdg.DEFAULTS.items()})
    monkeypatch.setattr(app.subprocess, "run", lambda *a, **k: type("P", (), {"returncode": 0})())

    qapp = QApplication.instance() or QApplication([])
    wiz = app.MigrationWizard([Volume(path="/dev/sda3", fstype="ntfs", size=10**11, uuid="U", label="OS")])
    wiz.show()
    wiz.next()  # -> source
    assert wiz.currentPage().list.count() == 2
    assert "Диск C: (OS)" in wiz.currentPage().list.item(0).text()
    wiz.next()  # -> folders
    wait_until(lambda: "файлов" in wiz.currentPage().tree.topLevelItem(0).text(1))
    wiz.next()  # -> extras
    assert wiz.currentPage().browsers.count() == 4
    assert wiz.currentPage().wifi.count() == 3
    wiz.next()  # -> copy, then auto-advances to done
    wait_until(lambda: isinstance(wiz.currentPage(), app.DonePage))
    assert wiz.result.copied == 6 and not wiz.result.errors
    assert (home / "Documents" / "Проекты" / "план.xlsx").exists()
    exported = list((home / "Documents" / "Закладки из Windows").iterdir())
    assert len(exported) == 4
    assert len(wiz.networks) == 2
    assert (home / ".config" / "lucent" / "migration-done").exists()
    wiz.close()
    qapp.processEvents()
