"""flatpak command lines, their output, and install progress.

The store drives the `flatpak` CLI as the logged-in user. System-wide
operations go through flatpak's own system helper, so polkit decides: on
Fedora an active local admin (`wheel`) installs, updates and removes
Flathub apps without a password, anyone else gets Plasma's password
prompt. That is why no command here uses `--noninteractive` (it forbids
the prompt) and none uses sudo/pkexec: the store never runs as root.

Output is parsed in the C.UTF-8 locale. With stdout not a terminal,
flatpak prints one plain line per progress update, e.g.
`Installing 2/3… ████▍               22%  3.4 MB/s  00:15`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

FLATPAK = "flatpak"
REMOTE = "flathub"


def _clean(s: str) -> str:
    return s.replace(" ", " ").strip()


# --- commands -------------------------------------------------------------------

def install_cmd(app_ids: list[str], remote: str = REMOTE) -> list[str]:
    return [FLATPAK, "install", "--system", "-y", "--or-update", remote, *app_ids]


def uninstall_cmd(app_id: str, installation: str = "system") -> list[str]:
    return [FLATPAK, "uninstall", f"--{installation}", "-y", app_id]


def update_cmd(app_ids: list[str] | None = None) -> list[str]:
    return [FLATPAK, "update", "--system", "-y", *(app_ids or [])]


def appstream_refresh_cmd(remote: str = REMOTE) -> list[str]:
    return [FLATPAK, "update", "--system", "--appstream", remote]


def list_cmd() -> list[str]:
    return [FLATPAK, "list", "--app", "--columns=application,name,version,branch,origin,installation,size"]


def updates_cmd() -> list[str]:
    return [FLATPAK, "remote-ls", "--system", "--updates", "--columns=ref,name,version,download-size"]


def sizes_cmd(remote: str = REMOTE) -> list[str]:
    """Download/installed sizes of every app, from flatpak's local cache (no network)."""
    return [FLATPAK, "remote-ls", "--system", "--cached", "--app",
            "--columns=application,download-size,installed-size", remote]


def metadata_cmd(app_id: str, installation: str | None = None, remote: str = REMOTE) -> list[str]:
    """The app's sandbox metadata: from the installed app, else the cached remote summary."""
    if installation:
        return [FLATPAK, "info", f"--{installation}", "--show-metadata", app_id]
    return [FLATPAK, "remote-info", "--system", "--cached", "--show-metadata", remote, app_id]


def cli_env(environ: dict[str, str]) -> dict[str, str]:
    env = {k: v for k, v in environ.items() if k not in ("LANGUAGE", "LC_MESSAGES")}
    env["LC_ALL"] = "C.UTF-8"
    return env


# --- output -----------------------------------------------------------------------

@dataclass(frozen=True)
class Installed:
    id: str
    name: str
    version: str
    branch: str
    origin: str
    installation: str
    size: str


def _rows(out: str, n: int) -> list[list[str]]:
    rows = []
    for line in out.splitlines():
        if not line.strip():
            continue
        cols = [_clean(c) for c in line.split("\t")]
        rows.append((cols + [""] * n)[:n])
    return rows


def parse_list(out: str) -> list[Installed]:
    return [Installed(*row) for row in _rows(out, 7) if row[0]]


@dataclass(frozen=True)
class Update:
    id: str
    name: str
    version: str
    download: str


@dataclass
class Updates:
    apps: list[Update] = field(default_factory=list)
    runtimes: int = 0       # shared parts (runtimes, translations, drivers)

    @property
    def count(self) -> int:
        return len(self.apps)


def parse_updates(out: str) -> Updates:
    ups = Updates()
    for ref, name, version, download in _rows(out, 4):
        kind, _, rest = ref.partition("/")
        app_id = rest.split("/")[0]
        if kind == "app" and app_id:
            ups.apps.append(Update(app_id, name, version, download))
        elif kind == "runtime":
            ups.runtimes += 1
    return ups


def parse_sizes(out: str) -> dict[str, tuple[str, str]]:
    return {app_id: (dl, inst) for app_id, dl, inst in _rows(out, 3) if app_id}


def error_message(stderr: str) -> str:
    """The line worth showing a person when flatpak fails."""
    lines = [_clean(line) for line in stderr.replace("\r", "\n").splitlines() if line.strip()]
    for line in reversed(lines):
        if line.lower().startswith("error:"):
            return line.split(":", 1)[1].strip()
    return lines[-1] if lines else ""


# --- progress ---------------------------------------------------------------------

_VERBS = {"Installing": "install", "Updating": "update", "Uninstalling": "uninstall"}
_STEP = re.compile(r"^(Installing|Updating|Uninstalling)(?: (\d+)/(\d+))?(?:…|\.\.\.)(.*)$")
_PCT = re.compile(r"(\d{1,3})%")


@dataclass(frozen=True)
class Progress:
    action: str     # install / update / uninstall
    step: int
    steps: int
    percent: int

    @property
    def fraction(self) -> float:
        """Overall progress of the whole transaction, 0..1."""
        steps = max(self.steps, 1)
        return min(1.0, ((self.step - 1) + self.percent / 100) / steps)


class ProgressParser:
    """Feed it raw chunks of flatpak's stdout; get Progress for each full line."""

    def __init__(self):
        self._buf = ""

    def feed(self, chunk: str) -> list[Progress]:
        self._buf += chunk.replace("\r", "\n")
        *lines, self._buf = self._buf.split("\n")
        out = []
        for line in lines:
            m = _STEP.match(line.strip())
            if not m:
                continue
            verb, step, steps, rest = m.groups()
            pct = _PCT.search(rest)
            out.append(Progress(_VERBS[verb], int(step or 1), int(steps or 1),
                                min(100, int(pct.group(1))) if pct else 0))
        return out
