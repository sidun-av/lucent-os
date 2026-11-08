"""Find Windows (NTFS / BitLocker) volumes from `lsblk -J` output.

Pure parsing lives here; the only side-effecting helpers are `run_lsblk`
and `mount_readonly`, which shell out and are kept trivially thin.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from typing import Any

LSBLK_COLUMNS = "NAME,PATH,TYPE,FSTYPE,SIZE,LABEL,UUID,PARTTYPE,RM,HOTPLUG,MOUNTPOINTS"

# GPT type of the Windows Recovery Environment partition.
WINRE_PARTTYPE = "de94bba4-06d1-4d40-a16a-bfd50179d6ac"
WINDOWS_FSTYPES = {"ntfs", "bitlocker"}


@dataclass(frozen=True)
class Volume:
    path: str
    fstype: str
    size: int
    label: str | None = None
    uuid: str | None = None
    disk: str | None = None
    removable: bool = False
    recovery: bool = False
    mountpoint: str | None = None
    parttype: str | None = field(default=None, compare=False)

    @property
    def bitlocker(self) -> bool:
        return self.fstype.lower() == "bitlocker"


def _bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip() not in ("", "0", "false")
    return bool(value)


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _walk(devices: list[dict], disk: str | None, out: list[Volume]) -> None:
    for dev in devices:
        this_disk = dev.get("path") if dev.get("type") == "disk" else disk
        fstype = (dev.get("fstype") or "").strip()
        if fstype.lower() in WINDOWS_FSTYPES:
            mounts = [m for m in (dev.get("mountpoints") or [dev.get("mountpoint")]) if m]
            parttype = (dev.get("parttype") or "").lower() or None
            out.append(
                Volume(
                    path=dev["path"],
                    fstype=fstype,
                    size=_int(dev.get("size")),
                    label=dev.get("label") or None,
                    uuid=dev.get("uuid") or None,
                    disk=this_disk,
                    removable=_bool(dev.get("rm")) or _bool(dev.get("hotplug")),
                    recovery=parttype == WINRE_PARTTYPE,
                    mountpoint=mounts[0] if mounts else None,
                    parttype=parttype,
                )
            )
        _walk(dev.get("children") or [], this_disk, out)


def parse_lsblk(data: str | dict) -> list[Volume]:
    """Return every NTFS or BitLocker block device, in lsblk order."""
    if isinstance(data, str):
        data = json.loads(data)
    out: list[Volume] = []
    _walk(data.get("blockdevices") or [], None, out)
    return out


def migratable(vols: list[Volume]) -> list[Volume]:
    """Volumes we can actually read files from (no WinRE, no locked BitLocker)."""
    return [v for v in vols if not v.recovery and not v.bitlocker]


def run_lsblk() -> list[Volume]:
    out = subprocess.run(
        ["lsblk", "-J", "-b", "-o", LSBLK_COLUMNS],
        check=True, capture_output=True, text=True,
    ).stdout
    return parse_lsblk(out)


def udisksctl_mount_cmd(vol: Volume) -> list[str]:
    # Read-only on purpose: Windows may be hibernated ("Fast Startup"), and a
    # migration tool must never risk the user's only copy of their data.
    return ["udisksctl", "mount", "--no-user-interaction", "-b", vol.path, "-o", "ro"]


_MOUNTED_RE = re.compile(r"^Mounted \S+ at (.+?)\.?\s*$")


def parse_udisksctl_mount(text: str) -> str | None:
    for line in text.splitlines():
        m = _MOUNTED_RE.match(line.strip())
        if m:
            return m.group(1)
    return None


def mount_readonly(vol: Volume) -> str:
    """Mount via udisks (polkit allows this for the active local user)."""
    if vol.mountpoint:
        return vol.mountpoint
    proc = subprocess.run(udisksctl_mount_cmd(vol), capture_output=True, text=True)
    where = parse_udisksctl_mount(proc.stdout)
    if proc.returncode != 0 or not where:
        raise OSError((proc.stderr or proc.stdout).strip() or f"cannot mount {vol.path}")
    return where


_UNITS = ["Б", "КБ", "МБ", "ГБ", "ТБ"]


def human_size(n: int) -> str:
    size = float(n)
    for unit in _UNITS:
        if size < 1024 or unit == _UNITS[-1]:
            if unit == "Б" or size >= 100 or size == int(size):
                text = f"{int(size)}" if unit == "Б" or size == int(size) else f"{size:.0f}"
            else:
                text = f"{int(size * 10) / 10:.1f}".replace(".", ",")
            return f"{text} {unit}"
        size /= 1024
    raise AssertionError("unreachable")
