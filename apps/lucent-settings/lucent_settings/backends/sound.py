"""Sound through PipeWire: devices listed with `pactl -f json` (pipewire-pulse),
volume and mute set with WirePlumber's `wpctl` on the default device."""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from ..run import Result, Runner

TARGET = {"output": "@DEFAULT_AUDIO_SINK@", "input": "@DEFAULT_AUDIO_SOURCE@"}


@dataclass
class Device:
    name: str
    label: str
    volume: int
    muted: bool
    default: bool
    virtual: bool = False


@dataclass
class State:
    outputs: list[Device] = field(default_factory=list)
    inputs: list[Device] = field(default_factory=list)

    @property
    def output(self) -> Device | None:
        return next((d for d in self.outputs if d.default), self.outputs[0] if self.outputs else None)

    @property
    def input(self) -> Device | None:
        return next((d for d in self.inputs if d.default), self.inputs[0] if self.inputs else None)

    @property
    def no_hardware(self) -> bool:
        return all(d.virtual for d in self.outputs)


def _volume(entry: dict) -> int:
    chans = list((entry.get("volume") or {}).values())
    if not chans:
        return 0
    pct = [int(str(c.get("value_percent", "0")).rstrip("%") or 0) for c in chans]
    return round(sum(pct) / len(pct))


class Sound:
    def __init__(self, runner: Runner):
        self.r = runner

    def _list(self, what: str, default: str) -> list[Device]:
        res = self.r.run(["pactl", "-f", "json", "list", what])
        try:
            items = json.loads(res.out) if res.ok else []
        except json.JSONDecodeError:
            items = []
        out = []
        for e in items:
            props = e.get("properties", {})
            if props.get("device.class") == "monitor" or e.get("name", "").endswith(".monitor"):
                continue
            out.append(Device(name=e["name"], label=e.get("description") or e["name"], volume=_volume(e),
                              muted=bool(e.get("mute")), default=e["name"] == default,
                              virtual=props.get("node.virtual") == "true"))
        return out

    def state(self) -> State:
        sink = self.r.run(["pactl", "get-default-sink"]).out.strip()
        source = self.r.run(["pactl", "get-default-source"]).out.strip()
        return State(outputs=self._list("sinks", sink), inputs=self._list("sources", source))

    def set_volume(self, kind: str, percent: int) -> Result:
        percent = max(0, min(100, int(percent)))
        return self.r.run(["wpctl", "set-volume", TARGET[kind], f"{percent / 100:.2f}"])

    def set_muted(self, kind: str, muted: bool) -> Result:
        return self.r.run(["wpctl", "set-mute", TARGET[kind], "1" if muted else "0"])

    def set_default(self, kind: str, name: str) -> Result:
        return self.r.run(["pactl", "set-default-sink" if kind == "output" else "set-default-source", name])
