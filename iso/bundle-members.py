#!/usr/bin/python3
"""Print the entries of a flatpak installation (/var/lib/flatpak) in the
order the offline app bundle stores them: NUL-terminated, relative ("./"),
for `tar --no-recursion --null -T -`.

Order, for compression: directories first, then the deployed files sorted
by what they are rather than by where flatpak put them, so the same file of
two versions of a runtime (KDE 6.10 and 6.11, GNOME 50 and 51, GL 25.08 and
26.08) sits side by side, within zstd's window, and the second copy costs
little:

  ./runtime/org.kde.Platform/x86_64/6.10/<commit>/files/lib/libQt6Core.so.6
  sorts as (runtime/org.kde.Platform/x86_64, files/lib/libQt6Core.so.6, 6.10)

Everything else (repo/objects, exports, symlinks such as `current`) comes
last. The repo's objects are hard links to the deployed files, and tar
stores a file's content at its first name only, so they cost a few bytes.

Usage: bundle-members.py ROOT > members
"""
from __future__ import annotations

import os
import sys


def key(rel: str) -> tuple:
    parts = rel.split("/")
    # kind/id/arch/branch/commit/rest...
    if len(parts) >= 6 and parts[0] in ("app", "runtime"):
        kind, ref_id, arch, branch, _commit, *rest = parts
        return (1, f"{kind}/{ref_id}/{arch}", "/".join(rest), branch, rel)
    return (2, rel)


def main(root: str) -> int:
    dirs: list[str] = []
    files: list[str] = []
    for top, dirnames, filenames in os.walk(root):
        rel_top = os.path.relpath(top, root)
        for name in dirnames + filenames:
            rel = name if rel_top == "." else f"{rel_top}/{name}"
            full = os.path.join(top, name)
            if os.path.isdir(full) and not os.path.islink(full):
                dirs.append(rel)
            else:
                files.append(rel)
    dirs.sort()
    files.sort(key=key)
    out = sys.stdout.buffer
    for rel in dirs + files:
        out.write(b"./" + os.fsencode(rel) + b"\0")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
