"""One QObject per Settings page: state for QML (`s`, a plain map) and slots
for its actions. All system calls run in the background (tasks.run); a page
shows `busy` while one runs and `error` if it failed, in plain words."""

from __future__ import annotations

import os
import platform
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlparse

from PySide6.QtCore import Property, QDateTime, QLocale, QObject, QTimer, Signal, Slot

from . import tasks
from .backends import about, appearance, bluetooth, display, habits, network, sound, updates, users, winapps
from .i18n import N_, _, language, ngettext
from .run import Result, Runner


def local_path(url_or_path: str) -> str:
    if url_or_path.startswith("file:"):
        return unquote(urlparse(url_or_path).path)
    return url_or_path


def locale() -> QLocale:
    return QLocale(language())


def nice_date(ts: int) -> str:
    """'November 9, 2026' in English; the format itself is a translated string."""
    if not ts:
        return ""
    dt = QDateTime.fromSecsSinceEpoch(int(ts))
    return locale().toString(dt.date(), _("MMMM d, yyyy"))


def when(ts: int | None) -> str:
    """'today, 09:14', 'yesterday, 18:02', or a date."""
    if not ts:
        return _("never")
    dt = datetime.fromtimestamp(ts)
    days = (datetime.now().date() - dt.date()).days
    clock = locale().toString(QDateTime.fromSecsSinceEpoch(int(ts)).time(), QLocale.FormatType.ShortFormat)
    if days == 0:
        return _("today, {time}").format(time=clock)
    if days == 1:
        return _("yesterday, {time}").format(time=clock)
    return nice_date(ts)


class Section(QObject):
    changed = Signal()
    toast = Signal(str)

    def __init__(self, runner: Runner, parent=None):
        super().__init__(parent)
        self.r = runner
        self._s: dict = {}
        self._busy = ""
        self._error = ""

    def _get_s(self):
        return self._s

    def _get_busy(self):
        return self._busy

    def _get_error(self):
        return self._error

    s = Property("QVariantMap", _get_s, notify=changed)
    busy = Property(str, _get_busy, notify=changed)
    error = Property(str, _get_error, notify=changed)

    def set(self, **kw) -> None:
        self._s = {**self._s, **kw}
        self.changed.emit()

    def task(self, busy: str, fn, done=None, failed: str = "") -> None:
        """Run fn in the background; failed is the plain-words error prefix."""
        self._busy, self._error = busy, ""
        self.changed.emit()

        def finish(result):
            self._busy = ""
            if isinstance(result, Exception):
                self._error = f"{failed} ({result})" if failed else str(result)
            elif isinstance(result, Result) and not result.ok and failed:
                self._error = f"{failed} {result.message}".strip()
            self.changed.emit()
            if done is not None:
                done(result)

        tasks.run(fn, finish)

    @Slot()
    def clearError(self):
        self._error = ""
        self.changed.emit()

    @Slot()
    def refresh(self):
        pass


