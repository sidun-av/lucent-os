"""The sheet's state machine and wording, driven by lucent-bridge's events."""

from __future__ import annotations

from lucent_bridge_sheet import model
from lucent_bridge_sheet.model import State, apply, parse_line

START = {
    "v": 1, "event": "start", "name": "Notepad++ Installer",
    "file": "npp.8.9.9.Installer.x64.exe", "size": 7028968, "icon": None,
    "installer": True, "program_arch": "x86-64", "host_arch": "x86-64",
    "translation": False, "first_launch": True,
}


def run(*events) -> State:
    s = State()
    for e in events:
        s = apply(s, e)
    return s


def test_lines_are_parsed_and_unknown_versions_or_garbage_ignored():
    assert parse_line('{"v":1,"event":"launched"}\n') == {"v": 1, "event": "launched"}
    assert parse_line('{"v":2,"event":"launched"}') is None
    assert parse_line("not json") is None
    assert parse_line('["v", 1]') is None
    assert parse_line("") is None


def test_preparing_on_x86():
    s = run(START, {"v": 1, "event": "step", "step": "prepare"},
            {"v": 1, "event": "progress", "fraction": 0.62})
    assert s.phase == "preparing"
    assert model.title(s) == "Preparing Windows program"
    assert model.file_line(s) == "npp.8.9.9.Installer.x64.exe · 6.7 MB"
    assert model.mode_line(s) == "x86-64 · direct execution"
    assert model.status_line(s) == "Getting everything ready to launch — only needed the first time"
    assert model.percent(s) == "62%"
    assert model.buttons(s) == [("cancel", "Cancel", False)]


def test_preparing_on_arm_translates():
    s = run({**START, "host_arch": "ARM64", "translation": True},
            {"v": 1, "event": "step", "step": "prepare"})
    assert model.mode_line(s) == "x86-64 → ARM · instruction translation"
    assert model.status_line(s) == "The first launch takes a little longer — after that it's fast"


def test_components_launch_and_the_end():
    s = run(START, {"v": 1, "event": "step", "step": "components", "detail": "vcrun2019"})
    assert model.status_line(s) == "Installing components: vcrun2019"
    s = apply(s, {"v": 1, "event": "step", "step": "launch"})
    assert model.status_line(s) == "Starting Notepad++ Installer…"
    s = apply(s, {"v": 1, "event": "launched"})
    assert s.phase == "launched" and s.fraction == 1.0
    assert model.buttons(s) == []
    assert model.closes_by_itself(s)
    s = apply(s, {"v": 1, "event": "exit", "code": 0})
    assert s.exit_code == 0 and model.closes_by_itself(s)


def test_progress_never_goes_back():
    s = run(START, {"v": 1, "event": "progress", "fraction": 0.5},
            {"v": 1, "event": "progress", "fraction": 0.3})
    assert s.fraction == 0.5


def test_errors_wait_for_the_user():
    err = {"v": 1, "event": "error", "kind": "hibernated", "title": "Windows didn't shut down completely",
           "message": "Setup is on the disk of a Windows ...", "hints": ["Shut Windows down with Shift."],
           "can_run_anyway": True}
    s = run(START, err)
    assert s.phase == "error"
    assert model.title(s) == "Windows didn't shut down completely"
    assert not model.closes_by_itself(s)
    assert model.buttons(s) == [("run-anyway", "Run anyway", False), ("close", "Close", True)]
    blocked = {**err, "kind": "blocked", "can_run_anyway": False}
    assert model.buttons(run(START, blocked)) == [("close", "Close", True)]
    # Without a start event (the file couldn't even be opened).
    s = run({"v": 1, "event": "error", "kind": "open-failed", "title": "Can't open this file",
             "message": "not a Windows program", "hints": [], "can_run_anyway": False})
    assert s.phase == "error" and model.title(s) == "Can't open this file"


def test_cancel_and_cancelled():
    s = model.cancel(run(START, {"v": 1, "event": "step", "step": "prepare"}))
    assert s.phase == "cancelling"
    assert model.status_line(s) == "Cancelling…"
    assert model.buttons(s) == []
    s = run(START, {"v": 1, "event": "cancelled"})
    assert s.phase == "done" and model.closes_by_itself(s)


def test_sizes_and_architectures():
    assert model.human_size(900) == "900 bytes"
    assert model.human_size(48_000) == "47 KB"
    assert model.human_size(7_028_968) == "6.7 MB"  # binary units, as Explorer and Dolphin count
    assert model.human_size(1_500_000_000) == "1.4 GB"
    s = run({**START, "program_arch": "MSI"})
    assert model.mode_line(s) == "Windows Installer · direct execution"
    s = run({**START, "program_arch": "ARM64", "host_arch": "ARM64"})
    assert model.mode_line(s) == "ARM64 · direct execution"
