"""System updates (rpm-ostree, which runs bootc container images) and app
updates (Flatpak).

How Lucent updates, in plain words: a new version of the whole system is
downloaded next to the one that is running and starts at the next restart.
The previous version stays on disk, so going back is one step.

rpm-ostree does the work in its daemon over D-Bus, guarded by polkit
(Fedora lets an administrator at the computer check, update and roll back
without a password prompt); `rpm-ostree status --json` describes the
versions on disk. Turning automatic downloads on or off edits a root-owned
file, so it goes through Lucent's small polkit helper (pkexec).
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .. import dbus, kconfig
from ..run import Result, Runner

RPM_OSTREED_CONF = Path("/etc/rpm-ostreed.conf")
HELPER = "/usr/libexec/lucent/settings-helper"


@dataclass
class Version:
    role: str          # update | current | previous | rollback
    build: str
    timestamp: int
    checksum: str

    @property
    def date(self) -> datetime:
        return datetime.fromtimestamp(self.timestamp)


@dataclass
class Status:
    versions: list[Version] = field(default_factory=list)
    available: Version | None = None

    def _role(self, role: str) -> Version | None:
        return next((v for v in self.versions if v.role == role), None)

    @property
    def current(self) -> Version | None:
        return self._role("current")

    @property
    def pending(self) -> Version | None:
        return self._role("update") or self._role("rollback")

    @property
    def previous(self) -> Version | None:
        return self._role("previous")

    @property
    def rollback_pending(self) -> bool:
        return self._role("rollback") is not None

    @property
    def can_roll_back(self) -> bool:
        return self.previous is not None and not self.rollback_pending


@dataclass
class AppUpdate:
    id: str
    name: str
    version: str


def _state_file() -> Path:
    base = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state")
    return base / "lucent-settings" / "updates.json"


class Updates:
    def __init__(self, runner: Runner):
        self.r = runner

    def status(self) -> Status:
        res = self.r.run(["rpm-ostree", "status", "--json"])
        try:
            data = json.loads(res.out) if res.ok else {}
        except json.JSONDecodeError:
            data = {}
        deps = data.get("deployments") or []
        st = Status()
        booted_i = next((i for i, d in enumerate(deps) if d.get("booted")), None)
        if booted_i is None:
            return st

        def version(d: dict, role: str) -> Version:
            return Version(role, d.get("version") or d.get("checksum", "")[:10], int(d.get("timestamp", 0)),
                           d.get("checksum", ""))

        booted = deps[booted_i]
        if booted_i > 0:
            nxt = deps[0]
            newer = int(nxt.get("timestamp", 0)) >= int(booted.get("timestamp", 0))
            st.versions.append(version(nxt, "update" if nxt.get("staged") or newer else "rollback"))
        st.versions.append(version(booted, "current"))
        if booted_i + 1 < len(deps):
            st.versions.append(version(deps[booted_i + 1], "previous"))
        cached = data.get("cached-update")
        if cached and cached.get("checksum") != booted.get("checksum"):
            st.available = Version("available", cached.get("version") or "", int(cached.get("timestamp", 0)),
                                   cached.get("checksum", ""))
        return st

    def check(self) -> tuple[bool, bool, str]:
        """(worked, update_available, error). Exit 77 means "no updates"."""
        res = self.r.run(["rpm-ostree", "upgrade", "--check"], timeout=300)
        if res.code == 77:
            return True, False, ""
        if res.ok:
            return True, True, ""
        return False, False, res.message

    def apply(self) -> Result:
        """Download and stage the new version; it starts at the next restart."""
        return self.r.run(["rpm-ostree", "upgrade"], timeout=3600)

    def roll_back(self) -> Result:
        return self.r.run(["rpm-ostree", "rollback"], timeout=300)

    def reboot(self) -> Result:
        return self.r.run(dbus.call(dbus.SESSION, "org.kde.LogoutPrompt", "/LogoutPrompt",
                                    "org.kde.LogoutPrompt", "promptReboot"))

    # --- automatic downloads -------------------------------------------------
    def auto_updates(self) -> bool:
        try:
            groups = kconfig.parse(RPM_OSTREED_CONF.read_text())
        except OSError:
            return False
        return groups.get(("Daemon",), {}).get("AutomaticUpdatePolicy", "none").lower() in ("stage", "apply")

    def set_auto_updates(self, on: bool) -> Result:
        return self.r.run(["pkexec", HELPER, "auto-updates", "on" if on else "off"], timeout=180)

    # --- apps ----------------------------------------------------------------
    def flatpak_updates(self) -> list[AppUpdate]:
        res = self.r.run(["flatpak", "remote-ls", "--system", "--updates", "--app",
                          "--columns=application,name,version"], timeout=120)
        apps = []
        for line in res.out.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2 and "." in parts[0]:
                apps.append(AppUpdate(parts[0], parts[1] or parts[0], parts[2] if len(parts) > 2 else ""))
        return apps

    def flatpak_update(self) -> Result:
        return self.r.run(["flatpak", "update", "--system", "-y", "--noninteractive"], timeout=3600)

    # --- when we last looked -------------------------------------------------
    def last_check(self) -> int | None:
        try:
            return int(json.loads(_state_file().read_text())["last_check"])
        except (OSError, ValueError, KeyError):
            return None

    def remember_check(self, when: int | None = None) -> None:
        f = _state_file()
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps({"last_check": int(when if when is not None else time.time())}))
