"""First-login keyboard layouts: follow what the installer chose.

Anaconda (or `localectl set-x11-keymap`) records the system keyboard in
/etc/X11/xorg.conf.d/00-keyboard.conf. Plasma keeps its own per-user list
in ~/.config/kxkbrc, so on a user's first login
(/usr/libexec/lucent/user-defaults, before KWin starts) this copies the
system layouts there. With no system layout the user simply gets `us`.
With two or more layouts, Alt+Shift switches them (Win+Space is bound in
kglobalshortcutsrc) unless the installer already set a switch option.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

X11_CONFIG = Path("/etc/X11/xorg.conf.d/00-keyboard.conf")
DEFAULT_SWITCH = "grp:alt_shift_toggle"

_OPTION = re.compile(r'^\s*Option\s+"(XkbLayout|XkbVariant|XkbOptions)"\s+"([^"]*)"', re.M)


def parse_x11_config(text: str) -> tuple[list[str], list[str], list[str]]:
    values = dict(_OPTION.findall(text))
    layouts = [x.strip() for x in values.get("XkbLayout", "").split(",") if x.strip()]
    variants = [x.strip() for x in values.get("XkbVariant", "").split(",")][: len(layouts)]
    variants += [""] * (len(layouts) - len(variants))
    options = [x.strip() for x in values.get("XkbOptions", "").split(",") if x.strip()]
    return layouts, variants, options


def kxkb_settings(layouts: list[str], variants: list[str], options: list[str]) -> dict[str, str] | None:
    """kxkbrc [Layout] keys for these system settings, or None to keep Plasma's default (us)."""
    if not layouts or (layouts == ["us"] and not any(variants) and not options):
        return None
    settings = {"Use": "true", "LayoutList": ",".join(layouts), "VariantList": ",".join(variants)}
    if len(layouts) > 1 and not any(o.startswith("grp:") for o in options):
        options = [DEFAULT_SWITCH, *options]
    if options:
        settings["Options"] = ",".join(options)
        settings["ResetOldOptions"] = "true"
    return settings


def write_cmds(settings: dict[str, str]) -> list[list[str]]:
    return [["kwriteconfig6", "--file", "kxkbrc", "--group", "Layout", "--key", k, "--", v]
            for k, v in settings.items()]


def user_has_layouts() -> bool:
    out = subprocess.run(["kreadconfig6", "--file", "kxkbrc", "--group", "Layout", "--key", "LayoutList"],
                         capture_output=True, text=True).stdout
    return bool(out.strip())


def main() -> int:
    try:
        text = X11_CONFIG.read_text()
    except OSError:
        text = ""
    settings = kxkb_settings(*parse_x11_config(text))
    if settings is None or user_has_layouts():
        return 0
    for cmd in write_cmds(settings):
        subprocess.run(cmd, check=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
