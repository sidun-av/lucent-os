"""Where installed apps, updates and AppStream data come from, and where
install/remove/update jobs run.

`Backend` holds the state and the job queue; `FlatpakBackend` runs the real
`flatpak` / `lucent-nextgen` commands with QProcess (as the user, never as
root). `fake.FakeBackend` replaces it for the Mac preview and the GUI tests.
Jobs run one at a time, like flatpak itself would.
"""

from __future__ import annotations

import os
import platform
import shutil
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher, QObject, QProcess, QProcessEnvironment, QTimer, Signal

from . import appstream, flatpak, nextgen
from .appstream import AppInfo
from .catalog import Catalog
from .flatpak import Installed, Updates
from .i18n import _, language

APPSTREAM_MAX_AGE = 24 * 3600     # refresh Flathub's catalogue at most once a day

# The flatpak installations the store shows (system: Flathub apps; user: ArtCraft).
INSTALL_DIRS = [Path("/var/lib/flatpak"), Path.home() / ".local/share/flatpak"]
WATCH_DELAY_MS = 1500             # one `flatpak list` for a burst of changes


def watch_paths(roots: list[Path]) -> list[str]:
    """Directories that change when an app is installed or removed outside
    the store (first-boot setup, a terminal): the installation, its app/
    folder and its exported launchers. Missing ones are skipped."""
    out = []
    for root in roots:
        for p in (root, root / "app", root / "exports/share/applications"):
            if p.is_dir():
                out.append(str(p))
    return out


@dataclass
class Job:
    key: str
    action: str                   # install / remove / update
    app_ids: list[str]
    cmd: list[str] | None = None
    label: str = ""
    progress: float = 0.0
    running: bool = False
    nextgen: bool = False
    data: dict = field(default_factory=dict)


def machine_arch() -> str:
    m = platform.machine().lower()
    return {"arm64": "aarch64", "amd64": "x86_64"}.get(m, m)


class Backend(QObject):
    installedChanged = Signal()
    updatesChanged = Signal()
    appstreamChanged = Signal()
    jobsChanged = Signal()
    metadataReady = Signal(str)
    failed = Signal(str, str)          # title, detail
    finished = Signal(str, str)        # action, app name (for a short confirmation)

    def __init__(self, catalog: Catalog, parent=None):
        super().__init__(parent)
        self.catalog = catalog
        self.arch = machine_arch()
        self.installed: dict[str, Installed] = {}
        self.updates = Updates()
        self.apps: dict[str, AppInfo] = {}
        self.sizes: dict[str, tuple[str, str]] = {}
        self.metadata: dict[str, str] = {}
        self.appstream_state = "loading"       # loading / ready / missing
        self.updates_state = "idle"            # idle / checking / done / failed
        self.jobs: OrderedDict[str, Job] = OrderedDict()
        self.icon_dirs: list[Path] = []

    # --- queries used by the UI ----------------------------------------------------
    def is_installed(self, app_id: str) -> bool:
        app = self.catalog.apps.get(app_id)
        if app is not None and app.system:
            return True
        return app_id in self.installed

    def job_for(self, app_id: str) -> Job | None:
        for job in self.jobs.values():
            if app_id in job.app_ids:
                return job
        return None

    def nextgen_update(self, app_id: str) -> bool:
        """Installed ArtCraft app older than the audited version in the catalog."""
        ng = self.catalog.nextgen_app(app_id)
        inst = self.installed.get(app_id)
        return bool(ng and inst and inst.version and inst.version != ng.version.lstrip("v"))

    # --- actions ----------------------------------------------------------------------
    def install(self, app_ids: list[str], label: str = "") -> None:
        ids = [a for a in app_ids if not self.is_installed(a) and not self.job_for(a)]
        if not ids:
            return
        ng = self.catalog.nextgen_app(ids[0])
        if ng is not None:
            cmd = nextgen.install_cmd(ng, self.arch)
            if cmd is None:
                self.failed.emit(_("{name} isn't available for this computer").format(name=ng.name), "")
                return
            self._queue(Job("+".join(ids), "install", ids, cmd, label or ng.name, nextgen=True))
        else:
            self._queue(Job("+".join(ids), "install", ids, flatpak.install_cmd(ids), label))

    def remove(self, app_id: str, label: str = "") -> None:
        if self.job_for(app_id) or app_id not in self.installed:
            return
        ng = self.catalog.nextgen_app(app_id)
        if ng is not None:
            cmd = nextgen.remove_cmd(ng)
        else:
            cmd = flatpak.uninstall_cmd(app_id, self.installed[app_id].installation or "system")
        self._queue(Job(app_id, "remove", [app_id], cmd, label, nextgen=ng is not None))

    def update(self, app_ids: list[str] | None = None, label: str = "") -> None:
        ids = app_ids or [u.id for u in self.updates.apps]
        ids = [a for a in ids if not self.job_for(a)]
        ng = [a for a in ids if self.catalog.nextgen_app(a)]
        flat = [a for a in ids if a not in ng]
        if flat or (app_ids is None and self.updates.runtimes):
            self._queue(Job("update:" + "+".join(flat), "update", flat,
                            flatpak.update_cmd(flat if app_ids else None), label))
        for a in ng:
            app = self.catalog.nextgen_app(a)
            self._queue(Job("update:" + a, "update", [a], nextgen.install_cmd(app, self.arch), app.name,
                            nextgen=True))

    def _queue(self, job: Job) -> None:
        self.jobs[job.key] = job
        self.jobsChanged.emit()
        self._next()

    def _next(self) -> None:
        if any(j.running for j in self.jobs.values()) or not self.jobs:
            return
        job = next(iter(self.jobs.values()))
        job.running = True
        self.jobsChanged.emit()
        self._run(job)

    def _done(self, job: Job, ok: bool, detail: str = "") -> None:
        self.jobs.pop(job.key, None)
        if ok:
            self.finished.emit(job.action, job.label)
        else:
            titles = {"install": _("Couldn't install {name}"), "remove": _("Couldn't remove {name}"),
                      "update": _("Couldn't update {name}")}
            self.failed.emit(titles[job.action].format(name=job.label or _("the apps")), detail)
        self.jobsChanged.emit()
        self.refresh_installed()
        if job.action == "update":
            self.check_updates(refresh_appstream=False)
        self._next()

    # --- to implement -----------------------------------------------------------------------
    def start(self) -> None: ...
    def refresh_installed(self) -> None: ...
    def check_updates(self, refresh_appstream: bool = True) -> None: ...
    def load_metadata(self, app_id: str) -> None: ...
    def launch(self, app_id: str) -> None: ...
    def open_system_updates(self) -> None: ...
    def _run(self, job: Job) -> None: ...


