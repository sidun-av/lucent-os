"""Every page loads in the real QML engine, offscreen, without a single QML
warning, in English and in Russian, light and dark.

Skipped when PySide6 is not installed (the backend tests don't need it)."""

import os

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from demo import laptop_runner  # noqa: E402
from PySide6.QtCore import QtMsgType, qInstallMessageHandler  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402

from lucent_settings import app, tasks  # noqa: E402

PAGES = app.PAGES


@pytest.fixture(scope="module")
def qapp():
    return QGuiApplication.instance() or QGuiApplication([])


@pytest.fixture
def warnings():
    found = []

    def handler(kind, ctx, msg):
        if kind in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg) and "qml" in (
                (ctx.file or "") + msg).lower():
            found.append(msg)
    qInstallMessageHandler(handler)
    yield found
    qInstallMessageHandler(None)


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_every_page_loads_without_qml_warnings(qapp, warnings, theme, monkeypatch, tmp_path):
    monkeypatch.setenv("LUCENT_SETTINGS_THEME", theme)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    monkeypatch.setattr(tasks, "INLINE", True)
    engine, system, secs = app.create_engine(qapp, laptop_runner(), "appearance")
    win = engine.rootObjects()[0]
    for page in PAGES:
        win.setProperty("page", page)
        for _ in range(5):
            qapp.processEvents()
    assert warnings == []
    assert secs["network"].s["current"] == "Home_5G"
    assert secs["updates"].s["state"] == "staged"
    assert secs["winapps"].s["apps"][0]["name"] == "Notepad++"
    assert warnings == []
    win.close()
    engine.deleteLater()
    qapp.processEvents()
