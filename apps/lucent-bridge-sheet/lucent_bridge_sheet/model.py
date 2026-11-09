"""What the launch sheet shows, as a pure function of lucent-bridge's events.

lucent-bridge (`src/progress.rs`, protocol version 1) writes one JSON object
per line: `start`, `step` (prepare / components / launch), `progress`,
`launched`, `installed`, `error`, `cancelled`, `exit`. Error texts arrive
already translated; everything else is worded here.
"""

from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass, field

from .i18n import _, language

PROTOCOL = 1


@dataclass(frozen=True)
class State:
    # waiting | preparing | components | launching | launched | error | cancelling | done
    phase: str = "waiting"
    name: str = ""
    file: str = ""
    size: int = 0
    icon: str | None = None
    installer: bool = False
    program_arch: str = "x86-64"
    host_arch: str = "x86-64"
    translation: bool = False
    fraction: float = 0.0
    detail: str = ""
    error: dict = field(default_factory=dict)
    exit_code: int | None = None
    started: bool = False


def parse_line(line: str) -> dict | None:
    """One protocol line, or None (blank, not JSON, other version)."""
    try:
        event = json.loads(line)
    except ValueError:
        return None
    if not isinstance(event, dict) or event.get("v") != PROTOCOL or "event" not in event:
        return None
    return event


def apply(s: State, e: dict) -> State:
    kind = e.get("event")
    r = dataclasses.replace
    if kind == "start":
        return r(s, started=True, name=str(e.get("name", "")), file=str(e.get("file", "")),
                 size=int(e.get("size") or 0), icon=e.get("icon") or None,
                 installer=bool(e.get("installer")),
                 program_arch=str(e.get("program_arch") or "x86-64"),
                 host_arch=str(e.get("host_arch") or "x86-64"),
                 translation=bool(e.get("translation")))
    if s.phase in ("error", "cancelling"):
        # The user is reading an explanation or has cancelled: hold it.
        return r(s, exit_code=e.get("code", s.exit_code)) if kind == "exit" else s
    if kind == "step":
        phase = {"prepare": "preparing", "components": "components", "launch": "launching"}.get(
            e.get("step"), s.phase)
        return r(s, phase=phase, detail=str(e.get("detail") or ""))
    if kind == "progress":
        return r(s, fraction=max(s.fraction, min(1.0, float(e.get("fraction") or 0))))
    if kind == "launched":
        return r(s, phase="launched", fraction=1.0)
    if kind == "error":
        return r(s, phase="error", error={
            "kind": e.get("kind", "failed"), "title": e.get("title") or _("Can't start this program"),
            "message": e.get("message", ""), "hints": list(e.get("hints") or []),
            "can_run_anyway": bool(e.get("can_run_anyway"))})
    if kind == "cancelled":
        return r(s, phase="done")
    if kind == "exit":
        return r(s, phase="done" if s.phase != "launched" else s.phase, exit_code=e.get("code"))
    return s


def cancel(s: State) -> State:
    return dataclasses.replace(s, phase="cancelling")


def closes_by_itself(s: State) -> bool:
    """Once the program is starting (or it's all over) the sheet goes away;
    an explanation stays until the user closes it."""
    return s.phase in ("launched", "done")


def title(s: State) -> str:
    if s.phase == "error":
        return s.error["title"]
    return _("Preparing Windows program")


def human_size(n: int) -> str:
    if n < 1024:
        return _("{} bytes").format(n)
    units = [_("{} KB"), _("{} MB"), _("{} GB")]
    value, unit = n / 1024, 0
    while value >= 1024 and unit < len(units) - 1:
        value, unit = value / 1024, unit + 1
    number = f"{value:.0f}" if unit == 0 else f"{value:.1f}"
    if language() == "ru":
        number = number.replace(".", ",")
    return units[unit].format(number)


def file_line(s: State) -> str:
    return f"{s.file} · {human_size(s.size)}" if s.file else ""


def mode_line(s: State) -> str:
    arch = _("Windows Installer") if s.program_arch == "MSI" else s.program_arch
    if s.translation:
        return f"{arch} → ARM · " + _("instruction translation")
    return f"{arch} · " + _("direct execution")


def status_line(s: State) -> str:
    if s.phase == "cancelling":
        return _("Cancelling…")
    if s.phase == "components":
        return _("Installing components: {}").format(s.detail)
    if s.phase in ("launching", "launched", "done"):
        return _("Starting {}…").format(s.name)
    if s.translation:
        return _("The first launch takes a little longer — after that it's fast")
    return _("Getting everything ready to launch — only needed the first time")


def percent(s: State) -> str:
    return _("{}%").format(round(s.fraction * 100))


def buttons(s: State) -> list[tuple[str, str, bool]]:
    """(action, label, is the primary / default button), left to right."""
    if s.phase == "error":
        out = [("run-anyway", _("Run anyway"), False)] if s.error.get("can_run_anyway") else []
        return out + [("close", _("Close"), True)]
    if s.phase in ("waiting", "preparing", "components", "launching"):
        return [("cancel", _("Cancel"), False)]
    return []