class FlatpakBackend(Backend):
    """The real thing: flatpak's system installation plus the user's ArtCraft apps."""

    _loaded = Signal(object)            # AppStream parsed in a worker thread

    def __init__(self, catalog: Catalog, parent=None):
        super().__init__(catalog, parent)
        self._loaded.connect(self._appstream_loaded)   # queued: back on the GUI thread
        self._procs: set[QProcess] = set()
        self._env = QProcessEnvironment()
        for k, v in flatpak.cli_env(dict(os.environ)).items():
            self._env.insert(k, v)
        self.appstream_path: Path | None = None
        self._watcher: QFileSystemWatcher | None = None
        self._watch_timer = QTimer(self, singleShot=True)
        self._watch_timer.timeout.connect(self._installations_changed)

    def watch_installations(self) -> None:
        """Follow installs and removals made outside the store: on the online
        path lucent-flatpak-setup installs the default apps after the first
        login, and a store opened meanwhile showed "Install" for them for
        good."""
        self._watch_timer.setInterval(WATCH_DELAY_MS)
        self._watcher = QFileSystemWatcher(watch_paths(INSTALL_DIRS), self)
        self._watcher.directoryChanged.connect(lambda _p: self._watch_timer.start())

    def _installations_changed(self) -> None:
        if self._watcher is not None:     # folders created since (app/, exports/...)
            new = [p for p in watch_paths(INSTALL_DIRS) if p not in self._watcher.directories()]
            if new:
                self._watcher.addPaths(new)
        self.refresh_installed()

    # small helper: run a command, call back with (exit code, stdout, stderr)
    def _call(self, cmd: list[str], done, on_output=None) -> QProcess | None:
        if shutil.which(cmd[0]) is None:
            done(127, "", f"{cmd[0]}: not found")
            return None
        p = QProcess(self)
        p.setProcessEnvironment(self._env)
        out: list[str] = []
        err: list[str] = []

        def read_out():
            text = bytes(p.readAllStandardOutput()).decode("utf-8", "replace")
            out.append(text)
            if on_output:
                on_output(text)

        def read_err():
            text = bytes(p.readAllStandardError()).decode("utf-8", "replace")
            err.append(text)
            if on_output:
                on_output(text)

        def finished(code, _status):
            read_out()
            read_err()
            self._procs.discard(p)
            p.deleteLater()
            done(code, "".join(out), "".join(err))

        p.readyReadStandardOutput.connect(read_out)
        p.readyReadStandardError.connect(read_err)
        p.finished.connect(finished)
        self._procs.add(p)
        p.start(cmd[0], cmd[1:])
        return p

    def start(self) -> None:
        self.refresh_installed()
        self.watch_installations()
        self.appstream_path = appstream.find_file(appstream.SYSTEM_DIRS, flatpak.REMOTE, self.arch)
        if self.appstream_path is not None:
            self.icon_dirs = appstream.icon_dirs(self.appstream_path)
            self._load_appstream()
        else:
            self.appstream_state = "missing"
            self.appstreamChanged.emit()
        self.check_updates()

    def _load_appstream(self) -> None:
        path, lang = self.appstream_path, language()

        def work():
            self._loaded.emit(appstream.load(path, lang=lang))

        threading.Thread(target=work, daemon=True).start()

    def _appstream_loaded(self, apps: dict[str, AppInfo]) -> None:
        self.apps = apps
        self.appstream_state = "ready" if apps else "missing"
        self.appstreamChanged.emit()
        self._call(flatpak.sizes_cmd(), self._sizes_done)

    def _sizes_done(self, code, out, _err):
        if code == 0:
            self.sizes = flatpak.parse_sizes(out)
            self.appstreamChanged.emit()

    def refresh_installed(self) -> None:
        def done(code, out, _err):
            if code == 0:
                self.installed = {a.id: a for a in flatpak.parse_list(out)}
                self.installedChanged.emit()
        self._call(flatpak.list_cmd(), done)

    def check_updates(self, refresh_appstream: bool = True) -> None:
        """One trip to Flathub: refresh its app catalogue (at most daily) and
        list available updates. Nothing else in the store uses the network,
        apart from screenshots on an app's page."""
        self.updates_state = "checking"
        self.updatesChanged.emit()
        stale = (self.appstream_path is None
                 or time.time() - self.appstream_path.stat().st_mtime > APPSTREAM_MAX_AGE)

        def listed(code, out, _err):
            if code == 0:
                self.updates = flatpak.parse_updates(out)
                self.updates_state = "done"
            else:
                self.updates_state = "failed"
            self.updatesChanged.emit()

        def refreshed(code, _out, _err):
            if code == 0:
                self.appstream_path = appstream.find_file(appstream.SYSTEM_DIRS, flatpak.REMOTE, self.arch)
                if self.appstream_path is not None:
                    self.icon_dirs = appstream.icon_dirs(self.appstream_path)
                    self._load_appstream()
            self._call(flatpak.updates_cmd(), listed)

        if refresh_appstream and stale:
            self._call(flatpak.appstream_refresh_cmd(), refreshed)
        else:
            self._call(flatpak.updates_cmd(), listed)

    def load_metadata(self, app_id: str) -> None:
        if app_id in self.metadata or self.catalog.nextgen_app(app_id):
            return
        inst = self.installed.get(app_id)

        def done(code, out, _err):
            self.metadata[app_id] = out if code == 0 else ""
            self.metadataReady.emit(app_id)
        self._call(flatpak.metadata_cmd(app_id, inst.installation if inst else None), done)

    def launch(self, app_id: str) -> None:
        app = self.catalog.apps.get(app_id)
        if app is not None and app.system:
            QProcess.startDetached("kstart", ["--application", app.system])
        else:
            QProcess.startDetached("flatpak", ["run", app_id])

    def open_system_updates(self) -> None:
        for cmd in (["lucent-settings", "--page", "updates"], ["systemsettings", "kcm_updates"]):
            if shutil.which(cmd[0]) and QProcess.startDetached(cmd[0], cmd[1:])[0]:
                return

    def _run(self, job: Job) -> None:
        parser = nextgen.ProgressParser() if job.nextgen else flatpak.ProgressParser()

        def output(text: str):
            for p in parser.feed(text):
                job.progress = p if isinstance(p, float) else p.fraction
                self.jobsChanged.emit()

        def done(code, _out, err):
            self._done(job, code == 0, flatpak.error_message(err))

        if self._call(job.cmd, done, output) is None:
            return
