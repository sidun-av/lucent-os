"""The QML UI against the fake backend, offscreen: every page loads without
QML errors, and install / remove / update go through the backend.

Skipped when PySide6 is not installed (the core tests do not need it)."""

import os
import time

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ["LUCENT_STORE_THEME"] = "light"

from PySide6.QtCore import QtMsgType, qInstallMessageHandler  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtQuickControls2 import QQuickStyle  # noqa: E402

from lucent_store import catalog  # noqa: E402
from lucent_store.app import create_engine  # noqa: E402
from lucent_store.fake import FakeBackend  # noqa: E402
from lucent_store.screenshots import ScreenshotCache  # noqa: E402
from lucent_store.store import Store  # noqa: E402

PAGES = ["home", "nextgen", "category:office", "category:games", "category:windows", "installed",
         "updates", "search:photo", "search:zzzz", "app:org.gimp.GIMP", "app:ai.storyteller.wordcraft",
         "app:org.kde.ark"]


def png() -> bytes:
    from PySide6.QtCore import QBuffer, QByteArray, QIODevice
    from PySide6.QtGui import QImage
    data = QByteArray()
    buf = QBuffer(data)
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    img = QImage(16, 9, QImage.Format.Format_RGB32)
    img.fill(0x3B6EF5)
    img.save(buf, "PNG")
    return bytes(data)


def wait_until(cond, timeout=10.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        QGuiApplication.processEvents()
        if cond():
            return
        time.sleep(0.01)
    raise AssertionError("timeout")


def spin(seconds=0.15):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        QGuiApplication.processEvents()


@pytest.fixture(scope="module")
def qapp():
    QQuickStyle.setStyle("Basic")
    return QGuiApplication.instance() or QGuiApplication([])


@pytest.fixture
def ui(qapp, appstream_file, tmp_path):
    problems = []

    def handler(kind, _ctx, msg):
        if kind in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg) and "qml" in msg.lower():
            problems.append(msg)
    qInstallMessageHandler(handler)
    cat = catalog.load()
    backend = FakeBackend(cat, appstream_path=appstream_file, speed_ms=5)
    store = Store(cat, backend, screenshots=ScreenshotCache(tmp_path, fetch=lambda u: png(), threaded=False))
    engine = create_engine(store, backend, "home", "1600x1000")
    backend.start()
    win = engine.rootObjects()[0]
    spin()
    yield win, store, backend, problems
    win.close()
    qInstallMessageHandler(None)
    spin(0.05)


def test_every_page_loads_without_qml_errors(ui):
    win, _store, _backend, problems = ui
    for page in PAGES:
        if page.startswith("search:"):
            win.setProperty("query", page[7:])
            page = "search"
        win.setProperty("page", page)
        spin()
    assert problems == []


def test_home_cards_and_states(ui):
    _win, store, _backend, _problems = ui
    cards = {c["windows"]: c for c in store.home(0)}
    assert cards["Microsoft Word"]["state"] == "installed"
    assert cards["Adobe Photoshop"]["state"] == "installed"
    assert cards["7-Zip"]["state"] == "system"
    # In the test AppStream file only GIMP, Okular and Krita exist; apps
    # missing on this architecture are hidden, so most cards drop out.
    assert "Adobe Premiere" not in cards


def test_install_remove_update_go_through_the_backend(ui):
    _win, store, backend, _problems = ui
    store.install(["com.example.Photon"], "Photon")
    store.remove("org.kde.okular")
    assert backend.job_for("com.example.Photon").running
    assert store.details("org.kde.okular", 0)["state"] == "queued"
    wait_until(lambda: not backend.jobs)
    assert "com.example.Photon" in backend.installed and "org.kde.okular" not in backend.installed
    assert store.updateCount == 2
    store.updateAll()
    wait_until(lambda: not backend.jobs)
    assert store.updateCount == 0


def test_beta_installs_the_pinned_artcraft_version(ui):
    _win, store, backend, _problems = ui
    apps = {a["key"]: a for a in store.nextgen(0)}
    assert list(apps) == ["vectorcraft", "wordcraft", "gridcraft", "deckcraft"]
    store.install(["ai.storyteller.wordcraft"], "WordCraft")
    job = backend.job_for("ai.storyteller.wordcraft")
    assert job.nextgen and job.cmd[:3] == ["lucent-nextgen", "install", "--yes"] and "--sha256" in job.cmd
    wait_until(lambda: not backend.jobs)
    assert backend.installed["ai.storyteller.wordcraft"].installation == "user"


def test_search_and_details(ui):
    _win, store, backend, _problems = ui
    assert [a["id"] for a in store.search("photoshop", 0)][0] == "org.gimp.GIMP"
    d = store.details("org.gimp.GIMP", 0)
    assert d["verified"] and d["license"] == "Free and open source" and d["licenseCode"].startswith("GPL")
    wait_until(lambda: "org.gimp.GIMP" in backend.metadata)
    d = store.details("org.gimp.GIMP", 0)
    assert "Can read and change all your files" in [p["text"] for p in d["permissions"]]


def test_system_updates_link(ui):
    _win, store, backend, _problems = ui
    store.openSystemUpdates()
    assert backend.opened_updates == 1


def test_one_row_header_needs_the_chrome_module(qapp, tmp_path, monkeypatch):
    """Frameless (one top row) only when org.lucent.chrome is installed
    (build_files/lucent-chrome); LUCENT_CHROME=0 keeps KWin's title bar."""
    from PySide6.QtQml import QQmlApplicationEngine

    from lucent_store.app import chrome_available
    engine = QQmlApplicationEngine()
    monkeypatch.delenv("LUCENT_CHROME", raising=False)
    module = tmp_path / "org/lucent/chrome"
    module.mkdir(parents=True)
    (module / "qmldir").write_text("module org.lucent.chrome\n")
    engine.addImportPath(str(tmp_path))
    assert chrome_available(engine)
    monkeypatch.setenv("LUCENT_CHROME", "0")
    assert not chrome_available(engine)
