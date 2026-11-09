"""About this computer: Lucent version and a short hardware summary."""

from __future__ import annotations

import json
import os
import platform
import shutil
import socket
from dataclasses import dataclass
from pathlib import Path

from ..i18n import ngettext
from ..run import Runner

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


class About:
    def __init__(self, runner: Runner):
        self.r = runner
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
            hostname=socket.gethostname(), kernel=platform.release())

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
