"""A Flatpak app's sandbox permissions, in words a newcomer understands.

Input is the app's metadata keyfile (`flatpak info --show-metadata`, or
`flatpak remote-info --cached --show-metadata` before installing). Output is
a short list, broadest access first, plus an overall isolation verdict.
Access an app only needs for itself (its own config folders, the GPU,
notifications) is not listed.
"""

from __future__ import annotations

import configparser
from dataclasses import dataclass

from .i18n import N_, _


@dataclass(frozen=True)
class Permission:
    text: str
    icon: str
    level: str      # "info", "notice", "high"


XDG = {
    "xdg-documents": (N_("Can read your Documents folder"), N_("Can read and change your Documents folder")),
    "xdg-download": (N_("Can read your Downloads folder"), N_("Can read and change your Downloads folder")),
    "xdg-pictures": (N_("Can read your Pictures folder"), N_("Can read and change your Pictures folder")),
    "xdg-music": (N_("Can read your Music folder"), N_("Can read and change your Music folder")),
    "xdg-videos": (N_("Can read your Videos folder"), N_("Can read and change your Videos folder")),
    "xdg-desktop": (N_("Can read your Desktop folder"), N_("Can read and change your Desktop folder")),
}
ALL_FILES = (N_("Can read all your files"), N_("Can read and change all your files"))
HOME = (N_("Can read your home folder"), N_("Can read and change your home folder"))
CHOSEN_ONLY = N_("Opens only the files you choose")


def _parse(meta: str) -> configparser.ConfigParser:
    cp = configparser.ConfigParser(interpolation=None, strict=False, delimiters=("=",))
    cp.optionxform = str
    try:
        cp.read_string(meta)
    except configparser.Error:
        return configparser.ConfigParser()
    return cp


def _list(cp: configparser.ConfigParser, key: str) -> list[str]:
    raw = cp.get("Context", key, fallback="") if cp.has_section("Context") else ""
    return [v for v in raw.split(";") if v and not v.startswith("!")]


def _bus(cp: configparser.ConfigParser, section: str) -> dict[str, str]:
    return dict(cp.items(section)) if cp.has_section(section) else {}


def _files(filesystems: list[str]) -> list[Permission]:
    out: list[Permission] = []
    host = [fs for fs in filesystems if fs.partition(":")[0] == "host"]
    home = [fs for fs in filesystems if fs.partition(":")[0] in ("home", "~")]
    for found, texts in ((host, ALL_FILES), (home, HOME)):
        if found:
            rw = any(fs.partition(":")[2] != "ro" for fs in found)
            return [Permission(_(texts[1] if rw else texts[0]), "folder", "notice")]
    for fs in filesystems:
        path, _sep, mode = fs.partition(":")
        if path in XDG:
            out.append(Permission(_(XDG[path][0 if mode == "ro" else 1]), "folder", "info"))
        elif path.startswith(("/", "~/")) and not path.startswith(("/tmp", "~/.")):
            out.append(Permission(_("Can use some other folders"), "folder", "info"))
    return list({p.text: p for p in out}.values())


def describe(meta: str) -> list[Permission]:
    cp = _parse(meta)
    shared, sockets, devices = _list(cp, "shared"), _list(cp, "sockets"), _list(cp, "devices")
    session = _bus(cp, "Session Bus Policy")

    out = _files(_list(cp, "filesystems"))
    if not out:
        out.append(Permission(_(CHOSEN_ONLY), "check", "info"))
    if "network" in shared:
        out.append(Permission(_("Uses the internet"), "globe", "info"))
    if session.get("org.freedesktop.Flatpak") == "talk":
        out.append(Permission(_("Can run programs outside its sandbox"), "x", "high"))
    if "system-bus" in sockets:
        out.append(Permission(_("Full access to system services"), "x", "high"))
    if "session-bus" in sockets:
        out.append(Permission(_("Full access to your session's services"), "x", "high"))
    if "all" in devices:
        out.append(Permission(_("Can use cameras, game controllers and other devices"), "chip", "notice"))
    elif "input" in devices:
        out.append(Permission(_("Can use game controllers"), "game", "info"))
    if "pulseaudio" in sockets:
        out.append(Permission(_("Plays sound and can use the microphone"), "info", "info"))
    if "bluetooth" in _list(cp, "features") or "bluetooth" in devices:
        out.append(Permission(_("Can use Bluetooth"), "info", "info"))
    if "ssh-auth" in sockets:
        out.append(Permission(_("Can use your SSH keys"), "lock", "notice"))
    if "gpg-agent" in sockets:
        out.append(Permission(_("Can use your GPG keys"), "lock", "notice"))
    if session.get("org.freedesktop.secrets") == "talk":
        out.append(Permission(_("Can use your saved passwords"), "lock", "notice"))
    if "x11" in sockets and "wayland" not in sockets:
        out.append(Permission(_("Can see other windows (older display system)"), "display", "notice"))
    return out


def isolation(meta: str) -> str:
    """"good" (no broad access), "limited" (broad file/device access) or
    "none" (can leave its sandbox)."""
    perms = describe(meta)
    if any(p.level == "high" for p in perms):
        return "none"
    if any(p.level == "notice" for p in perms):
        return "limited"
    return "good"
