"""About this computer: Lucent version, a short hardware summary, and the
computer's name (systemd-hostnamed: read freely, renamed through polkit)."""

from __future__ import annotations

import json
import os
import platform
import re
import shutil
import socket
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from .. import dbus
from ..i18n import _, ngettext
from ..run import Result, Runner

OS_RELEASE = Path("/etc/os-release")
MEMINFO = Path("/proc/meminfo")
DMI = Path("/sys/class/dmi/id")
DT_MODEL = Path("/sys/firmware/devicetree/base/model")
JUNK = {"", "to be filled by o.e.m.", "default string", "system product name", "not applicable", "none"}


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip().strip("\0")
    except OSError:
        return ""


def os_release() -> dict[str, str]:
    out = {}
    for line in _read(OS_RELEASE).splitlines():
        k, sep, v = line.partition("=")
        if sep:
            out[k] = v.strip().strip('"')
    return out


def machine_model() -> str:
    vendor = _read(DMI / "sys_vendor")
    for key in ("product_version", "product_name"):
        name = _read(DMI / key)
        if name.lower() not in JUNK and not name.lower().startswith("rev"):
            return f"{vendor} {name}".strip() if vendor.lower() not in JUNK else name
    return _read(DT_MODEL)


HOSTNAMED = ("org.freedesktop.hostname1", "/org/freedesktop/hostname1", "org.freedesktop.hostname1")

# Russian to Latin for the network name (the shown name keeps the Cyrillic):
# U+0430..U+044F in alphabet order, and U+0451 (yo).
_TRANSLIT = dict(zip((chr(c) for c in range(0x430, 0x450)),
                     ["a", "b", "v", "g", "d", "e", "zh", "z", "i", "y", "k", "l", "m", "n", "o", "p",
                      "r", "s", "t", "u", "f", "kh", "ts", "ch", "sh", "shch", "", "y", "", "e", "yu", "ya"]))
_TRANSLIT[chr(0x451)] = "e"


def host_name(display: str) -> str:
    """The network (static) host name for a display name: lowercase Latin
    letters, digits and hyphens, at most 63 characters (RFC 1123 label)."""
    text = "".join(_TRANSLIT.get(c, c) for c in display.strip().lower())
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = text.replace("'", "")
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:63].rstrip("-")


@dataclass(frozen=True)
class ComputerName:
    shown: str      # what About shows: the pretty name if set, else the host name
    static: str     # /etc/hostname ("" = unset: os-release DEFAULT_HOSTNAME is used)
    pretty: str


@dataclass
class Summary:
    os_name: str
    os_version: str
    model: str
    cpu: str
    arch: str
    memory_gb: float
    disk_total_gb: float
    disk_free_gb: float
    hostname: str
    kernel: str


def qtdbus_hostnamed_call(method: str, *args) -> tuple[bool, str]:
    """hostnamed call from inside this process, polkit allowed to ask: both
    renames check the same action for the same process, so the password is
    asked once (busctl would be a new process, asked again)."""
    from PySide6.QtDBus import QDBus, QDBusConnection, QDBusMessage

    msg = QDBusMessage.createMethodCall(*HOSTNAMED, method)
    msg.setArguments(list(args))
    msg.setInteractiveAuthorizationAllowed(True)
    reply = QDBusConnection.systemBus().call(msg, QDBus.Block, 180_000)
    if reply.type() == QDBusMessage.MessageType.ErrorMessage:
        return False, reply.errorMessage() or reply.errorName()
    return True, ""


class About:
    def __init__(self, runner: Runner, hostnamed_call=None):
        self.r = runner
        self.hostnamed_call = hostnamed_call or qtdbus_hostnamed_call
        self._cpu_fields: dict[str, str] | None = None

    def _lscpu(self) -> dict[str, str]:
        if self._cpu_fields is None:
            res = self.r.run(["lscpu", "--json"])
            try:
                self._cpu_fields = {f["field"].rstrip(":"): f["data"] for f in json.loads(res.out)["lscpu"]}
            except (ValueError, KeyError, TypeError):
                self._cpu_fields = {}
        return self._cpu_fields

    def cpu(self) -> str:
        fields = self._lscpu()
        name = fields.get("Model name", "")
        if not name or name == "-":
            name = fields.get("Vendor ID", "") or platform.machine()
        cores = fields.get("CPU(s)", "")
        if not cores.isdigit():
            return name
        return ngettext("{name} ({n} core)", "{name} ({n} cores)", int(cores)).format(name=name, n=cores)

    def summary(self) -> Summary:
        rel = os_release()
        mem_kb = 0
        for line in _read(MEMINFO).splitlines():
            if line.startswith("MemTotal:"):
                mem_kb = int(line.split()[1])
        try:
            du = shutil.disk_usage("/var")
            total, free = du.total / 1e9, du.free / 1e9
        except OSError:
            total = free = 0.0
        return Summary(
            os_name=rel.get("PRETTY_NAME", "Lucent OS"),
            os_version=rel.get("PRETTY_NAME", "").removeprefix("Lucent OS ").split(" ")[0] or rel.get("VERSION_ID", ""),
            model=machine_model(), cpu=self.cpu(), arch=self._lscpu().get("Architecture") or platform.machine(),
            memory_gb=mem_kb / 1024 / 1024, disk_total_gb=total, disk_free_gb=free,
            hostname=self.computer_name().shown, kernel=platform.release())

    def computer_name(self) -> ComputerName:
        res = self.r.run(dbus.get_property(dbus.SYSTEM, *HOSTNAMED, "Hostname", "StaticHostname", "PrettyHostname"),
                         timeout=10)
        try:
            current, static, pretty = (str(v) for v in dbus.values(res.out)[:3])
        except (ValueError, KeyError, TypeError):
            current, static, pretty = socket.gethostname(), "", ""
        return ComputerName(shown=pretty or current, static=static, pretty=pretty)

    def rename(self, display: str) -> Result:
        """Rename this PC like Windows' "Rename this PC": the name as typed is
        the pretty name, its Latin form the network name. hostnamed asks
        polkit (an administrator's password, once) for each."""
        display = " ".join(display.split())
        name = host_name(display)
        if not display or not name:
            return Result(1, "", _("Use at least one letter or digit."))
        if len(display) > 64:
            return Result(1, "", _("Use at most 64 characters."))
        for method, value in (("SetStaticHostname", name), ("SetPrettyHostname", display if display != name else "")):
            ok, err = self.hostnamed_call(method, value, True)    # True: interactive (polkit may ask)
            if not ok:
                return Result(1, "", err)
        return Result(0, "", "")

    def open_advanced(self) -> bool:
        """KDE System Settings: every setting Lucent's own app leaves out."""
        return self.r.spawn(["systemsettings"])

    def open_hardware_details(self) -> bool:
        return self.r.spawn(["kinfocenter"])


def gpu() -> str:
    """Kernel driver of the first display adapter (amdgpu, i915, virtio_gpu...)."""
    for card in sorted(Path("/sys/class/drm").glob("card[0-9]")):
        drv = card / "device" / "driver"
        if drv.exists():
            return os.path.basename(os.path.realpath(drv))
    return ""
