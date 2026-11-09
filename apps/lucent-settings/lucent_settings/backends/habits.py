"""Windows habits: window buttons, the Win-key shortcuts, double-click,
the keyboard-layout switch.

The shortcuts are Lucent's defaults (/usr/share/lucent/kglobalshortcutsrc,
README "Shortcuts"); this page shows them, it doesn't edit them.
Win+Space always switches layouts (a KDE global shortcut); the choice here
adds Alt+Shift or Ctrl+Shift as the classic XKB toggle, or neither.
"""

from __future__ import annotations

from dataclasses import dataclass

from .. import dbus, kconfig
from ..i18n import N_
from ..run import Result, Runner

SWITCH_OPTIONS = {"alt_shift": "grp:alt_shift_toggle", "ctrl_shift": "grp:ctrl_shift_toggle", "win_space": ""}
BUTTONS = {"right": ("M", "IAX"), "left": ("XIA", "")}


@dataclass(frozen=True)
class Shortcut:
    action: str
    keys: list[str]


SHORTCUTS = [
    Shortcut(N_("Start menu"), ["Win"]),
    Shortcut(N_("Switch windows"), ["Alt", "Tab"]),
    Shortcut(N_("Open Files"), ["Win", "E"]),
    Shortcut(N_("Show desktop"), ["Win", "D"]),
    Shortcut(N_("Snap window to a side"), ["Win", "← →"]),
    Shortcut(N_("Lock the computer"), ["Win", "L"]),
    Shortcut(N_("Task Manager"), ["Ctrl", "Shift", "Esc"]),
    Shortcut(N_("Screenshot"), ["PrtSc"]),
]


class Habits:
    def __init__(self, runner: Runner):
        self.r = runner

    def double_click(self) -> bool:
        return kconfig.read("kdeglobals", "KDE", "SingleClick", "false").lower() != "true"

    def set_double_click(self, on: bool) -> Result:
        res = kconfig.write(self.r, "kdeglobals", "KDE", "SingleClick", not on)
        # KGlobalSettings::SettingsChanged (3), SETTINGS_MOUSE (0): what the
        # mouse settings module sends so running apps reread the click mode.
        self.r.run(dbus.emit(dbus.SESSION, "/KGlobalSettings", "org.kde.KGlobalSettings", "notifyChange",
                             "ii", 3, 0))
        return res

    def _options(self) -> list[str]:
        raw = kconfig.read("kxkbrc", "Layout", "Options", "")
        return [o for o in raw.split(",") if o]

    def layout_switch(self) -> str:
        opts = self._options()
        for name, opt in SWITCH_OPTIONS.items():
            if opt and opt in opts:
                return name
        return "win_space"

    def layout_count(self) -> int:
        layouts = [x for x in kconfig.read("kxkbrc", "Layout", "LayoutList", "").split(",") if x]
        return max(1, len(layouts))

    def set_layout_switch(self, name: str) -> Result:
        opts = [o for o in self._options() if not o.startswith("grp:")]
        if SWITCH_OPTIONS[name]:
            opts.append(SWITCH_OPTIONS[name])
        res = kconfig.write(self.r, "kxkbrc", "Layout", "Options", ",".join(opts))
        kconfig.write(self.r, "kxkbrc", "Layout", "ResetOldOptions", True)
        self.r.run(dbus.emit(dbus.SESSION, "/Layouts", "org.kde.keyboard", "reloadConfig"))
        return res

    def buttons_side(self) -> str:
        left = kconfig.read("kwinrc", "org.kde.kdecoration2", "ButtonsOnLeft", "M")
        return "left" if "X" in left else "right"

    def set_buttons_side(self, side: str) -> Result:
        left, right = BUTTONS[side]
        kconfig.write(self.r, "kwinrc", "org.kde.kdecoration2", "ButtonsOnLeft", left)
        res = kconfig.write(self.r, "kwinrc", "org.kde.kdecoration2", "ButtonsOnRight", right)
        self.r.run(dbus.call(dbus.SESSION, "org.kde.KWin", "/KWin", "org.kde.KWin", "reconfigure"))
        return res
