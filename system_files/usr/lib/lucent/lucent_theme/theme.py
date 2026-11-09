"""Switch Lucent's look: light / dark / auto and the accent, in one step.

Everything uses Plasma's own mechanisms, live (no re-login):

  mode light|dark  plasma-apply-lookandfeel -a org.lucent.desktop[.dark]
                   (colour scheme, Plasma theme, widget style lucent /
                   lucent-dark, window decoration, icons: what Quick
                   Settings' Theme does); Plasma's automatic mode off
  mode auto        kdeglobals [KDE] AutomaticLookAndFeel=true: Plasma's
                   kded module switches between the two at sunrise/sunset
  accent           KDE's accent override (plasma-apply-colorscheme
                   --accent-color) for the colour scheme and everything that
                   follows it (Plasma theme, Kirigami, launcher); Indigo is the
                   schemes' own accent, so it removes the override. Kvantum
                   can't follow the palette: every accent is its own Kvantum
                   theme (Lucent, LucentAzure, ...; ~/.config/Kvantum/
                   kvantum.kvconfig), and running Qt apps are told to reload
                   their style
  Flatpak apps     /usr/libexec/lucent/kvantum-flatpak-sync copies the
                   active Kvantum theme (and its light/dark variant) into
                   each Flatpak Qt app
  wallpaper        a desktop showing one image of a wallpaper package is put
                   back on the package, so Plasma shows its day or night
                   image to match the mode

The choice is kept in ~/.config/lucent-themerc. `sync` (run when kdeglobals
changes, lucent-kvantum-sync.path) puts it back when Plasma's automatic mode
switched the global theme, and follows Plasma's "accent from wallpaper".
"""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from . import accents

LIGHT_PKG = "org.lucent.desktop"
DARK_PKG = "org.lucent.desktop.dark"
OWN = "lucent-themerc"
SETTINGS = "lucent-settingsrc"          # Lucent Settings keeps its swatch here too
MARK = "# Managed by Lucent (lucent-theme)"
FLATPAK_SYNC = "/usr/libexec/lucent/kvantum-flatpak-sync"
MODES = ("light", "dark", "auto")


@dataclass
class Result:
    code: int
    out: str
    err: str


class Runner:
    def run(self, argv, timeout=60) -> Result:
        try:
            p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        except FileNotFoundError:
            return Result(127, "", f"{argv[0]}: not found")
        except subprocess.TimeoutExpired:
            return Result(124, "", f"{argv[0]}: timed out")
        return Result(p.returncode, p.stdout, p.stderr)


# ------------------------------------------------------------ kconfig ---
def config_home() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")


def parse_kconfig(text: str) -> dict[tuple[str, ...], dict[str, str]]:
    groups: dict[tuple[str, ...], dict[str, str]] = {}
    cur: dict[str, str] | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if line.startswith("[") and line.endswith("]"):
            cur = groups.setdefault(tuple(line[1:-1].split("][")), {})
        elif "=" in line and cur is not None:
            k, v = line.split("=", 1)
            cur[k.strip()] = v.strip()
    return groups


def dump_kconfig(groups) -> str:
    out = []
    for names, kv in groups.items():
        out.append("[" + "][".join(names) + "]")
        out += [f"{k}={v}" for k, v in kv.items()]
        out.append("")
    return "\n".join(out)


def read(file: str, group: str, key: str, default: str = "") -> str:
    try:
        return parse_kconfig((config_home() / file).read_text()).get((group,), {}).get(key, default)
    except OSError:
        return default


def write_own(file: str, group: str, values: dict[str, str]) -> None:
    path = config_home() / file
    try:
        groups = parse_kconfig(path.read_text())
    except OSError:
        groups = {}
    g = groups.setdefault((group,), {})
    for k, v in values.items():
        if v == "":
            g.pop(k, None)
        else:
            g[k] = v
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_kconfig(groups))


def kwrite(r, file, group, key, value=None) -> Result:
    # --notify: running Plasma (e.g. the automatic light/dark switcher) re-reads it
    argv = ["kwriteconfig6", "--notify", "--file", file, "--group", group, "--key", key]
    argv += ["--delete"] if value is None else ["--", value]
    return r.run(argv)


# -------------------------------------------------------------- state ---
@dataclass
class State:
    mode: str          # light | dark | auto
    accent: str        # accent id


def _rgb_key(value: str) -> str:
    """'47,122,224' -> '#2f7ae0' ('' if not a colour)."""
    try:
        r, g, b = (int(x) for x in value.split(",")[:3])
    except ValueError:
        return ""
    return "#%02x%02x%02x" % (r, g, b)


