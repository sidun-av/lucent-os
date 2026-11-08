"""Resolve the Linux destination folders from ~/.config/user-dirs.dirs."""

from __future__ import annotations

import os
import re
from pathlib import Path

DEFAULTS = {
    "DESKTOP": "Desktop",
    "DOCUMENTS": "Documents",
    "DOWNLOAD": "Downloads",
    "MUSIC": "Music",
    "PICTURES": "Pictures",
    "VIDEOS": "Videos",
}

_LINE = re.compile(r'^XDG_([A-Z]+)_DIR="(.*)"\s*$')


def parse_user_dirs(text: str, home: Path) -> dict[str, Path]:
    dirs: dict[str, Path] = {}
    for line in text.splitlines():
        m = _LINE.match(line.strip())
        if not m:
            continue
        key, value = m.groups()
        if value.startswith("$HOME"):
            rest = value[len("$HOME"):].strip("/")
            if not rest:
                continue  # "$HOME/" = directory disabled
            dirs[key] = home / rest
        elif value.startswith("/"):
            dirs[key] = Path(value)
    return dirs


def target_dirs(home: Path | None = None, config_home: Path | None = None) -> dict[str, Path]:
    home = home or Path.home()
    config_home = config_home or Path(os.environ.get("XDG_CONFIG_HOME") or home / ".config")
    try:
        parsed = parse_user_dirs((config_home / "user-dirs.dirs").read_text(), home)
    except OSError:
        parsed = {}
    return {key: parsed.get(key, home / name) for key, name in DEFAULTS.items()}