# ---------------------------------------------------------------------------
class NetworkSection(Section):
    def __init__(self, runner, parent=None):
        super().__init__(runner, parent)
        self.b = network.Network(runner)
        self.set(wifiHardware=False, wifiEnabled=False, current="", wired=[], wifiDevice="", networks=[],
                 scanned=False, loaded=False)

    def _apply_state(self, st: network.State):
        wifi = next((d for d in st.devices if d.kind == "wifi"), None)
        wired = [{"name": d.name, "connected": d.connected, "connection": d.connection,
                  "unplugged": d.state == "unavailable"} for d in st.devices if d.kind == "ethernet"]
        wifi_name = wifi.connection if wifi and wifi.connected else ""
        side = wifi_name or (_("Cable") if st.wired_connected else (_("Off") if wifi and not st.wifi_enabled else ""))
        self.set(wifiHardware=st.wifi_hardware and wifi is not None, wifiEnabled=st.wifi_enabled,
                 current=st.current, wifiCurrent=wifi_name, sideValue=side, wired=wired,
                 wifiDevice=wifi.name if wifi else "", loaded=True)

    @Slot()
    def refresh(self):
        tasks.run(self.b.state, lambda st: isinstance(st, network.State) and self._apply_state(st))

    @Slot()
    def scan(self):
        if not self._s.get("wifiHardware") or not self._s.get("wifiEnabled"):
            return

        def done(nets):
            if isinstance(nets, list):
                self.set(networks=[{"ssid": n.ssid, "bars": network.signal_bars(n.signal), "secure": n.secure,
                                    "active": n.active, "known": n.known, "enterprise": n.enterprise}
                                   for n in nets], scanned=True)
        self.task("scan", lambda: self.b.scan(rescan=True), done)

    @Slot(bool)
    def setWifi(self, on):
        self.set(wifiEnabled=on)
        self.task("wifi", lambda: self.b.set_wifi(on), lambda _r: (self.refresh(), on and QTimer.singleShot(1500, self.scan)),
                  _("Couldn't switch Wi-Fi."))

    @Slot(str, str, bool)
    def connectTo(self, ssid, password, known):
        def done(res):
            self.refresh()
            self.scan()
        self.task("connect:" + ssid, lambda: self.b.connect(ssid, password or None, known=known), done,
                  _("Couldn't connect to “{name}”.").format(name=ssid))

    @Slot(str)
    def disconnectDevice(self, device):
        self.task("disconnect:" + device, lambda: self.b.device_disconnect(device),
                  lambda _r: (self.refresh(), self.scan()), _("Couldn't disconnect."))

    @Slot(str)
    def connectDevice(self, device):
        self.task("connect:" + device, lambda: self.b.device_connect(device), lambda _r: self.refresh(),
                  _("Couldn't connect."))

    @Slot()
    def openAdvanced(self):
        self.r.spawn(["systemsettings", "kcm_networkmanagement"])


# ---------------------------------------------------------------------------
class BluetoothSection(Section):
    def __init__(self, runner, parent=None):
        super().__init__(runner, parent)
        self.b = bluetooth.Bluetooth(runner)
        self.set(available=False, powered=False, discovering=False, paired=[], nearby=[], loaded=False, adapter="")

    def _apply(self, st):
        if not isinstance(st, bluetooth.State):
            return

        def dev(d: bluetooth.Device):
            return {"path": d.path, "name": d.name, "connected": d.connected, "kind": d.kind,
                    "battery": -1 if d.battery is None else d.battery}
        self.set(available=st.adapter is not None, adapter=st.adapter or "", powered=st.powered,
                 discovering=st.discovering, paired=[dev(d) for d in st.devices if d.paired],
                 nearby=[dev(d) for d in st.devices if not d.paired], loaded=True)

    @Slot()
    def refresh(self):
        tasks.run(self.b.state, self._apply)

    @Slot(bool)
    def setPowered(self, on):
        adapter = self._s.get("adapter")
        if adapter:
            self.set(powered=on)
            self.task("power", lambda: self.b.set_powered(adapter, on), lambda _r: self.refresh(),
                      _("Couldn't switch Bluetooth."))

    @Slot(bool)
    def setDiscovering(self, on):
        adapter = self._s.get("adapter")
        if adapter and self._s.get("powered") and on != self._s.get("discovering"):
            tasks.run(lambda: self.b.discover(adapter, on), lambda _r: self.refresh())

    @Slot(str)
    def pair(self, path):
        self.task("pair:" + path, lambda: self.b.pair(path), lambda _r: self.refresh(),
                  _("Pairing didn't work. Make sure the device is in pairing mode and close by."))

    @Slot(str)
    def connectDevice(self, path):
        self.task("connect:" + path, lambda: self.b.connect(path), lambda _r: self.refresh(),
                  _("Couldn't connect. Is the device switched on and close by?"))

    @Slot(str)
    def disconnectDevice(self, path):
        self.task("disconnect:" + path, lambda: self.b.disconnect(path), lambda _r: self.refresh())

    @Slot(str)
    def forget(self, path):
        adapter = self._s.get("adapter")
        self.task("forget:" + path, lambda: self.b.forget(adapter, path), lambda _r: self.refresh())


