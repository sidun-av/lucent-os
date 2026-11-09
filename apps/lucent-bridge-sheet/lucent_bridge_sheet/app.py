"""lucent-bridge-sheet: the calm "Preparing Windows program" sheet.

lucent-bridge starts it when there is something to show (a first launch, a
component install, an explanation) and writes its progress to our stdin as
JSON lines (lucent-bridge `src/progress.rs`, protocol 1). We answer through
the exit status: 0 closed / done, 2 Cancel, 3 "Run anyway".

  lucent-bridge-sheet                      read events from stdin
  lucent-bridge-sheet --preview NAME --out FILE.png [--theme light|dark]
                                           render a sample (docs, tests, build)
"""

from __future__ import annotations

import argparse
import os
import sys
import time

from PySide6.QtCore import QSocketNotifier, QTimer
from PySide6.QtWidgets import QApplication

from . import i18n, look as looks, model
from .sheet import Sheet

EXIT_DONE, EXIT_CANCEL, EXIT_RUN_ANYWAY = 0, 2, 3
MIN_VISIBLE = 1.2       # s: never just flash
AFTER_LAUNCH = 2.5      # s: "Starting …" stays until the program's window usually is there

SAMPLES = {
    "preparing": [
        {"v": 1, "event": "start", "name": "Notepad++ Installer", "file": "npp.8.9.9.Installer.x64.exe",
         "size": 7028968, "icon": None, "installer": True, "program_arch": "x86-64",
         "host_arch": "x86-64", "translation": False, "first_launch": True},
        {"v": 1, "event": "step", "step": "prepare"},
        {"v": 1, "event": "progress", "fraction": 0.62},
    ],
    "preparing-arm": [
        {"v": 1, "event": "start", "name": "Notepad++ Installer", "file": "npp.8.9.9.Installer.x64.exe",
         "size": 7028968, "icon": None, "installer": True, "program_arch": "x86-64",
         "host_arch": "ARM64", "translation": True, "first_launch": True},
        {"v": 1, "event": "step", "step": "prepare"},
        {"v": 1, "event": "progress", "fraction": 0.34},
    ],
    "hibernated": [
        {"v": 1, "event": "start", "name": "Photo Organizer", "file": "PhotoOrganizer.exe", "size": 48213504,
         "icon": None, "installer": False, "program_arch": "x86-64", "host_arch": "x86-64",
         "translation": False, "first_launch": True},
        {"v": 1, "event": "error", "kind": "hibernated", "title": "Windows didn't shut down completely",
         "message": "Photo Organizer is on the disk of a Windows that didn't shut down completely (Fast "
                    "Startup or hibernation). Lucent keeps that disk read-only so nothing on it is damaged, "
                    "so programs started from there can't save anything next to themselves.",
         "hints": ["To use the disk fully, start Windows and shut it down while holding Shift.",
                   "Or install the program in Lucent: open its installer from your Downloads folder."],
         "can_run_anyway": True},
    ],
    "anticheat": [
        {"v": 1, "event": "start", "name": "VALORANT", "file": "VALORANT.exe", "size": 3_300_000,
         "icon": None, "installer": False, "program_arch": "x86-64", "host_arch": "x86-64",
         "translation": False, "first_launch": True},
        {"v": 1, "event": "error", "kind": "blocked", "title": "VALORANT won't work",
         "message": "Riot Vanguard is a kernel-mode anti-cheat driver. Wine cannot load Windows kernel "
                    "drivers, so this game cannot run on Linux at all.",
         "hints": [], "can_run_anyway": False},
    ],
}


