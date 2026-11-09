"""lucent-theme: switch Lucent's light/dark/auto mode and accent in one step.

  lucent-theme apply [--mode light|dark|auto] [--accent NAME|#RRGGBB]
  lucent-theme status [--json]
  lucent-theme sync
  lucent-theme accents [--json]

Exit codes: 0 done, 1 a step failed (details on stderr), 2 bad arguments.
See docs/theming.md.
"""
from __future__ import annotations

import argparse
import json
import sys

from . import accents, theme


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="lucent-theme", description="Lucent light/dark mode and accent colour.")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("apply", help="switch mode and/or accent (live, no re-login)")
    a.add_argument("--mode", choices=theme.MODES)
    a.add_argument("--accent", help="indigo, azure, lagoon, violet, orchid, rose, pine, slate, or #rrggbb "
                                    "(snapped to the nearest of them)")
    s = sub.add_parser("status", help="what is chosen and what is showing")
    s.add_argument("--json", action="store_true")
    sub.add_parser("sync", help="put the chosen look back (after Plasma switched themes)")
    l = sub.add_parser("accents", help="the accent swatches")
    l.add_argument("--json", action="store_true")
    return p


def main(argv=None, runner=None) -> int:
    try:
        args = _parser().parse_args(argv)
    except SystemExit as e:          # argparse: --help (0) or bad arguments (2)
        return int(e.code or 0)
    r = runner or theme.Runner()
    errors: list[str] = []
    if args.cmd == "apply":
        if args.mode is None and args.accent is None:
            print("lucent-theme apply: give --mode and/or --accent", file=sys.stderr)
            return 2
        acc = args.accent
        if acc is not None and not (accents.find(acc) or (acc.startswith("#") and len(acc) == 7)):
            print(f"lucent-theme: unknown accent {acc!r} (try: lucent-theme accents)", file=sys.stderr)
            return 2
        code = theme.apply(r, mode=args.mode, accent=acc, errors=errors)
    elif args.cmd == "sync":
        code = theme.sync(r, errors=errors)
    elif args.cmd == "status":
        st = theme.status()
        if args.json:
            print(json.dumps(st))
        else:
            for k, v in st.items():
                print(f"{k}: {v}")
        return 0
    else:
        rows = [{"id": a.id, "name": a.name, "hex": a.hex} for a in accents.ACCENTS]
        if args.json:
            print(json.dumps(rows))
        else:
            for row in rows:
                print(f"{row['id']:8} {row['hex']}")
        return 0
    for e in errors:
        print(f"lucent-theme: {e}", file=sys.stderr)
    return code