# ---------------------------------------------------------------------------
class DisplaySection(Section):
    REVERT_SECONDS = 15

    def __init__(self, runner, parent=None):
        super().__init__(runner, parent)
        self.b = display.Display(runner)
        self._revert_to: tuple[str, str] | None = None
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        self.set(outputs=[], night=False, nightAvailable=False, confirm=0, loaded=False)

    def _load(self):
        return self.b.outputs(), self.b.night_light()

    def _apply(self, res):
        if isinstance(res, Exception):
            return
        outs, (night, available) = res
        rows = []
        for o in outs:
            rec = display.recommended_scale(o.width, o.height, o.width_mm)
            rows.append({"name": o.name, "width": o.width, "height": o.height, "scale": o.scale,
                         "currentMode": next((m.id for m in o.modes if (m.width, m.height) == o.current_size),
                                             o.current_mode),
                         "modes": [{"id": m.id, "label": f"{m.width} × {m.height}",
                                    "size": f"{m.width}x{m.height}"} for m in o.modes],
                         "recommendedScale": rec})
        self.set(outputs=rows, night=night, nightAvailable=available, loaded=True)

    @Slot()
    def refresh(self):
        tasks.run(self._load, self._apply)

    @Slot(str, str)
    def setMode(self, output, mode_id):
        out = next((o for o in self._s["outputs"] if o["name"] == output), None)
        if out is None or out["currentMode"] == mode_id:
            return
        previous = out["currentMode"]

        def done(res):
            if isinstance(res, Result) and res.ok:
                self._revert_to = (output, previous)
                self.set(confirm=self.REVERT_SECONDS)
                self._timer.start()
            self.refresh()
        self.task("mode", lambda: self.b.set_mode(output, mode_id), done, _("Couldn't change the resolution."))

    def _tick(self):
        left = self._s.get("confirm", 0) - 1
        if left <= 0:
            self.revert()
        else:
            self.set(confirm=left)

    @Slot()
    def keep(self):
        self._timer.stop()
        self._revert_to = None
        self.set(confirm=0)

    @Slot()
    def revert(self):
        self._timer.stop()
        self.set(confirm=0)
        if self._revert_to:
            output, mode_id = self._revert_to
            self._revert_to = None
            self.task("mode", lambda: self.b.set_mode(output, mode_id), lambda _r: self.refresh())

    @Slot(str, float)
    def setScale(self, output, scale):
        self.task("scale", lambda: self.b.set_scale(output, scale), lambda _r: self.refresh(),
                  _("Couldn't change the scale."))

    @Slot(bool)
    def setNight(self, on):
        self.set(night=on)
        self.task("night", lambda: self.b.set_night_light(on), lambda _r: QTimer.singleShot(800, self.refresh))


# ---------------------------------------------------------------------------
class SoundSection(Section):
    def __init__(self, runner, parent=None):
        super().__init__(runner, parent)
        self.b = sound.Sound(runner)
        self._pending: dict[str, int] = {}
        self.set(outputs=[], inputs=[], output={}, input={}, noHardware=True, loaded=False)

    def _apply(self, st):
        if not isinstance(st, sound.State):
            return

        def dev(d):
            label = _("No sound device") if d.virtual else d.label
            return {"name": d.name, "label": label, "volume": d.volume, "muted": d.muted, "default": d.default}
        out = dev(st.output) if st.output else {}
        inp = dev(st.input) if st.input else {}
        # don't fight the slider while the person is dragging it
        for kind, d in (("output", out), ("input", inp)):
            if kind in self._pending and d:
                d["volume"] = self._pending[kind]
        self.set(outputs=[dev(d) for d in st.outputs], inputs=[dev(d) for d in st.inputs], output=out, input=inp,
                 noHardware=st.no_hardware, loaded=True)

    @Slot()
    def refresh(self):
        tasks.run(self.b.state, self._apply)

    @Slot(str, int)
    def setVolume(self, kind, value):
        self._pending[kind] = value
        d = dict(self._s.get(kind) or {})
        d["volume"] = value
        self.set(**{kind: d})

        def done(_r):
            self._pending.pop(kind, None)
        tasks.run(lambda: self.b.set_volume(kind, value), done)

    @Slot(str, bool)
    def setMuted(self, kind, muted):
        tasks.run(lambda: self.b.set_muted(kind, muted), lambda _r: self.refresh())

    @Slot(str, str)
    def setDefault(self, kind, name):
        tasks.run(lambda: self.b.set_default(kind, name), lambda _r: self.refresh())