def current_mode() -> str:
    if read("kdeglobals", "KDE", "AutomaticLookAndFeel", "false").lower() == "true":
        return "auto"
    return "dark" if effective_dark() else "light"


def effective_dark() -> bool:
    """Is the desktop dark right now (whatever chose it)?"""
    pkg = read("kdeglobals", "KDE", "LookAndFeelPackage", "")
    if pkg:
        return pkg.endswith(".dark")
    return read("kdeglobals", "KDE", "widgetStyle", "").lower().endswith("-dark")


def read_state() -> State:
    mode = read(OWN, "Theme", "Mode", "") or current_mode()
    acc = read(OWN, "Theme", "Accent", "")
    if not acc:   # not chosen here yet: adopt Lucent Settings' swatch, if any
        hexc = read(SETTINGS, "Appearance", "Accent", "")
        acc = accents.nearest(hexc).id if hexc.startswith("#") and len(hexc) == 7 else accents.DEFAULT.id
    return State(mode if mode in MODES else "light", acc if accents.find(acc) else accents.DEFAULT.id)


def kvantum_theme(accent_id: str) -> str:
    return "Lucent" if accent_id == "indigo" else "Lucent" + accents.find(accent_id).name


def kvantum_current() -> str:
    path = config_home() / "Kvantum/kvantum.kvconfig"
    try:
        return parse_kconfig(path.read_text()).get(("General",), {}).get("theme", "Lucent")
    except OSError:
        return "Lucent"


def _kvantum_ours() -> bool:
    path = config_home() / "Kvantum/kvantum.kvconfig"
    try:
        text = path.read_text()
    except OSError:
        return True
    return text.startswith(MARK) or kvantum_current().startswith("Lucent")


# ------------------------------------------------------------ actions ---
WALLPAPER_JS = r"""
for (const d of desktops()) {
    if (d.wallpaperPlugin !== "org.kde.image") continue;
    d.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    const img = d.readConfig("Image", "");
    const m = String(img).match(/^(file:\/\/)?(\/usr\/share\/wallpapers\/[^\/]+)\/contents\/images(_dark)?\//);
    if (m) d.writeConfig("Image", "file://" + m[2] + "/");
}
"""


def _wallpaper_follows_mode(r) -> None:
    """Desktops showing one image of a wallpaper package go back to the
    package, so Plasma picks its day or night image for the mode."""
    r.run(["dbus-send", "--session", "--print-reply", "--dest=org.kde.plasmashell", "/PlasmaShell",
           "org.kde.PlasmaShell.evaluateScript", "string:" + WALLPAPER_JS])


def _set_kvantum(r, accent_id: str) -> bool:
    name = kvantum_theme(accent_id)
    path = config_home() / "Kvantum/kvantum.kvconfig"
    wanted = f"{MARK}\n[General]\ntheme={name}\n"
    try:
        if path.read_text() == wanted:
            return False
    except OSError:
        pass
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(wanted)
    # KDE apps re-create their style on KGlobalSettings' StyleChanged (2):
    # Kvantum then reads the new theme. No re-login needed.
    r.run(["dbus-send", "--session", "--type=signal", "/KGlobalSettings",
           "org.kde.KGlobalSettings.notifyChange", "int32:2", "int32:0"])
    return True


def _apply_global_theme(r, pkg: str, errors: list[str]) -> None:
    """plasma-apply-lookandfeel also resets the window-button layout to the
    package's; a layout the person chose (Settings' habits) is kept."""
    left = read("kwinrc", "org.kde.kdecoration2", "ButtonsOnLeft", "")
    right = read("kwinrc", "org.kde.kdecoration2", "ButtonsOnRight", "")
    _check(r.run(["plasma-apply-lookandfeel", "-a", pkg], timeout=90), errors)
    if (left or right) and (read("kwinrc", "org.kde.kdecoration2", "ButtonsOnLeft", "") != left
                            or read("kwinrc", "org.kde.kdecoration2", "ButtonsOnRight", "") != right):
        kwrite(r, "kwinrc", "org.kde.kdecoration2", "ButtonsOnLeft", left)
        kwrite(r, "kwinrc", "org.kde.kdecoration2", "ButtonsOnRight", right)
        r.run(["dbus-send", "--session", "--type=method_call", "--dest=org.kde.KWin", "/KWin", "org.kde.KWin.reconfigure"])


def _accent_in_kde() -> str:
    """The accent the colour scheme shows now, '' if it is the scheme's own.

    Plasma 6 keeps no AccentColor key: plasma-apply-colorscheme
    --accent-color writes the colour into every set's DecorationFocus
    (exactly; Selection gets a tinted shade) and a global theme puts the
    scheme's own colours back. The Lucent schemes' own DecorationFocus is
    their indigo (#4257e8 light, #7088ff dark)."""
    focus = _rgb_key(read("kdeglobals", "Colors:Window", "DecorationFocus", ""))
    own = {accents.INDIGO[False]["accent"], accents.INDIGO[True]["accent"]}
    return "" if not focus or focus in own else focus


