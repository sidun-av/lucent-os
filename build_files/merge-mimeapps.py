#!/usr/bin/python3
"""Merge a mimeapps.list fragment's [Default Applications] into lists.

Usage: merge-mimeapps.py FRAGMENT FIRST [OTHER...]

FIRST is created if missing; each OTHER is updated only if it exists (so a
higher-precedence list shipped by the base image can't shadow the fragment).
Other groups and keys are kept; comments and order are preserved.
"""
import sys
from pathlib import Path

GROUP = "[Default Applications]"


def defaults(text: str) -> dict[str, str]:
    out, inside = {}, False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("["):
            inside = s == GROUP
        elif inside and "=" in s and not s.startswith("#"):
            k, v = s.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def merge(text: str, new: dict[str, str]) -> str:
    lines = text.splitlines()
    todo = dict(new)
    out, inside, group_seen = [], False, False
    for line in lines:
        s = line.strip()
        if s.startswith("["):
            if inside:
                blanks = []
                while out and not out[-1].strip():
                    blanks.append(out.pop())
                out.extend(f"{k}={v}" for k, v in todo.items())
                out.extend(blanks)
                todo.clear()
            inside = s == GROUP
            group_seen |= inside
        elif inside and "=" in s and not s.startswith("#"):
            k = s.split("=", 1)[0].strip()
            if k in todo:
                line = f"{k}={todo.pop(k)}"
        out.append(line)
    if todo:
        if not group_seen:
            out += ([""] if out else []) + [GROUP]
        out.extend(f"{k}={v}" for k, v in todo.items())
    return "\n".join(out) + "\n"


def main(argv: list[str]) -> int:
    new = defaults(Path(argv[1]).read_text())
    if not new:
        print(f"{argv[1]}: no [Default Applications] entries", file=sys.stderr)
        return 1
    for i, name in enumerate(argv[2:]):
        p = Path(name)
        if not p.exists() and i > 0:
            continue
        p.write_text(merge(p.read_text() if p.exists() else "", new))
        print(f"{p}: {len(new)} default handler(s) set")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