# ---------------------------------------------------------------------------
def wall_tiles(walls, current: str) -> list[dict]:
    """The Appearance page's row: the wallpaper in use (day and night, if it
    has both), Lucent's own, then the person's pictures, then the rest."""
    current = current.rstrip("/")
    order = sorted(walls, key=lambda w: (w.path.rstrip("/") != current, w.name != "Lucent", w.ours))
    tiles = []
    for w in order:
        if w.thumbnail_dark:
            tiles.append({"path": w.path, "name": w.name, "thumb": "file://" + w.thumbnail, "variant": "day"})
            tiles.append({"path": w.path, "name": w.name, "thumb": "file://" + w.thumbnail_dark, "variant": "night"})
        else:
            tiles.append({"path": w.path, "name": w.name, "thumb": "file://" + w.thumbnail,
                          "variant": "" if w.ours else "picture"})
    return tiles


class AppearanceSection(Section):
    def __init__(self, runner, parent=None):
        super().__init__(runner, parent)
        self.b = appearance.Appearance(runner)
        self.set(mode="light", accent=appearance.ACCENTS[0], accents=appearance.ACCENTS, wallpaper="",
                 wallpaperThumb="", wallpaperName="", wallpapers=[], wallTiles=[], animations="fast", textSize=11,
                 textSizes=appearance.TEXT_SIZES, loaded=False)

    def _load(self):
        walls = self.b.wallpapers()
        current = self.b.current_wallpaper()
        return dict(mode=self.b.mode(), accent=self.b.accent(), animations=self.b.animations(),
                    textSize=self.b.text_size(), walls=walls, current=current)

    def _apply(self, d):
        if isinstance(d, Exception):
            return
        walls = d.pop("walls")
        current = d.pop("current")
        cur = next((w for w in walls if w.path.rstrip("/") == current.rstrip("/")), None)
        name = cur.name if cur else Path(current).stem
        self.set(**d, wallpaper=current,
                 wallpaperThumb=("file://" + (cur.thumbnail if cur else appearance.thumbnail(current)))
                 if (cur or appearance.thumbnail(current)) else "",
                 wallpaperThumbDark=("file://" + appearance.thumbnail(current, dark=True))
                 if appearance.thumbnail(current, dark=True) else "",
                 wallpaperName=name, wallpaperOurs=bool(cur and cur.ours),
                 wallpapers=[{"path": w.path, "name": w.name, "thumb": "file://" + w.thumbnail, "ours": w.ours}
                             for w in walls], wallTiles=wall_tiles(walls, current), loaded=True)

    @Slot()
    def refresh(self):
        tasks.run(self._load, self._apply)

    @Slot(str)
    def setMode(self, mode):
        if mode == self._s.get("mode"):
            return
        self.set(mode=mode)
        self.task("mode", lambda: self.b.set_mode(mode), lambda _r: self.refresh(), _("Couldn't change the theme."))

    @Slot(str)
    def setAccent(self, color):
        self.set(accent=color)
        self.task("accent", lambda: self.b.set_accent(color), None, _("Couldn't change the accent colour."))

    @Slot(str)
    def setWallpaper(self, path):
        path = local_path(path)
        self.task("wallpaper", lambda: self.b.set_wallpaper(path), lambda _r: self.refresh(),
                  _("Couldn't change the wallpaper."))

    @Slot(str)
    def setAnimations(self, speed):
        self.set(animations=speed)
        tasks.run(lambda: self.b.set_animations(speed))

    @Slot(int)
    def setTextSize(self, points):
        if points == self._s.get("textSize"):
            return
        self.set(textSize=points)
        self.task("text", lambda: self.b.set_text_size(points))


