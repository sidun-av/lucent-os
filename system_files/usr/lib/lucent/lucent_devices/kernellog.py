"""Find firmware and probe failures in this boot's kernel log.

Kernel drivers prefix their messages with "<driver> <device>: ", e.g.

    iwlwifi 0000:00:14.3: Direct firmware load for iwlwifi-so-a0-gf-a0-93.ucode failed with error -2
    Bluetooth: hci0: Failed to load Intel firmware file intel/ibt-0040-0041.sfi (-2)
    mt7921e 0000:01:00.0: probe with driver mt7921e failed with error -110

"Direct firmware load ... failed" alone is *not* fatal: many drivers ask for
the newest firmware first and fall back to an older file (iwlwifi does this
on every boot), or ask for optional board-specific files. A message from
the driver itself that it could not load its firmware is fatal; so is a
failed probe.
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass


@dataclass
class Event:
    kind: str                 # "firmware" | "probe"
    device: str | None        # kernel device name: "0000:00:14.3", "3-10:1.0", "hci0"
    driver: str | None
    file: str | None = None
    error: int | None = None
    fatal: bool = False
    line: str = ""


_TS = re.compile(r"^\[\s*\d+\.\d+\]\s*")
_PREFIX = re.compile(r"^(?P<drv>[\w.\-]+) (?P<dev>\S+?): (?P<msg>.+)$")
_BT = re.compile(r"^Bluetooth: (?P<dev>hci\d+): (?P<msg>.+)$")
_BARE = re.compile(r"^(?P<drv>[\w.\-]+): (?P<msg>.+)$")

_FW_FILE = r"(?P<file>[\w.\-+/]+\.(?:bin|ucode|fw|sfi|ddc|pnvm|hcd|seq|sbin|tlv|nvm|dat|zst|xz|img|mbn|elf|txt))"
_SOFT = re.compile(r"Direct firmware load for (?P<file>\S+) failed with error (?P<err>-?\d+)")
_HARD = [
    re.compile(r"firmware: failed to load (?P<file>\S+) \((?P<err>-?\d+)\)"),
    re.compile(r"(?i)(?:failed|unable) to (?:load|request|get|find)\b[^:]*?firmware(?: file)?\s+" + _FW_FILE
               + r"(?:\s*\((?P<err>-?[\w-]+)\))?"),
    re.compile(r"(?i)firmware file " + _FW_FILE + r" not found"),
    re.compile(r"(?i)(?:failed|unable) to (?:early )?(?:load|request)\b.*firmware(?::\s*(?P<err>-?\d+))?"),
    re.compile(r"(?i)no suitable firmware found"),
]
_PROBE_DEV = re.compile(r"probe with driver (?P<drv>\S+) failed with error (?P<err>-?\d+)")
_PROBE_OF = re.compile(r"probe of (?P<dev>\S+) failed with error (?P<err>-?\d+)")

_ERRNO = {"-ENOENT": -2, "-EIO": -5, "-ENOMEM": -12, "-EINVAL": -22, "-ETIMEDOUT": -110}


def _err(value):
    if value is None:
        return None
    if value in _ERRNO:
        return _ERRNO[value]
    try:
        return int(value)
    except ValueError:
        return None


def _strip(line: str) -> str:
    line = _TS.sub("", line.strip())
    if " kernel: " in line:
        line = line.split(" kernel: ", 1)[1]
    return line


def parse(text: str) -> list[Event]:
    events: list[Event] = []
    for raw in text.splitlines():
        line = _strip(raw)
        if not line:
            continue
        drv = dev = None
        m = _BT.match(line)
        if m:
            drv, dev, msg = "bluetooth", m["dev"], m["msg"]
        elif (m := _PREFIX.match(line)) and not m["drv"].endswith(":"):
            drv, dev, msg = m["drv"], m["dev"], m["msg"]
        elif m := _BARE.match(line):
            drv, msg = m["drv"], m["msg"]
        else:
            msg = line

        if p := _PROBE_DEV.search(msg):
            events.append(Event("probe", dev, p["drv"], error=_err(p["err"]), fatal=True, line=line))
            continue
        if p := _PROBE_OF.search(msg):
            events.append(Event("probe", p["dev"], drv, error=_err(p["err"]), fatal=True, line=line))
            continue
        if s := _SOFT.search(msg):
            events.append(Event("firmware", dev, drv, file=s["file"], error=_err(s["err"]), line=line))
            continue
        for rx in _HARD:
            h = rx.search(msg)
            if h:
                gd = h.groupdict()
                events.append(Event("firmware", dev, drv, file=gd.get("file"),
                                    error=_err(gd.get("err")), fatal=True, line=line))
                break
    return events


def read_live() -> tuple[str | None, str | None]:
    """(text, source) for this boot, or (None, None) if it cannot be read.

    The journal needs membership in wheel/adm/systemd-journal on Fedora;
    dmesg may be restricted. Without either, lucent-devices says it could
    not check firmware rather than claiming all is well.
    """
    for source, cmd in (("journal", ["journalctl", "-k", "-b", "0", "-o", "cat", "--no-pager", "-q"]),
                        ("dmesg", ["dmesg"])):
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        except (OSError, subprocess.SubprocessError):
            continue
        # A booted kernel always has messages; empty output means "not allowed".
        if p.returncode == 0 and p.stdout.count("\n") > 5:
            return p.stdout, source
    return None, None
