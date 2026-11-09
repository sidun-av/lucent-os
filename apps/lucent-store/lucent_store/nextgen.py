"""ArtCraft's alpha apps ("Next generation · beta") via /usr/bin/lucent-nextgen.

The script downloads the app's Flatpak bundle from its GitHub release,
checks it against the release's SHA256SUMS.txt *and* the hash pinned in
catalog.toml, and installs it for the current user only. The store passes
the pinned, audited version, so a newer upstream release (which might add
features Lucent hasn't audited, e.g. AI) is never installed by the store.
"""

from __future__ import annotations

import re
from pathlib import Path

from .catalog import NextGenApp

SCRIPT = "lucent-nextgen"
SCRIPT_SOURCE = Path(__file__).resolve().parents[3] / "system_files" / "usr" / "bin" / "lucent-nextgen"


def install_cmd(app: NextGenApp, arch: str) -> list[str] | None:
    sha = app.sha256.get(arch)
    if not sha:
        return None
    return [SCRIPT, "install", "--yes", "--version", app.version, "--sha256", sha, app.key]


def remove_cmd(app: NextGenApp) -> list[str]:
    return [SCRIPT, "remove", app.key]


_PCT = re.compile(r"(\d{1,3}(?:[.,]\d+)?)\s*%")
DOWNLOAD, VERIFY, INSTALL = 0.8, 0.82, 0.85


class ProgressParser:
    """Overall 0..1 progress from the script's merged stdout/stderr."""

    def __init__(self):
        self._buf = ""
        self._stage = ""

    def feed(self, chunk: str) -> list[float]:
        self._buf += chunk.replace("\r", "\n")
        *lines, self._buf = self._buf.split("\n")
        out: list[float] = []
        for raw in lines:
            line = raw.strip()
            if not line:
                continue
            if line.startswith("Downloading"):
                self._stage = "download"
                out.append(0.0)
            elif line == "Verifying":
                self._stage = "verify"
                out.append(VERIFY)
            elif line.startswith(("Installing", "Updating")):
                self._stage = "install"
                m = _PCT.search(line)
                pct = float(m.group(1).replace(",", ".")) if m else 0.0
                out.append(round(INSTALL + (1 - INSTALL) * pct / 100, 3))
            elif line.startswith(("Installation complete", "Installed.")):
                if not out or out[-1] != 1.0:
                    out.append(1.0)
            elif self._stage == "download":
                m = _PCT.search(line)
                if m:
                    out.append(round(DOWNLOAD * float(m.group(1).replace(",", ".")) / 100, 3))
        return out