# ---------------------------------------------------------------------------
class UsersSection(Section):
    nameSaved = Signal()
    passwordChanged = Signal()

    def __init__(self, runner, parent=None, backend: users.Users | None = None):
        super().__init__(runner, parent)
        self.b = backend or users.Users(runner)
        self._path = ""
        self.set(name="", login="", admin=False, icon="", initials="?", version=0, loaded=False)

    def _apply(self, me):
        if not isinstance(me, users.Me):
            return
        self._path = me.path
        icon = me.icon if me.icon and os.access(me.icon, os.R_OK) else ""
        self.set(name=me.display_name, realName=me.real_name, login=me.login, admin=me.admin,
                 # a new version in the URL makes QML load the replaced file again
                 icon=f"file://{icon}?v={int(time.time() * 1000)}" if icon else "",
                 initials=users.initials(me.display_name), loaded=True)

    @Slot()
    def refresh(self):
        tasks.run(self.b.me, self._apply)

    @Slot(str)
    def setName(self, name):
        name = name.strip()
        if not self._path or not name or name == self._s.get("realName"):
            return

        def done(res):
            if isinstance(res, Result) and res.ok:
                self.nameSaved.emit()
            self.refresh()
        self.task("name", lambda: self.b.set_real_name(self._path, name), done, _("The name wasn't changed."))

    @Slot(str)
    def setPicture(self, url):
        path = local_path(url)
        self.task("picture", lambda: self.b.set_icon(self._path, path), lambda _r: self.refresh(),
                  _("The picture wasn't changed."))

    @Slot()
    def useInitials(self):
        from .avatar import initials_png
        out = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "lucent-settings" / "initials.png"
        initials_png(self._s.get("initials", "?"), out)
        self.setPicture(str(out))

    @Slot(str, str, result=str)
    def setPassword(self, new, again):
        problem = users.password_problem(new, again)
        if problem == "empty":
            return _("Type the new password.")
        if problem == "mismatch":
            return _("The two passwords are different.")
        if problem == "short":
            return _("Use at least {n} characters.").format(n=users.MIN_LENGTH)

        def done(res):
            if isinstance(res, tuple) and res[0]:
                self.passwordChanged.emit()
                self.toast.emit(_("Password changed."))
            else:
                msg = res[1] if isinstance(res, tuple) else str(res)
                if "NotAuthorized" in msg or "not authorized" in msg.lower() or "dismissed" in msg.lower():
                    self._error = _("The password wasn't changed: confirming with your current password was cancelled or failed.")
                else:
                    self._error = _("The password wasn't changed.") + (f" ({msg})" if msg else "")
                self.changed.emit()
        self.task("password", lambda: self.b.set_password(self._path, new), done)
        return ""

    @Slot()
    def openAdvanced(self):
        self.r.spawn(["systemsettings", "kcm_users"])