def _apply_colour_accent(r, accent_id: str, errors: list[str]) -> None:
    a = accents.find(accent_id)
    if a.id == "indigo":
        if _accent_in_kde():
            # The schemes' own colours come back with the global theme.
            _apply_global_theme(r, DARK_PKG if effective_dark() else LIGHT_PKG, errors)
        return
    if _accent_in_kde() != a.hex:
        _check(r.run(["plasma-apply-colorscheme", "--accent-color", a.hex]), errors)


def _check(res: Result, errors: list[str]) -> None:
    if res.code != 0:
        errors.append((res.err or res.out).strip() or f"exit code {res.code}")


def _keep_settings_in_step(accent_id: str) -> None:
    """Lucent Settings remembers its swatch in lucent-settingsrc and puts it
    back after theme switches; keep that the same as ours."""
    path = config_home() / SETTINGS
    if path.exists():
        a = accents.find(accent_id)
        write_own(SETTINGS, "Appearance", {"Accent": "" if a.id == "indigo" else a.hex})


def apply(r, mode: str | None = None, accent: str | None = None, errors: list[str] | None = None) -> int:
    """Apply a mode and/or an accent (None = keep). Returns 0 or 1."""
    errors = [] if errors is None else errors
    st = read_state()
    if accent is not None:
        a = accents.find(accent) or (accents.nearest(accent) if accent.startswith("#") and len(accent) == 7 else None)
        if a is None:
            raise ValueError(f"unknown accent: {accent}")
        st.accent = a.id
    if mode is not None:
        if mode not in MODES:
            raise ValueError(f"unknown mode: {mode}")
        st.mode = mode
        if mode == "auto":
            for key, val in (("DefaultLightLookAndFeel", LIGHT_PKG), ("DefaultDarkLookAndFeel", DARK_PKG),
                             ("AutomaticLookAndFeel", "true")):
                _check(kwrite(r, "kdeglobals", "KDE", key, val), errors)
        else:
            _check(kwrite(r, "kdeglobals", "KDE", "AutomaticLookAndFeel", "false"), errors)
            pkg = DARK_PKG if mode == "dark" else LIGHT_PKG
            if read("kdeglobals", "KDE", "LookAndFeelPackage", "") != pkg:
                _apply_global_theme(r, pkg, errors)
        _wallpaper_follows_mode(r)
    write_own(OWN, "Theme", {"Mode": st.mode, "Accent": st.accent})
    _keep_settings_in_step(st.accent)
    _apply_colour_accent(r, st.accent, errors)
    _set_kvantum(r, st.accent)
    _check(r.run([FLATPAK_SYNC], timeout=120), errors)
    return 1 if errors else 0


def sync(r, errors: list[str] | None = None) -> int:
    """Re-assert the chosen look after something else changed kdeglobals."""
    errors = [] if errors is None else errors
    chosen = bool(read(OWN, "Theme", "Accent", "") or read(SETTINGS, "Appearance", "Accent", ""))
    if read("kdeglobals", "General", "accentColorFromWallpaper", "false").lower() == "true" or not chosen:
        # Plasma picks the accent (from the wallpaper, or System Settings set
        # one and nothing was chosen through Lucent): Kvantum follows the
        # nearest swatch, the colours are left as they are.
        kde = _accent_in_kde()
        if _kvantum_ours():
            _set_kvantum(r, accents.nearest(kde).id if kde else accents.DEFAULT.id)
    else:
        st = read_state()
        _apply_colour_accent(r, st.accent, errors)
        if _kvantum_ours():
            _set_kvantum(r, st.accent)
    # The UI font for the session's language (plasma-localerc changed): see fonts.py
    from . import fonts
    fonts.apply(r)
    _check(r.run([FLATPAK_SYNC], timeout=120), errors)
    return 1 if errors else 0


def status() -> dict:
    st = read_state()
    a = accents.find(st.accent)
    return {
        "mode": st.mode,
        "effective_mode": "dark" if effective_dark() else "light",
        "accent": a.id,
        "accent_name": a.name,
        "accent_hex": a.hex,
        "accent_from_wallpaper": read("kdeglobals", "General", "accentColorFromWallpaper", "false").lower() == "true",
        "kvantum_theme": kvantum_current(),
        "look_and_feel": read("kdeglobals", "KDE", "LookAndFeelPackage", LIGHT_PKG),
    }
