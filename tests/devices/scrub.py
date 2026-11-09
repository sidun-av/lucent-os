#!/usr/bin/env python3
"""Scrub machine identifiers from a recorded udev database or kernel log
before it becomes a fixture in this public repo.

    python3 tests/devices/scrub.py FILE...      (rewrites in place)

Serial numbers, UUIDs, WWNs, MAC-derived names and host names are replaced;
everything lucent-devices reads (paths, drivers, IDs, classes, names from
the hwdb, kernel messages) is kept.
"""
import re
import sys

_KEY = re.compile(r"^(E: [A-Z0-9_]*(?:SERIAL|UUID|WWN|NET_NAME_MAC|MAC_ADDRESS|SCSI_IDENT_LUN|SCSI_IDENT_PORT|SCSI_IDENT_SERIAL)[A-Z0-9_]*=).*$", re.M)
_HOST = re.compile(r"(Hostname set to <)[^>]*(>)")
_UUIDISH = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I)
_PARTUUID = re.compile(r"(PARTUUID=)\S+")
_MAC = re.compile(r"\b[0-9a-f]{2}(?::[0-9a-f]{2}){5}\b", re.I)


def scrub(text: str) -> str:
    text = _KEY.sub(r"\1REDACTED", text)
    text = _HOST.sub(r"\1host\2", text)
    text = _PARTUUID.sub(r"\1REDACTED", text)
    text = _MAC.sub("00:00:00:00:00:00", text)
    # Partition/filesystem UUIDs in free text (not Hyper-V device GUIDs in
    # paths, which identify the device *type* and are the same everywhere).
    out = []
    for line in text.splitlines(keepends=True):
        # Disk symlinks carry serial numbers and WWNs; nothing reads them.
        if line.startswith(("S: disk/", "E: DEVLINKS=/dev/disk/")):
            continue
        if line.startswith(("P:", "E: DEVPATH=", "M:", "J:", "E: ID_PATH", "E: MODALIAS", "L:", "N:")):
            out.append(line)
        else:
            out.append(_UUIDISH.sub("00000000-0000-0000-0000-000000000000", line))
    return "".join(out)


if __name__ == "__main__":
    for path in sys.argv[1:]:
        with open(path, encoding="utf-8", errors="replace") as f:
            data = f.read()
        with open(path, "w", encoding="utf-8") as f:
            f.write(scrub(data))