# ---------------------------------------------------------------------------
class UpdatesSection(Section):
    def __init__(self, runner, parent=None):
        super().__init__(runner, parent)
        self.b = updates.Updates(runner)
        self.set(versions=[], state="unknown", newBuild="", autoUpdates=False, lastCheck=_("never"), apps=[],
                 appsText="", appsChecked=False, checked=False, loaded=False, count=0)

    def _version_row(self, v: updates.Version, os_name: str) -> dict:
        title = {"current": os_name, "update": _("New version"), "rollback": _("Previous version"),
                 "previous": _("Previous version")}[v.role]
        built = _("built {date}").format(date=nice_date(v.timestamp))
        sub = {"current": _("Installed and running · {built}"),
               "update": _("Downloaded · {built}"),
               "rollback": _("Used before the last update · {built}"),
               "previous": _("Kept so you can go back · {built}")}[v.role].format(built=built)
        pill = {"current": _("running now"), "update": _("starts after restart"),
                "rollback": _("starts after restart"), "previous": ""}[v.role]
        return {"role": v.role, "title": title, "sub": sub, "pill": pill, "build": v.build}

    def _load(self):
        st = self.b.status()
        return st, self.b.auto_updates(), self.b.last_check(), about.os_release().get("PRETTY_NAME", "Lucent OS")

    def _apply(self, res):
        if isinstance(res, Exception):
            return
        st, auto, last, pretty = res
        os_name = pretty.split(" (")[0]
        if st.rollback_pending:
            state = "rollback"
        elif st.pending is not None:
            state = "staged"
        elif st.available is not None:
            state = "available"
        elif self._s.get("checked"):
            state = "uptodate"
        else:
            state = self._s.get("state") if self._s.get("state") in ("error",) else "unknown"
        self.set(versions=[self._version_row(v, os_name) for v in st.versions], state=state,
                 newBuild=(st.pending or st.available).build if (st.pending or st.available) else "",
                 canRollBack=st.can_roll_back, autoUpdates=auto, lastCheck=when(last), loaded=True,
                 count=1 if state in ("staged", "available") else 0)

    @Slot()
    def refresh(self):
        tasks.run(self._load, self._apply)

    @Slot()
    def check(self):
        def work():
            ok, available, msg = self.b.check()
            apps = self.b.flatpak_updates()
            if ok:
                self.b.remember_check()
            return ok, available, msg, apps

        def done(res):
            if isinstance(res, Exception):
                return
            ok, _available, msg, apps = res
            self._apply_apps(apps)
            if ok:
                self.set(checked=True)
            else:
                self.set(state="error")
                cause = msg.rsplit(": ", 1)[-1] if msg else ""
                self._error = _("Couldn't check for updates. Are you online?") + (f" ({cause})" if cause else "")
                self.changed.emit()
            self.refresh()
        self.task("check", work, done)

    def _apply_apps(self, apps):
        if not isinstance(apps, list):
            return
        names = ", ".join(a.name for a in apps[:3]) + ("…" if len(apps) > 3 else "")
        text = ngettext("{n} app can be updated: {names}", "{n} apps can be updated: {names}",
                        len(apps)).format(n=len(apps), names=names) if apps else _("All apps are up to date")
        self.set(apps=[{"id": a.id, "name": a.name} for a in apps], appsText=text, appsChecked=True)

    @Slot()
    def checkApps(self):
        self.task("apps-check", self.b.flatpak_updates, self._apply_apps)

    @Slot()
    def download(self):
        self.task("download", self.b.apply, lambda _r: self.refresh(),
                  _("The update couldn't be downloaded."))

    @Slot()
    def restart(self):
        self.b.reboot()

    @Slot()
    def rollBack(self):
        self.task("rollback", self.b.roll_back, lambda _r: self.refresh(),
                  _("Couldn't switch to the previous version."))

    @Slot(bool)
    def setAuto(self, on):
        self.set(autoUpdates=on)
        self.task("auto", lambda: self.b.set_auto_updates(on), lambda _r: self.refresh(),
                  _("The setting wasn't changed."))

    @Slot()
    def updateApps(self):
        self.task("apps", self.b.flatpak_update, lambda _r: self.checkApps(), _("Some apps couldn't be updated."))


# ---------------------------------------------------------------------------
STATUS_LABELS = {"works": N_("Works well"), "partial": N_("Works, with known problems"),
                 "broken": N_("Doesn't work on Lucent"), "unknown": N_("Not tested yet")}


class WinAppsSection(Section):
    def __init__(self, runner, parent=None, machine: str | None = None):
        super().__init__(runner, parent)
        self.b = winapps.WinApps(runner)
        self.machine = machine or platform.machine()
        self.set(mode=winapps.mode(self.machine), apps=[], loaded=False)

    def _apply(self, apps):
        if not isinstance(apps, list):
            return
        rows = []
        for a in apps:
            # works / broken show as a pill; the others are said in words
            parts = [] if a.status in ("works", "broken") else [_(STATUS_LABELS.get(a.status, STATUS_LABELS["unknown"]))]
            if a.size is not None:
                parts.append(winapps.human_size(a.size))
            if a.exe_arch in ("x86_64", "x86") and self.machine in ("aarch64", "arm64"):
                parts.append(_("made for Intel/AMD, translated"))
            elif a.exe_arch == "x86":
                parts.append(_("32-bit"))
            rows.append({"id": a.app_id, "name": a.name, "icon": ("file://" + a.icon) if a.icon else "",
                         "folder": a.folder, "status": a.status, "sub": " · ".join(parts), "notes": a.notes})
        self.set(apps=rows, loaded=True)

    @Slot()
    def refresh(self):
        tasks.run(self.b.apps, self._apply)

    @Slot(str)
    def remove(self, app_id):
        self.task("remove:" + app_id, lambda: self.b.remove(app_id), lambda _r: self.refresh(),
                  _("The program wasn't removed."))

    @Slot(str)
    def openFolder(self, folder):
        self.b.open_folder(folder)


