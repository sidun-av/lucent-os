"""KDE configuration files (kdeglobals, kwinrc, kxkbrc, ...).

Reads parse the user's file and the system defaults directly (cheap, no
process per key); writes go through `kwriteconfig6 --notify`, which is what
KDE's own settings modules do, so running apps that watch the file (KWin,
Plasma, KConfigWatcher users) pick the change up immediately.
"""

from __future__ import annotations

import os
from pathlib import Path

from .run import Result, Runner


def config_home() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")


def config_dirs() -> list[Path]:
    dirs = os.environ.get("XDG_CONFIG_DIRS") or "/etc/xdg"
    return [Path(d) for d in dirs.split(":") if d]


def parse(text: str) -> dict[tuple[str, ...], dict[str, str]]:
    """KConfig INI: groups like [A][B] become ("A", "B"); `key[$e]` and
    locale suffixes are dropped to the bare key."""
    groups: dict[tuple[str, ...], dict[str, str]] = {}
    cur: dict[str, str] | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("["):
            names = tuple(part for part in line[1:-1].split("][")) if line.endswith("]") else (line[1:],)
            cur = groups.setdefault(names, {})
            continue
        if cur is None or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key.endswith("]") and "[" in key:
            key = key[: key.index("[")]
        cur[key] = value.strip()
    return groups


def read(file: str, group: str | tuple[str, ...], key: str, default: str = "") -> str:
    """User value, else the first system default (XDG_CONFIG_DIRS order)."""
    g = (group,) if isinstance(group, str) else group
    for path in [config_home() / file] + [d / file for d in config_dirs()]:
        try:
            groups = parse(path.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
        if key in groups.get(g, {}):
            return groups[g][key]
    return default


def write_argv(file: str, group: str | tuple[str, ...], key: str, value: str | bool | None) -> list[str]:
    argv = ["kwriteconfig6", "--file", file]
    for g in ((group,) if isinstance(group, str) else group):
        argv += ["--group", g]
    argv += ["--key", key, "--notify"]
    if value is None:
        argv.append("--delete")
    elif isinstance(value, bool):
        argv += ["--type", "bool", "true" if value else "false"]
    else:
        argv.append(str(value))
    return argv


def write(runner: Runner, file: str, group: str | tuple[str, ...], key: str,
          value: str | bool | None) -> Result:
    return runner.run(write_argv(file, group, key, value))
