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

import hashlib
import json
import os
import platform
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .. import dbus, kconfig
from ..run import Result, Runner

RPM_OSTREED_CONF = Path("/etc/rpm-ostreed.conf")
HELPER = "/usr/libexec/lucent/settings-helper"
GOARCH = {"x86_64": "amd64", "aarch64": "arm64", "arm64": "arm64", "amd64": "amd64"}


def registry_ref(origin: str) -> str | None:
    """'ostree-unverified-registry:ghcr.io/x:tag' -> 'docker://ghcr.io/x:tag';
    None for an origin that is not a registry (oci dir, local storage)."""
    if not origin:
        return None
    if "docker://" in origin:
        return "docker://" + origin.split("docker://", 1)[1]
    for prefix in ("ostree-unverified-registry:", "ostree-image-signed:registry:",
                   "ostree-remote-registry:"):
        if origin.startswith(prefix):
            rest = origin[len(prefix):]
            if prefix == "ostree-remote-registry:":
                rest = rest.split(":", 1)[1]
            return "docker://" + rest
    return None


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
    def __init__(self, runner: Runner, machine: str | None = None):
        self.r = runner
        self.machine = machine or platform.machine()

    def _status_json(self) -> dict:
        res = self.r.run(["rpm-ostree", "status", "--json"])
        try:
            return json.loads(res.out) if res.ok else {}
        except json.JSONDecodeError:
            return {}

    def status(self) -> Status:
        data = self._status_json()
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
        seen = self._state().get("available")
        on_disk = {d.get("container-image-reference-digest") for d in deps}
        if st.available is None and seen and seen not in on_disk:
            st.available = Version("available", "", 0, seen)
        return st

    def check(self) -> tuple[bool, bool, str]:
        """(worked, update_available, error).

        For a registry image the registry's manifest digest for this CPU is
        compared with the digests of the versions on disk (rpm-ostree's own
        --check is unreliable for container images: coreos/rpm-ostree#1579).
        Otherwise rpm-ostree decides (exit 77 = no updates)."""
        data = self._status_json()
        deps = data.get("deployments") or []
        booted = next((d for d in deps if d.get("booted")), {})
        ref = registry_ref(booted.get("container-image-reference", ""))
        if ref is None:
            res = self.r.run(["rpm-ostree", "upgrade", "--check"], timeout=300)
            if res.code == 77:
                return True, False, ""
            return (True, True, "") if res.ok else (False, False, res.message)
        res = self.r.run(["skopeo", "inspect", "--raw", ref], timeout=90)
        if not res.ok:
            return False, False, res.message
        digest = self._arch_digest(res.out)
        if not digest:
            return False, False, "no image for this processor"
        on_disk = {d.get("container-image-reference-digest") for d in deps}
        available = digest not in on_disk
        self._save_state(available=digest if available else "")
        return True, available, ""

    def _arch_digest(self, raw: str) -> str:
        try:
            doc = json.loads(raw)
        except json.JSONDecodeError:
            return ""
        if "manifests" in doc:  # an index (multi-arch tag): this CPU's entry
            want = GOARCH.get(self.machine, self.machine)
            for m in doc["manifests"]:
                if m.get("platform", {}).get("architecture") == want:
                    return m.get("digest", "")
            return ""
        return "sha256:" + hashlib.sha256(raw.encode()).hexdigest()

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

    # --- what we saw last time -----------------------------------------------
    def _state(self) -> dict:
        try:
            return json.loads(_state_file().read_text())
        except (OSError, ValueError):
            return {}

    def _save_state(self, **kw) -> None:
        f = _state_file()
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps({**self._state(), **kw}))

    def last_check(self) -> int | None:
        try:
            return int(self._state()["last_check"])
        except (KeyError, TypeError, ValueError):
            return None

    def remember_check(self, when: int | None = None) -> None:
        self._save_state(last_check=int(when if when is not None else time.time()))
