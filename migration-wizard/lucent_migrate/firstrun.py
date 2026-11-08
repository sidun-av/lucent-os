"""First-login autostart decision for the migration wizard."""

from __future__ import annotations

import os
from pathlib import Path

from .volumes import Volume


def config_dir() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")


def _marker(cfg: Path) -> Path:
    return cfg / "lucent" / "migration-done"


# Regular accounts start here (login.defs UID_MIN). System accounts with a
# graphical session, like Fedora's first-boot "plasma-setup" user, must
# never get the wizard.
UID_MIN = 1000


def should_autostart(cfg: Path, vols: list[Volume], uid: int | None = None) -> bool:
    """Show the wizard once, only to regular users, and only if this machine
    has Windows disks (BitLocker counts: the wizard explains how to unlock them)."""
    uid = os.getuid() if uid is None else uid
    return uid >= UID_MIN and not _marker(cfg).exists() and bool(vols)


def mark_done(cfg: Path) -> None:
    marker = _marker(cfg)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.touch()
