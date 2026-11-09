"""The UI font follows the session's language.

Pebble Drift's typeface is Figtree (/usr/share/fonts/figtree, SIL OFL). It
has Latin only (Western and Central European, not Vietnamese), no Cyrillic
or Greek. A Russian session in Figtree would draw every Latin letter in
Figtree and every Cyrillic one in a fallback font: a patchwork. So:

  every language of the session covered by Figtree  -> Figtree
  any other (ru, uk, el, vi, zh, ...)                -> Inter

"Covered" is fontconfig's own answer (`fc-list Figtree:lang=ru`), so there is
no hand-kept list. The session's languages are the UI language (the first
entry of LANGUAGE) and the formats' (LC_TIME, LANG: Russian formats put
Cyrillic month names in the clock), read from KDE's plasma-localerc (what
the Region & Language page writes) and from the environment.

It changes only the five font keys of kdeglobals, and only while they are
Figtree or Inter: a font the person picked is left alone, and the size and
the rest of the string are kept (Figtree's default weight 500 maps to
Inter's 400 and back). It runs at every login before the shell starts
(/etc/xdg/plasma-workspace/env/lucent-ui-font.sh) and from `lucent-theme
sync` when plasma-localerc changes, so a language switch takes effect at
once if it needs Inter and at the next login otherwise. Text in other
scripts inside a Figtree session (a Cyrillic file name) falls back to Inter
through fontconfig (/etc/fonts/conf.d/60-lucent-fonts.conf).
"""
from __future__ import annotations

import os

from . import theme

FIGTREE = "Figtree"
INTER = "Inter"
WEIGHT = {FIGTREE: 500, INTER: 400}    # Figtree Medium: --type-body-weight 500
# (group, key, point size, fixed weight or None = the family's default)
# 11 pt = 14.7 px at 96 dpi: the mockups' 15 px body text, readable at 1x.
KEYS = [("General", "font", 11, None), ("General", "menuFont", 11, None),
        ("General", "toolBarFont", 11, None), ("General", "smallestReadableFont", 10, None),
        ("WM", "activeFont", 11, 600)]
MANAGED = {FIGTREE, INTER}


def font_string(family: str, size: float, weight: int) -> str:
    """A Qt 6 QFont::toString() as KDE stores it in kdeglobals."""
    size_s = f"{size:g}"
    return f"{family},{size_s},-1,5,{weight},0,0,0,0,0,0,0,0,0,0,1"


def lang_code(locale: str) -> str:
    """'ru_RU.UTF-8' -> 'ru', 'zh_CN' -> 'zh-cn' (fontconfig's names: only
    Chinese is told apart by territory, it differs in script)."""
    loc = locale.strip().split(".")[0].split("@")[0].replace("_", "-").lower()
    if loc in ("c", "posix"):
        return "en"
    return loc if loc.startswith("zh-") else loc.split("-")[0]


def _localerc() -> dict:
    path = theme.config_home() / "plasma-localerc"
    try:
        return theme.parse_kconfig(path.read_text())
    except OSError:
        return {}


def session_languages(env=None) -> list[str]:
    """The UI and formats languages, KDE's settings first, then the environment."""
    env = os.environ if env is None else env
    rc = _localerc()
    found = [rc.get(("Translations",), {}).get("LANGUAGE", "").split(":")[0],
             rc.get(("Formats",), {}).get("LC_TIME", ""), rc.get(("Formats",), {}).get("LANG", ""),
             env.get("LANGUAGE", "").split(":")[0], env.get("LC_ALL", ""), env.get("LC_MESSAGES", ""),
             env.get("LC_TIME", ""), env.get("LANG", "")]
    out = []
    for loc in found:
        code = lang_code(loc) if loc else ""
        if code and code not in out:
            out.append(code)
    return out or ["en"]


def covers(r, family: str, code: str) -> bool:
    """Does fontconfig say `family` has every letter of language `code`?"""
    for c in dict.fromkeys([code, code.split("-")[0]]):
        res = r.run(["fc-list", f"{family}:lang={c}", "family"], timeout=20)
        if res.code == 0 and res.out.strip():
            return True
    return False


def wanted_family(r, env=None) -> str:
    return FIGTREE if all(covers(r, FIGTREE, c) for c in session_languages(env)) else INTER


def _read(group: str, key: str) -> str:
    return theme.read("kdeglobals", group, key, "")


def apply(r, env=None) -> list[str]:
    """Put the session's family into kdeglobals; returns the keys written."""
    family = wanted_family(r, env)
    written = []
    for group, key, size, fixed in KEYS:
        cur = _read(group, key)
        if not cur:
            if family == FIGTREE:
                continue        # the system default (/etc/xdg/kdeglobals) is Figtree
            new = font_string(family, size, fixed or WEIGHT[family])
        else:
            parts = cur.split(",")
            if parts[0] not in MANAGED or parts[0] == family:
                continue        # the person's own font, or already right
            if fixed is None and len(parts) > 4 and parts[4] == str(WEIGHT[parts[0]]):
                parts[4] = str(WEIGHT[family])
            parts[0] = family
            new = ",".join(parts)
        theme.kwrite(r, "kdeglobals", group, key, new)
        written.append(f"{group}/{key}")
    if written:
        # running KDE apps pick the new font up (KGlobalSettings FontChanged)
        r.run(["dbus-send", "--session", "--type=signal", "/KGlobalSettings",
               "org.kde.KGlobalSettings.notifyChange", "int32:1", "int32:0"])
    return written


def current_family() -> str:
    cur = _read("General", "font")
    return cur.split(",")[0] if cur else FIGTREE


def status(r, env=None) -> dict:
    return {"family": current_family(), "wanted": wanted_family(r, env), "languages": session_languages(env)}
