"""Windows programs installed through Lucent Bridge.

`lucent-bridge list --json` lists them (one Wine prefix each);
`lucent-bridge plan --json` on the program's .exe gives the compatibility
status from Bridge's own database (matched by the program's product name,
the same lookup a launch uses); the size shown is the program's own folder.
"""

from __future__ import annotations

import json
import os
import shlex
import stat
from dataclasses import dataclass
from pathlib import Path

from ..i18n import _
from ..run import Result, Runner


def mode(machine: str) -> str:
    if machine in ("x86_64", "amd64"):
        return "native"
    if machine in ("aarch64", "arm64"):
        return "translated"
    return "unsupported"


def human_size(n: int) -> str:
    units = [_("B"), _("KB"), _("MB"), _("GB"), _("TB")]
    size, i = float(n), 0
    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1
    if i == 0:
        return f"{int(size)} {units[0]}"
    text = f"{size:.1f}"
    if _("B") != "B":  # translated catalogs use a decimal comma
        text = text.replace(".", ",")
    return f"{text} {units[i]}"


def folder_size(path: Path) -> int | None:
    """Bytes of regular files under path; symlinks and hard links count once."""
    if not path.is_dir():
        return None
    total, seen = 0, set()
    for root, _dirs, files in os.walk(path):
        for f in files:
            try:
                st = os.lstat(os.path.join(root, f))
            except OSError:
                continue
            if stat.S_ISREG(st.st_mode) and st.st_ino not in seen:
                seen.add(st.st_ino)
                total += st.st_size
    return total


def _desktop_entry(path: str) -> dict[str, str]:
    entry: dict[str, str] = {}
    try:
        lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return entry
    in_main = False
    for line in lines:
        if line.startswith("["):
            in_main = line.strip() == "[Desktop Entry]"
            continue
        if in_main and "=" in line:
            k, _sep, v = line.partition("=")
            entry.setdefault(k.strip(), v.strip())
    return entry


@dataclass
class App:
    app_id: str
    name: str
    runner: str
    icon: str = ""
    exe: str = ""
    folder: str = ""
    size: int | None = None
    status: str = "unknown"     # works | partial | broken | unknown
    exe_arch: str = ""
    notes: str = ""


class WinApps:
    def __init__(self, runner: Runner):
        self.r = runner

    def apps(self) -> list[App]:
        res = self.r.run(["lucent-bridge", "list", "--json"])
        try:
            items = json.loads(res.out) if res.ok else []
        except json.JSONDecodeError:
            items = []
        out = []
        for m in items:
            a = App(app_id=m["app_id"], name=m.get("name") or m["app_id"], runner=m.get("runner", ""),
                    icon=(m.get("icons") or [""])[0])
            for d in m.get("desktop_entries") or []:
                e = _desktop_entry(d)
                argv = shlex.split(e.get("Exec", ""))
                if argv[:2] == ["lucent-bridge", "run"] and len(argv) > 2:
                    a.exe = next((x for x in argv[2:] if not x.startswith("-")), "")
                    a.folder = e.get("Path") or str(Path(a.exe).parent)
                    a.icon = a.icon or e.get("Icon", "")
                    break
            if a.exe:
                plan = self.r.run(["lucent-bridge", "plan", "--json", "--assume-tools", a.exe])
                try:
                    p = json.loads(plan.out) if plan.ok else {}
                except json.JSONDecodeError:
                    p = {}
                compat = p.get("compat") or {}
                a.status = compat.get("status", "unknown")
                a.notes = compat.get("notes", "")
                a.exe_arch = p.get("exe_arch", "")
                a.size = folder_size(Path(a.folder))
            if a.icon and not os.path.isfile(a.icon):
                a.icon = ""
            out.append(a)
        return sorted(out, key=lambda a: a.name.lower())

    def remove(self, app_id: str) -> Result:
        return self.r.run(["lucent-bridge", "remove", "--yes", app_id], timeout=120)

    def open_folder(self, folder: str) -> bool:
        return self.r.spawn(["xdg-open", folder])
