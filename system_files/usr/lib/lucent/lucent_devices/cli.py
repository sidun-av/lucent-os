"""lucent-devices: what hardware this computer has and whether it works.

    lucent-devices            plain text (English, or Russian under a ru_* locale)
    lucent-devices --json     machine-readable, for the Settings "Devices" page
    lucent-devices --all      also list chipset parts

Reads only local data: the udev database and this boot's kernel log. No
network access, nothing is sent anywhere. Exit status: 0 when every device
works, 1 when one needs attention, 2 on an error.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from . import inventory, kernellog, render, udevdb
from .strings import pick_lang


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="lucent-devices", description=__doc__.split("\n\n")[0])
    ap.add_argument("--json", action="store_true", help="print JSON")
    ap.add_argument("--all", action="store_true", help="also show chipset parts")
    ap.add_argument("--udev-db", metavar="FILE", help="read `udevadm info --export-db` output from FILE")
    ap.add_argument("--kernel-log", metavar="FILE", help="read the kernel log from FILE")
    args = ap.parse_args(argv)

    try:
        if args.udev_db:
            with open(args.udev_db, encoding="utf-8", errors="replace") as f:
                udev_text = f.read()
            hwdb = None
        else:
            udev_text = udevdb.read_live()
            hwdb = udevdb.hwdb_query
        if args.kernel_log:
            with open(args.kernel_log, encoding="utf-8", errors="replace") as f:
                log, source = f.read(), "file"
        else:
            log, source = kernellog.read_live()
    except (OSError, Exception) as e:  # noqa: BLE001 - one clear message, not a traceback
        print(f"lucent-devices: {e}", file=sys.stderr)
        return 2

    report = inventory.build(udevdb.parse(udev_text),
                             kernellog.parse(log) if log is not None else None,
                             kernel_log_source=source, hwdb=hwdb)
    if args.json:
        json.dump(report, sys.stdout, ensure_ascii=False, indent=1)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(render.text(report, lang=pick_lang(os.environ), show_all=args.all))
    s = report["summary"]
    return 1 if s["problem"] or s["needs_driver"] else 0
