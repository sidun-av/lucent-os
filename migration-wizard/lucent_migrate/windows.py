"""Locate Windows user profiles and their known folders on a mounted volume.

NTFS is case-insensitive but the Linux view of it may not be, so every
lookup goes through `child_ci`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# Windows folder name -> XDG user-dir key
KNOWN_FOLDERS: dict[str, str] = {
    "Desktop": "DESKTOP",
    "Documents": "DOCUMENTS",
    "Downloads": "DOWNLOAD",
    "Music": "MUSIC",
    "Pictures": "PICTURES",
    "Videos": "VIDEOS",
}

# Folders Windows' OneDrive "backup" feature moves into OneDrive\.
ONEDRIVE_FOLDERS = {"Desktop", "Documents", "Pictures"}

SYSTEM_PROFILES = {"public", "default", "default user", "all users", "defaultuser0", "defaultapppool"}


@dataclass
class WindowsUser:
    name: str
    home: Path
    folders: dict[str, list[Path]] = field(default_factory=dict)


def child_ci(parent: Path, name: str) -> Path | None:
    """Case-insensitive child lookup; None when absent."""
    try:
        entries = list(parent.iterdir())
    except OSError:
        return None
    for entry in entries:
        if entry.name == name:
            return entry
    lowered = name.lower()
    return next((e for e in entries if e.name.lower() == lowered), None)


def is_windows_system(root: Path) -> bool:
    win = child_ci(root, "Windows")
    return bool(win and child_ci(win, "System32"))


def _is_profile(home: Path) -> bool:
    if not home.is_dir() or home.is_symlink():
        return False
    if home.name.lower() in SYSTEM_PROFILES:
        return False
    return child_ci(home, "NTUSER.DAT") is not None or any(
        child_ci(home, f) is not None for f in KNOWN_FOLDERS
    )


def _folders(home: Path) -> dict[str, list[Path]]:
    onedrive = child_ci(home, "OneDrive")
    result: dict[str, list[Path]] = {}
    for win_name, key in KNOWN_FOLDERS.items():
        sources: list[Path] = []
        local = child_ci(home, win_name)
        if local and local.is_dir() and not local.is_symlink() and any(local.iterdir()):
            sources.append(local)
        if onedrive and win_name in ONEDRIVE_FOLDERS:
            od = child_ci(onedrive, win_name)
            if od and od.is_dir():
                sources.append(od)
        if not sources and local and local.is_dir() and not local.is_symlink():
            sources.append(local)  # empty but present: still show it
        if sources:
            result[key] = sources
    return result


def find_users(root: Path) -> list[WindowsUser]:
    users_dir = child_ci(root, "Users")
    if not users_dir or not users_dir.is_dir():
        return []
    users = [
        WindowsUser(home.name, home, _folders(home))
        for home in users_dir.iterdir()
        if _is_profile(home)
    ]
    return sorted(users, key=lambda u: u.name.lower())
