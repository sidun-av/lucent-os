"""Bluetooth through BlueZ's D-Bus API (org.bluez, system bus).

Pairing a device that needs a PIN or confirmation uses Plasma's own BlueZ
agent (bluedevil, always running in a Plasma session), so the familiar KDE
prompt appears; this module only issues the calls.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from .. import dbus
from ..run import Result, Runner

BLUEZ = "org.bluez"
ADAPTER = "org.bluez.Adapter1"
DEVICE = "org.bluez.Device1"

KINDS = {
    "audio-headphones": "headphones", "audio-headset": "headphones", "audio-card": "speaker",
    "input-mouse": "mouse", "input-keyboard": "keyboard", "input-gaming": "gamepad",
    "input-tablet": "tablet", "phone": "phone", "computer": "computer",
}


@dataclass
class Device:
    path: str
    address: str
    name: str
    paired: bool
    connected: bool
    kind: str = "other"
    battery: int | None = None
    rssi: int | None = None


@dataclass
class State:
    adapter: str | None = None
    powered: bool = False
    discovering: bool = False
    devices: list[Device] = field(default_factory=list)


class Bluetooth:
    def __init__(self, runner: Runner):
        self.r = runner

    def state(self) -> State:
        res = self.r.run(dbus.call(dbus.SYSTEM, BLUEZ, "/", "org.freedesktop.DBus.ObjectManager",
                                   "GetManagedObjects"), timeout=10)
        st = State()
        if not res.ok:
            return st
        try:
            objects = dbus.plain(dbus.values(res.out)[0][0])
        except (ValueError, IndexError, KeyError, json.JSONDecodeError):
            return st
        for path, ifaces in sorted(objects.items()):
            if ADAPTER in ifaces and st.adapter is None:
                a = ifaces[ADAPTER]
                st.adapter, st.powered, st.discovering = path, bool(a.get("Powered")), bool(a.get("Discovering"))
            if DEVICE in ifaces:
                d = ifaces[DEVICE]
                address = d.get("Address", "")
                name = d.get("Name") or d.get("Alias") or ""
                if not d.get("Paired") and (not name or name.replace("-", ":") == address):
                    continue  # nameless beacons: nothing a person could recognise
                battery = ifaces.get("org.bluez.Battery1", {}).get("Percentage")
                st.devices.append(Device(path=path, address=address, name=name or address,
                                         paired=bool(d.get("Paired")), connected=bool(d.get("Connected")),
                                         kind=KINDS.get(d.get("Icon", ""), "other"),
                                         battery=battery, rssi=d.get("RSSI")))
        st.devices.sort(key=lambda d: (not d.paired, not d.connected, -(d.rssi or -999), d.name.lower()))
        return st

    def set_powered(self, adapter: str, on: bool) -> Result:
        return self.r.run(dbus.set_property(dbus.SYSTEM, BLUEZ, adapter, ADAPTER, "Powered", "b", on))

    def discover(self, adapter: str, on: bool) -> Result:
        return self.r.run(dbus.call(dbus.SYSTEM, BLUEZ, adapter, ADAPTER,
                                    "StartDiscovery" if on else "StopDiscovery"))

    def pair(self, device: str) -> Result:
        res = self.r.run(dbus.call(dbus.SYSTEM, BLUEZ, device, DEVICE, "Pair", timeout=90), timeout=95)
        if not res.ok:
            return res
        self.r.run(dbus.set_property(dbus.SYSTEM, BLUEZ, device, DEVICE, "Trusted", "b", True))
        return self.connect(device)

    def connect(self, device: str) -> Result:
        return self.r.run(dbus.call(dbus.SYSTEM, BLUEZ, device, DEVICE, "Connect", timeout=30), timeout=35)

    def disconnect(self, device: str) -> Result:
        return self.r.run(dbus.call(dbus.SYSTEM, BLUEZ, device, DEVICE, "Disconnect"))

    def forget(self, adapter: str, device: str) -> Result:
        return self.r.run(dbus.call(dbus.SYSTEM, BLUEZ, adapter, ADAPTER, "RemoveDevice", "o", device))
