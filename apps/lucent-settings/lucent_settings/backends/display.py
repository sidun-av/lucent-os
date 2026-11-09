"""Screens: resolution and scale through kscreen-doctor (KScreen, the same
backend as Plasma's display settings), night light through KWin.

Night light: KWin reads `[NightColor] Active` from kwinrc and follows the
change as soon as kwriteconfig6 --notify announces it; its state is read
back from KWin's D-Bus object.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field

from .. import dbus, kconfig
from ..run import Result, Runner

SCALES = [1.0, 1.25, 1.5, 1.75, 2.0]


def scale_label(scale: float) -> str:
    return f"{round(scale * 100)}%"


def recommended_scale(width: int, height: int, width_mm: int) -> float:
    """Pick the scale that makes 1 logical px about 1/96 inch at desk distance
    (what Plasma's own heuristics aim at), rounded to the offered steps."""
    if width_mm <= 0:
        return 1.0
    dpi = width / (width_mm / 25.4)
    raw = dpi / 110 if width_mm < 400 else dpi / 120
    best = min(SCALES, key=lambda s: abs(s - raw))
    return max(1.0, best)


@dataclass
class Mode:
    id: str
    width: int
    height: int
    refresh: float


@dataclass
class Output:
    name: str
    width: int
    height: int
    scale: float
    current_mode: str
    width_mm: int = 0
    modes: list[Mode] = field(default_factory=list)

    @property
    def current_size(self) -> tuple[int, int]:
        return self.width, self.height


class Display:
    def __init__(self, runner: Runner):
        self.r = runner

    def outputs(self) -> list[Output]:
        res = self.r.run(["kscreen-doctor", "-j"])
        try:
            data = json.loads(res.out)
        except json.JSONDecodeError:
            return []
        outs = []
        for o in data.get("outputs", []):
            if not o.get("connected") or not o.get("enabled", True):
                continue
            current = str(o.get("currentModeId", ""))
            modes: dict[tuple[int, int], Mode] = {}
            cur_size = None
            for m in o.get("modes", []):
                size = (int(m["size"]["width"]), int(m["size"]["height"]))
                mode = Mode(str(m["id"]), size[0], size[1], float(m.get("refreshRate", 0)))
                if mode.id == current:
                    cur_size = size
                old = modes.get(size)
                if old is None or mode.refresh > old.refresh + 0.5:
                    modes[size] = mode
            w, h = cur_size or (o.get("size", {}).get("width", 0), o.get("size", {}).get("height", 0))
            outs.append(Output(name=o["name"], width=int(w), height=int(h), scale=float(o.get("scale", 1)),
                               current_mode=current, width_mm=int(o.get("sizeMM", {}).get("width", 0)),
                               modes=sorted(modes.values(), key=lambda m: (-m.width * m.height, -m.width))))
        return outs

    def set_mode(self, output: str, mode_id: str) -> Result:
        return self.r.run(["kscreen-doctor", f"output.{output}.mode.{mode_id}"])

    def set_scale(self, output: str, scale: float) -> Result:
        text = f"{scale:.2f}".rstrip("0").rstrip(".") if not math.isclose(scale, round(scale)) else str(round(scale))
        return self.r.run(["kscreen-doctor", f"output.{output}.scale.{text}"])

    def night_light(self) -> tuple[bool, bool]:
        """(enabled, available)"""
        res = self.r.run(dbus.get_property(dbus.SESSION, "org.kde.KWin", "/org/kde/KWin/NightLight",
                                           "org.kde.KWin.NightLight", "enabled", "available"))
        vals = dbus.values(res.out) if res.ok else []
        if len(vals) == 2:
            return bool(vals[0]), bool(vals[1])
        return kconfig.read("kwinrc", "NightColor", "Active", "false") == "true", False

    def set_night_light(self, on: bool) -> Result:
        return kconfig.write(self.r, "kwinrc", "NightColor", "Active", on)
