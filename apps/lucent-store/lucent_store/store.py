"""The object QML talks to (`store`), plus `i18n` for QML's strings.

QML asks for plain lists and dicts (`store.home()`, `store.details(id)`)
and re-asks whenever `revision` changes, which happens on every change in
the backend (installed apps, a job's progress, AppStream loaded, ...).
The data is small, so rebuilding it is cheaper than keeping list models
in sync.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Property, QObject, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication, QPalette

from . import appstream, permissions, theme
from .backend import Backend
from .catalog import Catalog
from .i18n import N_, _, ngettext, pgettext
from .screenshots import ScreenshotCache

LICENSE_WORDS = {"free": N_("Free and open source"), "proprietary": N_("Proprietary"),
                 "unknown": N_("License not stated")}
ISOLATION_WORDS = {
    "good": N_("Well isolated: it can only reach what is listed here."),
    "limited": N_("Partly isolated: it can reach your files or devices."),
    "none": N_("Not isolated: it can act outside its sandbox, like a Windows program."),
}


class I18n(QObject):
    """QML's `l10n.text("...")` and `l10n.plural("{n} app", "{n} apps", n)`.
    (Not "tr": that name belongs to QObject.)"""

    @Slot(str, result=str)
    def text(self, text: str) -> str:
        return _(text)

    @Slot(str, str, result=str)
    def ctext(self, context: str, text: str) -> str:
        return pgettext(context, text)

    @Slot(str, str, int, result=str)
    def plural(self, singular: str, plural: str, n: int) -> str:
        return ngettext(singular, plural, n).format(n=n)


class Store(QObject):
    revisionChanged = Signal()
    themeChanged = Signal()
    toast = Signal(str, str, str)          # kind (error/done), title, detail
    _shotReady = Signal(str)               # from the download thread

    def __init__(self, catalog: Catalog, backend: Backend, screenshots: ScreenshotCache | None = None,
                 parent=None):
        super().__init__(parent)
        self.catalog = catalog
        self.backend = backend
        self._revision = 0
        self._dark = False
        self._shotReady.connect(self._bump)     # queued onto the GUI thread
        self.screenshots = screenshots or ScreenshotCache(on_ready=self._shotReady.emit)
        for sig in (backend.installedChanged, backend.updatesChanged, backend.appstreamChanged,
                    backend.jobsChanged, backend.metadataReady):
            sig.connect(self._bump)
        backend.failed.connect(lambda title, detail: self.toast.emit("error", title, detail))
        backend.finished.connect(self._finished)
        self.tiles = {n.id: n.key for n in catalog.nextgen}     # ArtCraft icons ship with the store
        self.update_theme()

    # --- change tracking ----------------------------------------------------------------
    def _bump(self, *_args) -> None:
        self._revision += 1
        self.revisionChanged.emit()

    @Property(int, notify=revisionChanged)
    def revision(self) -> int:
        return self._revision

    def _finished(self, action: str, name: str) -> None:
        if action == "install" and name:
            self.toast.emit("done", _("{name} is installed").format(name=name), _("Find it in the app launcher."))

    # --- theme -------------------------------------------------------------------------------
    def update_theme(self, *_args) -> None:
        forced = theme.forced_scheme()
        if forced:
            dark = forced == "dark"
        else:
            app = QGuiApplication.instance()
            dark = bool(app) and app.palette().color(QPalette.ColorRole.Window).lightness() < 128
        if dark != self._dark or not hasattr(self, "_tokens"):
            self._dark = dark
            self._tokens = theme.tokens(dark)
            self.themeChanged.emit()

    @Property(bool, notify=themeChanged)
    def dark(self) -> bool:
        return self._dark

    @Property("QVariantMap", notify=themeChanged)
    def t(self) -> dict:
        return self._tokens

    # --- small state -------------------------------------------------------------------------
    @Property(str, notify=revisionChanged)
    def appstreamState(self) -> str:
        return self.backend.appstream_state

    @Property(str, notify=revisionChanged)
    def updatesState(self) -> str:
        return self.backend.updates_state

    @Property(int, notify=revisionChanged)
    def updateCount(self) -> int:
        ng = sum(1 for n in self.catalog.nextgen if self.backend.nextgen_update(n.id))
        return self.backend.updates.count + ng

    @Property(str, constant=True)
    def catalogVersion(self) -> str:
        return self.catalog.version

    # --- per-app state -------------------------------------------------------------------------
    def _state(self, app_ids: list[str]) -> tuple[str, float]:
        for a in app_ids:
            job = self.backend.job_for(a)
            if job is not None:
                if not job.running:
                    return "queued", 0.0
                return {"install": "installing", "remove": "removing", "update": "updating"}[job.action], job.progress
        system = all(self.catalog.apps.get(a) is not None and self.catalog.apps[a].system for a in app_ids)
        if system:
            return "system", 0.0
        if all(self.backend.is_installed(a) for a in app_ids):
            return "installed", 0.0
        return "available", 0.0

    def _name(self, app_id: str) -> str:
        if app_id in self.catalog.apps:
            return self.catalog.apps[app_id].name if not self.catalog.apps[app_id].system \
                else _(self.catalog.apps[app_id].name)
        ng = self.catalog.nextgen_app(app_id)
        if ng:
            return ng.name
        info = self.backend.apps.get(app_id)
        if info:
            return info.name
        inst = self.backend.installed.get(app_id)
        return inst.name if inst and inst.name else app_id

    def _summary(self, app_id: str) -> str:
        if app_id in self.catalog.apps:
            return _(self.catalog.apps[app_id].summary)
        ng = self.catalog.nextgen_app(app_id)
        if ng:
            return _(ng.description)
        info = self.backend.apps.get(app_id)
        return info.summary if info else ""

    def _available_here(self, app_id: str) -> bool:
        """Hide catalog apps Flathub doesn't build for this CPU (e.g. Steam on ARM)."""
        app = self.catalog.apps.get(app_id)
        if (app and app.system) or self.backend.is_installed(app_id) or self.backend.appstream_state != "ready":
            return True
        return app_id in self.backend.apps

    def _app(self, app_id: str) -> dict:
        state, progress = self._state([app_id])
        info = self.backend.apps.get(app_id)
        return {
            "id": app_id, "name": self._name(app_id), "summary": self._summary(app_id),
            "icon": "image://app/" + app_id, "state": state, "progress": progress,
            "verified": bool(info and info.verified),
            "license": _(LICENSE_WORDS[appstream.license_kind(info.license)]) if info else "",
            "free": bool(info) and appstream.license_kind(info.license) == "free",
            "hasUpdate": any(u.id == app_id for u in self.backend.updates.apps) or self.backend.nextgen_update(app_id),
        }

    # --- pages -------------------------------------------------------------------------------------
    @Slot(int, result="QVariantList")
    def home(self, _rev: int = 0) -> list:
        out = []
        for r in self.catalog.replacements:
            if not all(self._available_here(a) for a in r.apps):
                continue
            state, progress = self._state(list(r.apps))
            icons = ["image://app/tile:" + r.icon] if r.icon else ["image://app/" + a for a in r.apps]
            name = r.name if " + " in r.name or r.name in {self.catalog.apps[a].name for a in r.apps} \
                else _(r.name)
            out.append({"windows": r.windows, "name": name, "description": _(r.description),
                        "note": _(r.note) if r.note else "", "icons": icons, "appIds": list(r.apps),
                        "state": state, "progress": progress})
        return out

    @Slot(result="QVariantList")
    def categories(self) -> list:
        return [{"id": c.id, "name": _(c.name), "icon": c.icon} for c in self.catalog.categories]

    @Slot(str, int, result="QVariantMap")
    def category(self, cid: str, _rev: int = 0) -> dict:
        c = self.catalog.category(cid)
        if c is None:
            return {}
        return {"id": c.id, "name": _(c.name), "description": _(c.description), "icon": c.icon,
                "apps": [self._app(a) for a in c.apps if self._available_here(a)]}

    @Slot(str, int, result="QVariantList")
    def search(self, query: str, _rev: int = 0) -> list:
        if self.backend.apps:
            hits = [a.id for a in appstream.search(self.backend.apps, query, self.catalog)]
        else:   # no AppStream yet: at least the curated apps
            q = appstream.fold(query).strip()
            hits = [a for a in self.catalog.apps if len(q) >= 2 and (
                q in appstream.fold(self._name(a)) or q in appstream.fold(self._summary(a)))]
        return [self._app(a) for a in hits]

    @Slot(int, result="QVariantList")
    def installed(self, _rev: int = 0) -> list:
        out = []
        for inst in sorted(self.backend.installed.values(), key=lambda i: self._name(i.id).lower()):
            d = self._app(inst.id)
            d["size"] = inst.size
            d["version"] = inst.version
            d["user"] = inst.installation == "user"
            out.append(d)
        return out

    @Slot(int, result="QVariantList")
    def updates(self, _rev: int = 0) -> list:
        out = []
        for u in self.backend.updates.apps:
            d = self._app(u.id)
            d.update({"version": u.version, "download": u.download})
            out.append(d)
        for n in self.catalog.nextgen:
            if self.backend.nextgen_update(n.id):
                d = self._app(n.id)
                d.update({"version": n.version.lstrip("v"), "download": ""})
                out.append(d)
        return out

    @Slot(int, result=int)
    def sharedUpdates(self, _rev: int = 0) -> int:
        return self.backend.updates.runtimes

    @Slot(int, result="QVariantList")
    def nextgen(self, _rev: int = 0) -> list:
        out = []
        for n in self.catalog.nextgen:
            d = self._app(n.id)
            d.update({"key": n.key, "icon": "image://app/tile:" + n.key, "version": n.version,
                      "supported": n.sha256.get(self.backend.arch) is not None})
            out.append(d)
        return out

    @Slot(str, int, result="QVariantMap")
    def details(self, app_id: str, _rev: int = 0) -> dict:
        d = self._app(app_id)
        info = self.backend.apps.get(app_id)
        ng = self.catalog.nextgen_app(app_id)
        cat_app = self.catalog.apps.get(app_id)
        inst = self.backend.installed.get(app_id)
        dl, inst_size = self.backend.sizes.get(app_id, ("", ""))
        d.update({
            "nextgen": ng is not None, "system": bool(cat_app and cat_app.system),
            "developer": info.developer if info else ("ArtCraft" if ng else ""),
            "description": info.description if info else "",
            "licenseCode": info.license if info else ("Apache-2.0" if ng else ""),
            "version": (inst.version if inst and inst.version else (info.version if info else "")) or
                       (ng.version.lstrip("v") if ng else ""),
            "download": dl, "installedSize": inst.size if inst and inst.size else inst_size,
            "homepage": info.homepage if info else (f"https://github.com/{ng.repo}" if ng else ""),
            "screenshots": [], "permissions": [], "isolation": "", "isolationText": "",
            "user": bool(inst and inst.installation == "user"),
        })
        if ng is not None:
            d["license"] = _(LICENSE_WORDS["free"])
            d["free"] = True
        if info:
            for shot in info.screenshots[:6]:
                path = self.screenshots.get(shot.url)
                d["screenshots"].append({"source": QUrl.fromLocalFile(str(path)).toString() if path else "",
                                         "caption": shot.caption})
        meta = self.backend.metadata.get(app_id)
        if meta is None and not ng and not d["system"]:
            # Not while QML is evaluating this binding: the answer bumps `revision`.
            QTimer.singleShot(0, lambda: self.backend.load_metadata(app_id))
        elif meta:
            d["permissions"] = [{"text": p.text, "icon": p.icon, "level": p.level}
                                for p in permissions.describe(meta)]
            iso = permissions.isolation(meta)
            d["isolation"] = iso
            d["isolationText"] = _(ISOLATION_WORDS[iso])
        return d

    # --- actions ---------------------------------------------------------------------------------
    @Slot("QVariantList", str)
    def install(self, app_ids: list, label: str = "") -> None:
        ids = [str(a) for a in app_ids]
        self.backend.install(ids, label or " + ".join(self._name(a) for a in ids))

    @Slot(str)
    def remove(self, app_id: str) -> None:
        self.backend.remove(app_id, self._name(app_id))

    @Slot(str)
    def update(self, app_id: str) -> None:
        self.backend.update([app_id], self._name(app_id))

    @Slot()
    def updateAll(self) -> None:
        self.backend.update(None, _("the updates"))

    @Slot()
    def checkUpdates(self) -> None:
        self.backend.check_updates()

    @Slot(str)
    def launch(self, app_id: str) -> None:
        self.backend.launch(app_id)

    @Slot()
    def openSystemUpdates(self) -> None:
        self.backend.open_system_updates()

    @Slot(str, result=str)
    def fold(self, text: str) -> str:
        return appstream.fold(text)


def qml_dir() -> Path:
    return Path(__file__).parent / "qml"
