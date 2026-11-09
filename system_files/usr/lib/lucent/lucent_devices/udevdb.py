"""Read the udev database (`udevadm info --export-db`).

One record per device; the fields lucent-devices needs are its sysfs path,
subsystem, device type, bound driver and properties (the hwdb's
ID_VENDOR_FROM_DATABASE / ID_MODEL_FROM_DATABASE among them).
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field


@dataclass
class Record:
    path: str
    props: dict = field(default_factory=dict)
    subsystem: str | None = None
    devtype: str | None = None
    driver: str | None = None

    @property
    def sysname(self) -> str:
        return self.path.rsplit("/", 1)[-1]


def parse(text: str) -> list[Record]:
    records: list[Record] = []
    cur: Record | None = None
    for raw in text.splitlines():
        line = raw.rstrip("\n")
        if not line.strip():
            cur = None
            continue
        tag, _, value = line.partition(": ")
        if tag == "P":
            cur = Record(path=value)
            records.append(cur)
            continue
        if cur is None:
            continue
        if tag == "U":
            cur.subsystem = value
        elif tag == "T":
            cur.devtype = value
        elif tag == "V":
            cur.driver = value
        elif tag == "E":
            key, _, val = value.partition("=")
            cur.props[key] = val
    for r in records:
        r.subsystem = r.subsystem or r.props.get("SUBSYSTEM")
        r.devtype = r.devtype or r.props.get("DEVTYPE")
        r.driver = r.driver or r.props.get("DRIVER") or None
    return records


def read_live() -> str:
    """The running system's database (no network; udevadm reads /sys and /run/udev)."""
    return subprocess.run(["udevadm", "info", "--export-db"], capture_output=True,
                          text=True, check=True).stdout


def hwdb_query(modalias: str) -> dict:
    """Names from the hwdb for a modalias, for records udev never annotated
    (e.g. when /run/udev is not visible, as in a container)."""
    try:
        out = subprocess.run(["systemd-hwdb", "query", modalias], capture_output=True,
                             text=True, timeout=5).stdout
    except (OSError, subprocess.SubprocessError):
        return {}
    res = {}
    for line in out.splitlines():
        k, _, v = line.partition("=")
        if k.endswith("_FROM_DATABASE"):
            res[k] = v
    return res