class Controller:
    """Feeds events to the sheet, and decides when it goes away."""

    def __init__(self, app: QApplication, sheet: Sheet):
        self.app, self.sheet = app, sheet
        self.state = model.State()
        self.shown_at: float | None = None
        self.closing = False
        self.buffer = b""
        sheet.action.connect(self.on_action)

    def feed(self, data: bytes) -> None:
        self.buffer += data
        *lines, self.buffer = self.buffer.split(b"\n")
        for line in lines:
            event = model.parse_line(line.decode("utf-8", "replace"))
            if event is not None:
                self.on_event(event)

    def on_event(self, event: dict) -> None:
        self.state = model.apply(self.state, event)
        self.sheet.set_state(self.state)
        if self.shown_at is None and self.state.phase != "waiting" or event.get("event") == "error":
            self.show()
        if model.closes_by_itself(self.state):
            self.finish(EXIT_DONE, AFTER_LAUNCH if self.state.phase == "launched" else 0.3)

    def on_eof(self) -> None:
        if self.state.phase == "error":
            self.show()          # the user reads it and closes it
        elif self.state.phase == "cancelling":
            self.finish(EXIT_CANCEL, 0)
        else:
            self.finish(EXIT_DONE, 0.3)

    def show(self) -> None:
        if self.shown_at is None:
            self.shown_at = time.monotonic()
            self.sheet.show()
            self.sheet.raise_()
            self.sheet.activateWindow()

    def on_action(self, action: str) -> None:
        if action == "cancel":
            self.state = model.cancel(self.state)
            self.sheet.set_state(self.state)
            self.finish(EXIT_CANCEL, 0, now=True)
        elif action == "run-anyway":
            self.finish(EXIT_RUN_ANYWAY, 0, now=True)
        else:
            self.finish(EXIT_DONE, 0, now=True)

    def finish(self, code: int, delay: float, now: bool = False) -> None:
        if self.closing:
            return
        self.closing = True
        if not now and self.shown_at is not None:
            delay = max(delay, MIN_VISIBLE - (time.monotonic() - self.shown_at))
        QTimer.singleShot(int(max(0.0, delay) * 1000), lambda: self.app.exit(code))


def preview(args) -> int:
    if args.theme:
        os.environ["LUCENT_SHEET_THEME"] = args.theme
    # At Lucent's default text size (11 pt), whatever this machine's is.
    sheet = Sheet(looks.load(scale=1.0))
    state = model.State()
    for e in SAMPLES[args.preview]:
        state = model.apply(state, e)
    sheet.set_state(state)
    sheet.shown_fraction = state.fraction
    sheet.resize(sheet.sizeHint())
    ok = sheet.render_image().save(args.out)
    print(f"{args.preview} -> {args.out} ({sheet.width()}x{sheet.height()})")
    return 0 if ok else 1


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="lucent-bridge-sheet")
    parser.add_argument("--preview", choices=sorted(SAMPLES))
    parser.add_argument("--out")
    parser.add_argument("--theme", choices=["light", "dark"])
    parser.add_argument("--lang", help="UI language for --preview (e.g. ru)")
    args = parser.parse_args(argv[1:])
    if args.lang:
        i18n.setup([args.lang])
    app = QApplication(argv[:1])
    app.setApplicationName("Lucent Bridge")
    app.setDesktopFileName("lucent-bridge")
    app.setQuitOnLastWindowClosed(False)
    looks.load_fonts()
    if args.preview:
        if not args.out:
            parser.error("--preview needs --out")
        return preview(args)

    sheet = Sheet(looks.load())
    ctl = Controller(app, sheet)
    os.set_blocking(0, False)
    notifier = QSocketNotifier(0, QSocketNotifier.Type.Read)

    def readable() -> None:
        try:
            data = os.read(0, 65536)
        except BlockingIOError:
            return
        except OSError:
            data = b""
        if data:
            ctl.feed(data)
        else:
            notifier.setEnabled(False)
            ctl.on_eof()

    notifier.activated.connect(readable)
    # Alt+F4 on the sheet: the same as its Cancel / Close button.
    sheet.closeEvent = lambda e: (e.ignore(), ctl.on_action(
        "cancel" if any(a == "cancel" for a, _, _ in model.buttons(ctl.state)) else "close"))
    return app.exec()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
