"""Wi-Fi and wired network, through NetworkManager's own client (nmcli).

nmcli is NetworkManager's supported command-line front end to the same
D-Bus API; its terse mode (-t) is stable and documented for scripts. A
Wi-Fi password is handed to nmcli on stdin (`passwd-file /dev/stdin`), never
in argv, where any local process could read it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..run import Result, Runner

WAIT = ["--wait", "30"]


def split_terse(line: str) -> list[str]:
    """nmcli -t fields are ':'-separated with '\\:' and '\\\\' escaped."""
    out, cur, i = [], [], 0
    while i < len(line):
        c = line[i]
        if c == "\\" and i + 1 < len(line):
            cur.append(line[i + 1])
            i += 2
            continue
        if c == ":":
            out.append("".join(cur))
            cur = []
        else:
            cur.append(c)
        i += 1
    out.append("".join(cur))
    return out


def signal_bars(signal: int) -> int:
    return 4 if signal >= 70 else 3 if signal >= 50 else 2 if signal >= 25 else 1


@dataclass
class Device:
    name: str
    kind: str          # wifi | ethernet
    state: str
    connection: str

    @property
    def connected(self) -> bool:
        return self.state.startswith("connected")


@dataclass
class State:
    wifi_hardware: bool
    wifi_enabled: bool
    networking: bool
    devices: list[Device] = field(default_factory=list)

    @property
    def current(self) -> str:
        """Name of the connection in use, Wi-Fi first."""
        for kind in ("wifi", "ethernet"):
            for d in self.devices:
                if d.kind == kind and d.connected and d.connection:
                    return d.connection
        return ""

    @property
    def wired_connected(self) -> bool:
        return any(d.kind == "ethernet" and d.connected for d in self.devices)


@dataclass
class WifiNetwork:
    ssid: str
    signal: int
    security: str
    active: bool
    known: bool = False

    @property
    def secure(self) -> bool:
        return bool(self.security.strip()) and self.security.strip() != "--"

    @property
    def enterprise(self) -> bool:
        return "802.1X" in self.security


class Network:
    def __init__(self, runner: Runner):
        self.r = runner

    def state(self) -> State:
        g = self.r.run(["nmcli", "-t", "-f", "WIFI-HW,WIFI,NETWORKING", "general"])
        hw, wifi, net = (split_terse(g.out.strip()) + ["", "", ""])[:3]
        st = State(wifi_hardware=hw == "enabled", wifi_enabled=wifi == "enabled", networking=net == "enabled")
        d = self.r.run(["nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "device"])
        for line in d.out.splitlines():
            parts = split_terse(line)
            if len(parts) < 4 or parts[1] not in ("wifi", "ethernet"):
                continue
            st.devices.append(Device(parts[0], parts[1], parts[2], parts[3]))
        return st

    def known_wifi(self) -> set[str]:
        res = self.r.run(["nmcli", "-t", "-f", "NAME,TYPE,DEVICE", "connection", "show"])
        known = set()
        for line in res.out.splitlines():
            parts = split_terse(line)
            if len(parts) >= 2 and parts[1] == "802-11-wireless":
                known.add(parts[0])
        return known

    def scan(self, rescan: bool = False) -> list[WifiNetwork]:
        res = self.r.run(["nmcli", "-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY,BSSID", "device", "wifi", "list",
                          "--rescan", "yes" if rescan else "auto"], timeout=40)
        best: dict[str, WifiNetwork] = {}
        for line in res.out.splitlines():
            parts = split_terse(line)
            if len(parts) < 4 or not parts[1]:
                continue  # hidden network
            try:
                signal = int(parts[2])
            except ValueError:
                signal = 0
            n = WifiNetwork(ssid=parts[1], signal=signal, security=parts[3], active=parts[0].strip() == "*")
            old = best.get(n.ssid)
            if old is None or n.active or (not old.active and n.signal > old.signal):
                best[n.ssid] = n
        known = self.known_wifi() if best else set()
        for n in best.values():
            n.known = n.ssid in known
        return sorted(best.values(), key=lambda n: (not n.active, -n.signal, n.ssid.lower()))

    def set_wifi(self, on: bool) -> Result:
        return self.r.run(["nmcli", "radio", "wifi", "on" if on else "off"])

    def connect(self, ssid: str, password: str | None, known: bool = False) -> Result:
        if known and not password:
            return self.r.run(["nmcli", *WAIT, "connection", "up", "id", ssid], timeout=45)
        if not password:
            return self.r.run(["nmcli", *WAIT, "device", "wifi", "connect", ssid], timeout=45)
        if known:
            self.r.run(["nmcli", "connection", "delete", "id", ssid])
        add = self.r.run(["nmcli", "connection", "add", "type", "wifi", "con-name", ssid, "ifname", "*",
                          "ssid", ssid, "wifi-sec.key-mgmt", "wpa-psk"])
        if not add.ok:
            return add
        up = self.r.run(["nmcli", *WAIT, "connection", "up", "id", ssid, "passwd-file", "/dev/stdin"],
                        stdin=f"802-11-wireless-security.psk:{password}\n", timeout=45)
        if not up.ok:
            self.r.run(["nmcli", "connection", "delete", "id", ssid])
        return up

    def disconnect_wifi(self, device: str) -> Result:
        return self.device_disconnect(device)

    def device_connect(self, device: str) -> Result:
        return self.r.run(["nmcli", *WAIT, "device", "connect", device], timeout=45)

    def device_disconnect(self, device: str) -> Result:
        return self.r.run(["nmcli", "device", "disconnect", device])
