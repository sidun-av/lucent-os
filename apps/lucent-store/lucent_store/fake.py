"""A backend with no flatpak behind it: for the preview on a non-Linux
machine (`lucent-store --fake`) and the GUI tests.

It starts with Lucent's default apps installed and two updates waiting
(as in docs/mockups/06-store.png); jobs "run" on a timer.
"""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QTimer

from . import appstream
from .backend import Backend, Job
from .flatpak import Installed, Update, Updates
from .i18n import language

DEFAULT_APPS = ["org.onlyoffice.desktopeditors", "org.kde.okular", "com.github.jeromerobert.pdfarranger",
                "org.gimp.GIMP", "org.kde.krita", "org.mozilla.firefox", "net.scribus.Scribus"]
SIZES = {"org.onlyoffice.desktopeditors": ("372.1 MB", "1.1 GB"), "org.gimp.GIMP": ("310.4 MB", "1.2 GB"),
         "org.inkscape.Inkscape": ("92.6 MB", "301.5 MB"), "org.darktable.Darktable": ("61.3 MB", "212.8 MB"),
         "org.kde.kdenlive": ("148.0 MB", "512.4 MB")}
META = {
    "org.gimp.GIMP": "[Context]\nshared=network;ipc;\nsockets=x11;wayland;pulseaudio;\ndevices=dri;all;\n"
                     "filesystems=host;xdg-config/GIMP;\n",
    "org.inkscape.Inkscape": "[Context]\nshared=ipc;\nsockets=wayland;fallback-x11;\ndevices=dri;\n"
                             "filesystems=xdg-documents;xdg-pictures;xdg-download;\n",
}
DEFAULT_META = "[Context]\nshared=network;ipc;\nsockets=wayland;fallback-x11;pulseaudio;\ndevices=dri;\n" \
               "filesystems=home;\n"


class FakeBackend(Backend):
    def __init__(self, catalog, parent=None, appstream_path: Path | None = None, speed_ms: int = 60):
        super().__init__(catalog, parent)
        self._appstream_path = appstream_path or (Path(p) if (p := os.environ.get("LUCENT_STORE_APPSTREAM")) else None)
        icons = os.environ.get("LUCENT_STORE_ICON_DIR")
        self.icon_dirs = [Path(icons)] if icons else []
        self.speed_ms = speed_ms
        self.launched: list[str] = []
        self.opened_updates = 0

    def start(self) -> None:
        for app_id in DEFAULT_APPS:
            name = self.catalog.apps[app_id].name if app_id in self.catalog.apps else app_id
            self.installed[app_id] = Installed(app_id, name, "1.0", "stable", "flathub", "system", "")
        self.apps = appstream.load(self._appstream_path, lang=language())
        self.appstream_state = "ready" if self.apps else "missing"
        self.sizes = dict(SIZES)
        for app_id, app in self.apps.items():
            self.sizes.setdefault(app_id, ("48.2 MB", "160.3 MB"))
        self.updates = Updates([Update("org.gimp.GIMP", "GNU Image Manipulation Program", "3.2.10", "310.4 MB"),
                                Update("org.mozilla.firefox", "Firefox", "146.0.1", "88.9 MB")], runtimes=1)
        self.updates_state = "done"
        self.installedChanged.emit()
        self.appstreamChanged.emit()
        self.updatesChanged.emit()

    def refresh_installed(self) -> None:
        self.installedChanged.emit()

    def check_updates(self, refresh_appstream: bool = True) -> None:
        self.updatesChanged.emit()

    def load_metadata(self, app_id: str) -> None:
        self.metadata[app_id] = META.get(app_id, DEFAULT_META)
        self.metadataReady.emit(app_id)

    def launch(self, app_id: str) -> None:
        self.launched.append(app_id)

    def open_system_updates(self) -> None:
        self.opened_updates += 1

    def _run(self, job: Job) -> None:
        timer = QTimer(self)
        timer.setInterval(self.speed_ms)

        def tick():
            job.progress = min(1.0, job.progress + 0.05)
            self.jobsChanged.emit()
            if job.progress >= 1.0:
                timer.stop()
                timer.deleteLater()
                for app_id in job.app_ids:
                    if job.action == "remove":
                        self.installed.pop(app_id, None)
                    else:
                        name = self.apps[app_id].name if app_id in self.apps else app_id
                        self.installed[app_id] = Installed(app_id, name, "1.0", "stable", "flathub",
                                                           "user" if job.nextgen else "system", "")
                if job.action == "update":
                    done = set(job.app_ids) or {u.id for u in self.updates.apps}
                    self.updates = Updates([u for u in self.updates.apps if u.id not in done],
                                           0 if not job.app_ids else self.updates.runtimes)
                    self.updatesChanged.emit()
                self._done(job, True)

        timer.timeout.connect(tick)
        timer.start()
