"""Translations, the same way as the migration wizard (lucent_migrate.i18n).

English is the source language. `po/<lang>.po` is compiled at image build
time to /usr/share/locale/<lang>/LC_MESSAGES/lucent-settings.mo (with the
wizard's .mo writer) and picked from LANGUAGE / LC_ALL / LC_MESSAGES / LANG.
QML marks its strings with `tr("...")`, Python with `_("...")`; both end up
in the same catalog.
"""

from __future__ import annotations

import gettext
import os
from pathlib import Path

DOMAIN = "lucent-settings"
LOCALEDIR = Path(os.environ.get("LUCENT_LOCALEDIR", "/usr/share/locale"))

_tr: gettext.NullTranslations | None = None


def setup(languages: list[str] | None = None, localedir: Path | None = None) -> None:
    global _tr
    _tr = gettext.translation(DOMAIN, localedir or LOCALEDIR, languages=languages, fallback=True)


def _t() -> gettext.NullTranslations:
    if _tr is None:
        setup()
    return _tr


def _(message: str) -> str:
    return _t().gettext(message)


def N_(message: str) -> str:
    return message


def ngettext(singular: str, plural: str, n: int) -> str:
    return _t().ngettext(singular, plural, n)


def language() -> str:
    """'ru', 'en', ...: the catalog actually in use (for date formats)."""
    info = _t().info()
    return (info.get("language") or "en").split("_")[0]
