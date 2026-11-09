"""Light / Dark / Auto, accent color, wallpaper, animations, text size.

Light and dark are Lucent's two global themes (look-and-feel packages
org.lucent.desktop and org.lucent.desktop.dark), applied with Plasma's own
`plasma-apply-lookandfeel`, exactly what Quick Settings does. Everything
that follows the look already listens to that: the widget style switches
with the package, Kvantum for Flatpak apps follows kdeglobals
(lucent-kvantum-sync.path). Auto is Plasma's own automatic mode
(kdeglobals [KDE] AutomaticLookAndFeel, switched by the
lookandfeelautoswitcher kded module at sunrise/sunset).

Applying a global theme resets the colour scheme and window buttons, so the
accent the person chose is kept in ~/.config/lucent-settingsrc and put back,
and the window-button side is restored afterwards. `sync_accent` does the
same after Auto switches at sunset (lucent-settings-accent.path).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse

from .. import dbus, kconfig
from ..i18n import language
from ..run import Result, Runner

LIGHT = "org.lucent.desktop"
DARK = "org.lucent.desktop.dark"
# The swatches of the 2026 design (Prism's colours, qml/Lucent/Theme.qml
# `accents`); the first is the theme's own blue, i.e. "no custom accent".
ACCENTS = ["#4257e8", "#2f7ae0", "#1f96a8", "#7a55e0", "#a54fc4", "#cf4f86", "#3f8f68", "#5f6684"]
# Lucent's own wallpapers first in the Appearance row (Pebble Drift set).
LUCENT_WALLPAPERS = ["Drift", "Tide", "Aurora", "Lucent"]
ANIMATIONS = {"off": "0", "fast": "0.7", "normal": "1"}
TEXT_SIZES = [10, 11, 12, 13]
SYSTEM_WALLPAPERS = Path("/usr/share/wallpapers")
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".avif", ".jxl", ".svg"}
OWN = "lucent-settingsrc"
FONT_KEYS = [("General", "font", 0), ("General", "menuFont", 0), ("General", "toolBarFont", 0),
             ("General", "smallestReadableFont", -1), ("WM", "activeFont", 0)]


def user_wallpaper_packages() -> Path:
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share") / "wallpapers"


def user_picture_dirs() -> list[Path]:
    pics = Path(os.environ.get("XDG_PICTURES_DIR") or Path.home() / "Pictures")
    return [pics / "Wallpapers", pics]


@dataclass
class Wallpaper:
    path: str
    name: str
    thumbnail: str
    ours: bool
    thumbnail_dark: str = ""   # a package's night image, if it has one
    description: str = ""


def _own_get(key: str, default: str = "") -> str:
    path = kconfig.config_home() / OWN
    try:
        return kconfig.parse(path.read_text()).get(("Appearance",), {}).get(key, default)
    except OSError:
        return default


def _own_set(key: str, value: str) -> None:
    path = kconfig.config_home() / OWN
    try:
        groups = kconfig.parse(path.read_text())
    except OSError:
        groups = {}
    groups.setdefault(("Appearance",), {})[key] = value
    lines = []
    for names, kv in groups.items():
        lines.append("[" + "][".join(names) + "]")
        lines += [f"{k}={v}" for k, v in kv.items() if v != ""]
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def _rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _hue_close(a: tuple[int, int, int], b: tuple[int, int, int]) -> bool:
    import colorsys
    ha, la, sa = colorsys.rgb_to_hls(*(c / 255 for c in a))
    hb, lb, sb = colorsys.rgb_to_hls(*(c / 255 for c in b))
    if sa < 0.15 or sb < 0.15:  # greys: compare saturation instead of hue
        return abs(sa - sb) < 0.15
    d = abs(ha - hb)
    return min(d, 1 - d) < 0.04


def chosen_accent() -> str:
    """The accent picked in Settings ("" = the theme's own)."""
    return _own_get("Accent")


def selection_color() -> str:
    """The accent Plasma uses now (e.g. taken from the wallpaper), as #rrggbb:
    kdeglobals [General] AccentColor, else the selection colour."""
    sel = kconfig.read("kdeglobals", "General", "AccentColor", "") or \
        kconfig.read("kdeglobals", "Colors:Selection", "BackgroundNormal", "")
    try:
        r, g, b = (int(x) for x in sel.split(",")[:3])
    except ValueError:
        return ""
    return f"#{r:02x}{g:02x}{b:02x}"


def sync_accent(runner: Runner) -> bool:
    """Put the chosen accent back if a theme switch dropped it. True if applied."""
    accent = _own_get("Accent")
    if not accent:
        return False
    sel = kconfig.read("kdeglobals", "Colors:Selection", "BackgroundNormal", "")
    try:
        current = tuple(int(x) for x in sel.split(","))[:3]
    except ValueError:
        current = ()
    if len(current) == 3 and _hue_close(current, _rgb(accent)):
        return False
    runner.run(["plasma-apply-colorscheme", "--accent-color", accent])
    return True


def thumbnail(path: str, dark: bool = False) -> str:
    """An image to show for a wallpaper: the picture, or a package's light
    (or, if it has one, dark) image."""
    p = Path(path)
    if p.is_dir():
        images = sorted((p / "contents" / "images_dark").glob("*")) if dark else []
        images = images or sorted((p / "contents" / "images").glob("*"))
        if images:
            return str(next((i for i in images if i.name.startswith("3840x2160")), images[-1]))
        return ""
    return str(p) if p.is_file() else ""


class Appearance:
    def __init__(self, runner: Runner):
        self.r = runner

    # --- light / dark / auto -------------------------------------------------
    def mode(self) -> str:
        if kconfig.read("kdeglobals", "KDE", "AutomaticLookAndFeel", "false").lower() == "true":
            return "auto"
        pkg = kconfig.read("kdeglobals", "KDE", "LookAndFeelPackage", LIGHT)
        return "dark" if pkg.endswith(".dark") else "light"

    def set_mode(self, mode: str) -> Result:
        if mode == "auto":
            return kconfig.write(self.r, "kdeglobals", "KDE", "AutomaticLookAndFeel", True)
        left = kconfig.read("kwinrc", "org.kde.kdecoration2", "ButtonsOnLeft", "")
        right = kconfig.read("kwinrc", "org.kde.kdecoration2", "ButtonsOnRight", "")
        res = self.r.run(["plasma-apply-lookandfeel", "-a", DARK if mode == "dark" else LIGHT], timeout=60)
        self._after_theme(left, right)
        return res

    def _after_theme(self, left: str, right: str) -> None:
        if left or right:
            kconfig.write(self.r, "kwinrc", "org.kde.kdecoration2", "ButtonsOnLeft", left)
            kconfig.write(self.r, "kwinrc", "org.kde.kdecoration2", "ButtonsOnRight", right)
            self.r.run(dbus.call(dbus.SESSION, "org.kde.KWin", "/KWin", "org.kde.KWin", "reconfigure"))
        accent = _own_get("Accent")
        if accent:
            self.r.run(["plasma-apply-colorscheme", "--accent-color", accent])

    # --- accent --------------------------------------------------------------
    def accent(self) -> str:
        return _own_get("Accent") or ACCENTS[0]

    def set_accent(self, color: str) -> Result:
        if color.lower() == ACCENTS[0]:
            _own_set("Accent", "")
            pkg = DARK if kconfig.read("kdeglobals", "KDE", "LookAndFeelPackage", LIGHT).endswith(".dark") else LIGHT
            # Re-applying the theme (keeping Auto) restores its own colours,
            # once Plasma's remembered accent is gone.
            kconfig.write(self.r, "kdeglobals", "General", "AccentColor", None)
            left = kconfig.read("kwinrc", "org.kde.kdecoration2", "ButtonsOnLeft", "")
            right = kconfig.read("kwinrc", "org.kde.kdecoration2", "ButtonsOnRight", "")
            res = self.r.run(["plasma-apply-lookandfeel", "-k", "-a", pkg], timeout=60)
            self._after_theme(left, right)
            return res
        _own_set("Accent", color.lower())
        return self.r.run(["plasma-apply-colorscheme", "--accent-color", color.lower()])

    def accent_from_wallpaper(self) -> bool:
        return kconfig.read("kdeglobals", "General", "accentColorFromWallpaper", "false").lower() == "true"

    def set_accent_from_wallpaper(self, on: bool) -> Result:
        """Plasma's own "accent from wallpaper" (plasmashell picks the colour)."""
        res = kconfig.write(self.r, "kdeglobals", "General", "accentColorFromWallpaper", on)
        if not on:
            # back to the swatch chosen before, or the theme's own colours
            self.set_accent(_own_get("Accent") or ACCENTS[0])
        return res

    # --- wallpaper -----------------------------------------------------------
    def wallpapers(self) -> list[Wallpaper]:
        out: list[Wallpaper] = []
        packages = []
        metas = sorted(user_wallpaper_packages().glob("*/metadata.json")) + sorted(SYSTEM_WALLPAPERS.glob("*/metadata.json"))
        seen_ids = set()
        for meta in metas:
            if meta.parent.name in seen_ids:
                continue  # a package installed for the user hides the system copy
            seen_ids.add(meta.parent.name)
            try:
                plugin = json.loads(meta.read_text())["KPlugin"]
                name = plugin["Name"]
            except (ValueError, KeyError, OSError):
                continue
            thumb = thumbnail(str(meta.parent))
            if thumb:
                night = thumbnail(str(meta.parent), dark=True)
                about = plugin.get(f"Description[{language()}]") or plugin.get("Description", "")
                packages.append(Wallpaper(str(meta.parent), name, thumb, True, night if night != thumb else "", about))
        packages.sort(key=lambda w: (w.name not in LUCENT_WALLPAPERS,
                                     LUCENT_WALLPAPERS.index(w.name) if w.name in LUCENT_WALLPAPERS else 0,
                                     w.name.lower()))
        out += packages
        seen = set()
        for d in user_picture_dirs():
            try:
                files = sorted(p for p in d.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXT)
            except OSError:
                continue
            for f in files:
                if f in seen:
                    continue
                seen.add(f)
                out.append(Wallpaper(str(f), f.stem, str(f), False))
        return out

    def current_wallpaper(self) -> str:
        path = kconfig.config_home() / "plasma-org.kde.plasma.desktop-appletsrc"
        try:
            groups = kconfig.parse(path.read_text())
        except OSError:
            return str(SYSTEM_WALLPAPERS / "Lucent")
        for names, kv in groups.items():
            if names[-2:] == ("org.kde.image", "General") and "Wallpaper" in names and kv.get("Image"):
                url = kv["Image"]
                p = unquote(urlparse(url).path) if url.startswith("file:") else url
                return p.rstrip("/")
        return str(SYSTEM_WALLPAPERS / "Lucent")

    def set_wallpaper(self, path: str) -> Result:
        return self.r.run(["plasma-apply-wallpaperimage", path], timeout=30)

    # --- motion and text -----------------------------------------------------
    def animations(self) -> str:
        value = kconfig.read("kdeglobals", "KDE", "AnimationDurationFactor", "1")
        try:
            f = float(value)
        except ValueError:
            return "normal"
        return "off" if f == 0 else "fast" if f < 0.95 else "normal"

    def set_animations(self, speed: str) -> Result:
        return kconfig.write(self.r, "kdeglobals", "KDE", "AnimationDurationFactor", ANIMATIONS[speed])

    def text_size(self) -> int:
        font = kconfig.read("kdeglobals", "General", "font", "Inter,11")
        try:
            return int(float(font.split(",")[1]))
        except (IndexError, ValueError):
            return 11

    def set_text_size(self, points: int) -> Result:
        res = Result(0)
        for group, key, delta in FONT_KEYS:
            current = kconfig.read("kdeglobals", group, key, "")
            parts = current.split(",") if current.count(",") >= 9 else \
                ["Inter", "11", "-1", "5", "600" if key == "activeFont" else "400"] + ["0"] * 10 + ["1"]
            parts[1] = str(points + delta)
            res = kconfig.write(self.r, "kdeglobals", group, key, ",".join(parts))
        # KDE apps reload fonts on this signal (KFontSettingsData).
        self.r.run(dbus.emit(dbus.SESSION, "/KDEPlatformTheme", "org.kde.KDEPlatformTheme", "refreshFonts"))
        return res
