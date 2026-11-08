"""Translations for Lucent's own UI.

English is the source language. Other languages are gettext catalogs
(`po/<lang>.po` in the source tree, compiled at image build time to
`/usr/share/locale/<lang>/LC_MESSAGES/lucent.mo`) and are picked from the
usual LANGUAGE / LC_ALL / LC_MESSAGES / LANG environment, so the wizard
follows the language the user chose in the installer or System Settings.

`compile_po` is a small msgfmt replacement (the image doesn't carry
gettext-devel tools); it supports contexts and plural forms.
"""

from __future__ import annotations

import ast
import gettext
import os
import struct
import sys
from pathlib import Path

DOMAIN = "lucent"
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
    return _t().gettext(message)


def N_(message: str) -> str:
    """Mark a string for translation without translating it yet."""
    return message


def ngettext(singular: str, plural: str, n: int) -> str:
    return _t().ngettext(singular, plural, n)


def pgettext(context: str, message: str) -> str:
    return _t().pgettext(context, message)


# --- .po -> .mo -------------------------------------------------------------------

Key = tuple[str | None, str]


def _entries(path: Path) -> list[dict]:
    """Parse a .po file into dicts with msgctxt/msgid/msgid_plural/msgstr/msgstr[N].
    Fuzzy entries (except the header) are dropped."""
    out: list[dict] = []
    cur: dict[str, str] = {}
    fuzzy = False
    field = ""

    def flush():
        nonlocal cur, fuzzy
        if "msgid" in cur and not (fuzzy and cur["msgid"]):
            out.append(cur)
        cur, fuzzy = {}, False

    for raw in path.read_text(encoding="utf-8").splitlines() + [""]:
        line = raw.strip()
        if not line:
            flush()
        elif line.startswith("#"):
            fuzzy = fuzzy or (line.startswith("#,") and "fuzzy" in line)
        elif line.startswith('"'):
            cur[field] += ast.literal_eval(line)
        else:
            name, _sep, value = line.partition(" ")
            if name in ("msgctxt", "msgid") and any(k.startswith("msgstr") for k in cur):
                flush()
            field = name
            cur[field] = ast.literal_eval(value)
    return out


def _plural_strs(entry: dict) -> list[str]:
    return [entry[k] for k in sorted((k for k in entry if k.startswith("msgstr[")),
                                     key=lambda k: int(k[7:-1]))]


def parse_po(path: Path) -> dict[Key, str | list[str]]:
    """Map (msgctxt, msgid) -> msgstr, or the list of plural msgstrs."""
    return {
        (e.get("msgctxt"), e["msgid"]): _plural_strs(e) if "msgid_plural" in e else e.get("msgstr", "")
        for e in _entries(path)
    }


def compile_po(po: Path, mo: Path) -> None:
    """Write a GNU .mo catalog (what `msgfmt` does), skipping untranslated entries."""
    catalog: dict[bytes, bytes] = {}
    for e in _entries(po):
        key = e["msgid"]
        if "msgctxt" in e:
            key = e["msgctxt"] + "\x04" + key
        if "msgid_plural" in e:
            strs = _plural_strs(e)
            if not all(strs):
                continue
            key += "\0" + e["msgid_plural"]
            value = "\0".join(strs)
        else:
            value = e.get("msgstr", "")
            if not value:
                continue
        catalog[key.encode()] = value.encode()
    keys = sorted(catalog)
    n = len(keys)
    ids = strs = b""
    offsets = []
    for k in keys:
        offsets.append((len(ids), len(k), len(strs), len(catalog[k])))
        ids += k + b"\0"
        strs += catalog[k] + b"\0"
    start = 7 * 4 + 16 * n
    table_ids = b"".join(struct.pack("<2I", ln, start + o) for o, ln, _so, _sl in offsets)
    table_strs = b"".join(struct.pack("<2I", ln, start + len(ids) + o) for _io, _il, o, ln in offsets)
    header = struct.pack("<7I", 0x950412DE, 0, n, 7 * 4, 7 * 4 + 8 * n, 0, 0)
    mo.parent.mkdir(parents=True, exist_ok=True)
    mo.write_bytes(header + table_ids + table_strs + ids + strs)


def main(argv: list[str]) -> int:
    """python3 -m lucent_migrate.i18n PO_DIR LOCALEDIR  (used by build.sh)"""
    po_dir, localedir = Path(argv[1]), Path(argv[2])
    for po in sorted(po_dir.glob("*.po")):
        compile_po(po, localedir / po.stem / "LC_MESSAGES" / f"{DOMAIN}.mo")
        print(f"{po.name} -> {localedir / po.stem}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
