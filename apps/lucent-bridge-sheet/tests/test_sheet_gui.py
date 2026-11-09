"""The sheet window, offscreen: it renders in both themes, and the controller
answers lucent-bridge through the exit status (0 done, 2 Cancel, 3 Run
anyway) at the right moments."""

from __future__ import annotations

import json
import os

import pytest

pytest.importorskip("PySide6.QtWidgets")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from lucent_bridge_sheet import app as sheet_app, look as looks, model  # noqa: E402
from lucent_bridge_sheet.sheet import Sheet  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def lines(*events) -> bytes:
    return b"".join(json.dumps(e).encode() + b"\n" for e in events)


START, PREP = sheet_app.SAMPLES["preparing"][:2]


@pytest.mark.parametrize("dark", [False, True])
@pytest.mark.parametrize("sample", sorted(sheet_app.SAMPLES))
def test_renders(qapp, dark, sample):
    sheet = Sheet(looks.load(dark=dark, scale=1.0))
    state = model.State()
    for e in sheet_app.SAMPLES[sample]:
        state = model.apply(state, e)
    sheet.set_state(state)
    img = sheet.render_image()
    assert img.width() == 720 and img.height() > 400
    # The card is opaque in its middle and the corners outside it are clear.
    mid = img.pixelColor(img.width() // 2, 60)
    assert mid.alpha() == 255
    assert (mid.lightness() < 80) == dark
    assert img.pixelColor(2, 2).alpha() == 0
    labels = [b.text() for b in sheet.buttons]
    assert labels == [label for _, label, _ in model.buttons(state)]


def run_controller(qapp, data: bytes, eof: bool, action: str | None = None, timeout_ms: int = 6000) -> tuple[int, Sheet]:
    sheet = Sheet(looks.load(dark=False, scale=1.0))
    ctl = sheet_app.Controller(qapp, sheet)
    ctl.feed(data)
    if eof:
        ctl.on_eof()
    if action:
        QTimer.singleShot(50, lambda: sheet.action.emit(action))
    QTimer.singleShot(timeout_ms, lambda: qapp.exit(99))
    code = qapp.exec()
    sheet.hide()
    return code, sheet


def test_cancel_exits_2(qapp):
    code, sheet = run_controller(qapp, lines(START, PREP), eof=False, action="cancel")
    assert code == sheet_app.EXIT_CANCEL
    assert sheet.state.phase == "cancelling"


def test_launch_closes_by_itself(qapp):
    code, _ = run_controller(qapp, lines(START, PREP, {"v": 1, "event": "launched"}), eof=False)
    assert code == sheet_app.EXIT_DONE


def test_errors_stay_until_answered(qapp):
    err = sheet_app.SAMPLES["hibernated"]
    code, sheet = run_controller(qapp, lines(*err), eof=True, timeout_ms=2500)
    assert code == 99, "still open after the bridge stopped writing"
    assert sheet.windowTitle() == "Windows didn't shut down completely"
    code, _ = run_controller(qapp, lines(*err), eof=True, action="run-anyway")
    assert code == sheet_app.EXIT_RUN_ANYWAY
    code, _ = run_controller(qapp, lines(*err), eof=True, action="close")
    assert code == sheet_app.EXIT_DONE


def test_partial_lines_and_garbage(qapp):
    sheet = Sheet(looks.load(dark=False, scale=1.0))
    ctl = sheet_app.Controller(qapp, sheet)
    data = lines(START, PREP)
    ctl.feed(data[:17])
    ctl.feed(b"")
    ctl.feed(data[17:] + b"garbage\n" + b'{"v":1,"event":"progress","fraction":0.5}')
    assert ctl.state.phase == "preparing" and ctl.state.fraction == 0.0
    ctl.feed(b"\n")
    assert ctl.state.fraction == 0.5
