"""The store notices apps installed or removed behind its back: the first-boot
setup (lucent-flatpak-setup) installs the default apps after login on the
online path, and a store opened meanwhile must not keep offering "Install"
for them."""

import os
import time

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402

from lucent_store import backend, catalog  # noqa: E402


def test_watched_dirs_are_the_installations_and_their_exports(tmp_path):
    system, user = tmp_path / "system", tmp_path / "user"
    (system / "app").mkdir(parents=True)
    (system / "exports/share/applications").mkdir(parents=True)
    paths = backend.watch_paths([system, user])
    assert str(system) in paths and str(system / "app") in paths
    assert str(system / "exports/share/applications") in paths
    assert not any(p.startswith(str(user)) for p in paths)      # missing dirs are skipped


def spin_until(cond, timeout=5.0):
    end = time.time() + timeout
    while time.time() < end:
        QCoreApplication.processEvents()
        if cond():
            return True
        time.sleep(0.02)
    return False


def test_an_app_appearing_on_disk_refreshes_the_installed_list(tmp_path, monkeypatch):
    QGuiApplication.instance() or QGuiApplication([])   # the GUI tests share it
    system = tmp_path / "flatpak"
    (system / "exports/share/applications").mkdir(parents=True)
    monkeypatch.setattr(backend, "INSTALL_DIRS", [system])
    monkeypatch.setattr(backend, "WATCH_DELAY_MS", 50)
    b = backend.FlatpakBackend(catalog.load())
    calls = []
    monkeypatch.setattr(b, "refresh_installed", lambda: calls.append(1))
    b.watch_installations()
    (system / "exports/share/applications/org.kde.okular.desktop").write_text("[Desktop Entry]\n")
    assert spin_until(lambda: calls)
    (system / "app").mkdir()                       # a new watched dir is picked up as well
    assert spin_until(lambda: len(calls) >= 2)
