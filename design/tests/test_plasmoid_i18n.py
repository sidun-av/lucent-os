"""English is the primary language; every string of Lucent's own plasmoids
has a Russian translation in design/po/<domain>.ru.po, and no stale ones."""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PLASMOIDS = ROOT / "system_files/usr/share/plasma/plasmoids"
PO = ROOT / "design/po"


def qml_strings(pkg: Path) -> set[tuple[str, str]]:
    out = set()
    for f in pkg.rglob("*.qml"):
        text = f.read_text()
        for ctx, msg in re.findall(r'i18nc\("((?:[^"\\]|\\.)*)",\s*"((?:[^"\\]|\\.)*)"', text):
            out.add((ctx, msg))
        for msg in re.findall(r'(?<![\w.])i18n\("((?:[^"\\]|\\.)*)"', text):
            out.add(("", msg))
    return out


def po_entries(path: Path) -> dict[tuple[str, str], str]:
    out, ctx, msgid = {}, "", None
    for line in path.read_text().splitlines():
        if line.startswith("msgctxt "):
            ctx = line[9:-1]
        elif line.startswith("msgid "):
            msgid = line[7:-1]
        elif line.startswith("msgstr ") and msgid is not None:
            if msgid:
                out[(ctx, msgid)] = line[8:-1]
            ctx, msgid = "", None
    return out


@pytest.mark.parametrize("pkg", sorted(p.name for p in PLASMOIDS.glob("org.lucent.*")))
def test_every_string_is_translated_to_russian(pkg):
    used = qml_strings(PLASMOIDS / pkg)
    po = po_entries(PO / f"plasma_applet_{pkg}.ru.po")
    missing = sorted(m for m in used if not po.get(m))
    stale = sorted(m for m in po if m not in used)
    assert not missing, f"untranslated in {pkg}: {missing}"
    assert not stale, f"no longer used in {pkg}: {stale}"
