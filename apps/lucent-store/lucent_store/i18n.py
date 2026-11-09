"""Translations for Lucent Store.

English is the source language. Other languages are gettext catalogs
(`apps/lucent-store/po/<lang>.po`, compiled at image build time to
`/usr/share/locale/<lang>/LC_MESSAGES/lucent-store.mo`) picked from the usual
LANGUAGE / LC_ALL / LC_MESSAGES / LANG environment, exactly like the
migration wizard (whose dependency-free .po -> .mo writer is reused).

Python code marks strings with `_()` / `N_()` / `ngettext()`; QML calls
`l10n.text("...")`, `l10n.plural("...", "...", n)` and
`l10n.ctext("context", "...")`; catalog.toml strings are
translated when shown. tests/test_i18n.py checks all three have Russian.
"""

from __future__ import annotations

import gettext
import os
import sys
from pathlib import Path

DOMAIN = "lucent-store"
LOCALEDIR = Path(os.environ.get("LUCENT_LOCALEDIR", "/usr/share/locale"))

_tr: gettext.NullTranslations | None = None


def setup(languages: list[str] | None = None, localedir: Path | None = None) -> None:
    """(Re)load the catalog; languages=None means: from the environment."""
    global _tr
    _tr = gettext.translation(DOMAIN, localedir or LOCALEDIR, languages=languages, fallback=True)


def _t() -> gettext.NullTranslations:
    if _tr is None:
        setup()
    return _tr


def _(message: str) -> str:
    return _t().gettext(message) if message else message


def N_(message: str) -> str:
    """Mark a string for translation without translating it yet."""
    return message


def ngettext(singular: str, plural: str, n: int) -> str:
    return _t().ngettext(singular, plural, n)


def pgettext(context: str, message: str) -> str:
    return _t().pgettext(context, message)


def language() -> str:
    """Two-letter UI language the catalog was picked for ("en" when untranslated)."""
    info = _t().info()
    lang = info.get("language", "") if isinstance(info, dict) else ""
    return (lang or "en").split("_")[0].lower()


def main(argv: list[str]) -> int:
    """python3 -m lucent_store.i18n PO_DIR LOCALEDIR  (used by build.sh)"""
    from lucent_migrate.i18n import compile_po

    po_dir, localedir = Path(argv[1]), Path(argv[2])
    for po in sorted(po_dir.glob("*.po")):
        compile_po(po, localedir / po.stem / "LC_MESSAGES" / f"{DOMAIN}.mo")
        print(f"{po.name} -> {localedir / po.stem}/LC_MESSAGES/{DOMAIN}.mo")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