# ---------------------------------------------------------------------------
class HabitsSection(Section):
    def __init__(self, runner, parent=None):
        super().__init__(runner, parent)
        self.b = habits.Habits(runner)
        self.set(shortcuts=[{"action": _(s.action), "keys": list(s.keys)} for s in habits.SHORTCUTS],
                 buttons="right", layoutSwitch="alt_shift", layoutCount=1, doubleClick=True, loaded=False)

    @Slot()
    def refresh(self):
        self.set(buttons=self.b.buttons_side(), layoutSwitch=self.b.layout_switch(),
                 layoutCount=self.b.layout_count(), doubleClick=self.b.double_click(), loaded=True)

    @Slot(str)
    def setButtons(self, side):
        self.set(buttons=side)
        tasks.run(lambda: self.b.set_buttons_side(side))

    @Slot(str)
    def setLayoutSwitch(self, name):
        self.set(layoutSwitch=name)
        tasks.run(lambda: self.b.set_layout_switch(name))

    @Slot(bool)
    def setDoubleClick(self, on):
        self.set(doubleClick=on)
        tasks.run(lambda: self.b.set_double_click(on))


# ---------------------------------------------------------------------------
class AboutSection(Section):
    def __init__(self, runner, parent=None):
        super().__init__(runner, parent)
        self.b = about.About(runner)
        rel = about.os_release()
        pretty = rel.get("PRETTY_NAME", "Lucent OS")
        self.set(osName=pretty.split(" (")[0], loaded=False)

    def _load(self):
        s = self.b.summary()
        st = updates.Updates(self.r).status()
        return s, st.current.build if st.current else "", about.gpu()

    def _apply(self, res):
        if isinstance(res, Exception):
            return
        s, build, gpu = res
        mem = f"{s.memory_gb:.0f}" if s.memory_gb >= 3 else f"{s.memory_gb:.1f}"
        self.set(osName=s.os_name.split(" (")[0], osDetail=s.os_name, model=s.model or _("Unknown model"),
                 cpu=s.cpu, arch=s.arch, memory=_("{n} GB").format(n=mem),
                 storage=_("{free} GB free of {total} GB").format(free=round(s.disk_free_gb),
                                                                  total=round(s.disk_total_gb)),
                 gpu=gpu, hostname=s.hostname, kernel=s.kernel, build=build, loaded=True)

    @Slot()
    def refresh(self):
        tasks.run(self._load, self._apply)

    @Slot()
    def openAdvanced(self):
        self.b.open_advanced()

    @Slot()
    def openHardware(self):
        self.b.open_hardware_details()

    @Slot(str)
    def copy(self, text):
        from PySide6.QtGui import QGuiApplication
        QGuiApplication.clipboard().setText(text)


def sections(runner: Runner, parent=None) -> dict[str, Section]:
    return {
        "network": NetworkSection(runner, parent),
        "bluetooth": BluetoothSection(runner, parent),
        "display": DisplaySection(runner, parent),
        "sound": SoundSection(runner, parent),
        "appearance": AppearanceSection(runner, parent),
        "users": UsersSection(runner, parent),
        "updates": UpdatesSection(runner, parent),
        "winapps": WinAppsSection(runner, parent),
        "habits": HabitsSection(runner, parent),
        "about": AboutSection(runner, parent),
    }
