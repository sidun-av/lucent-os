"""English is the source language; Russian is a gettext translation.
Every string the store shows (Python, QML, catalog.toml) must have one."""

import ast
import re
from pathlib import Path

import pytest

from lucent_store import catalog, i18n

PKG = Path(i18n.__file__).parent
PO_DIR = Path(__file__).parents[1] / "po"
CYRILLIC = re.compile("[Ѐ-ӿ]")
QML_TEXT = re.compile(r'l10n\.text\(\s*"((?:[^"\\]|\\.)*)"\s*\)')
QML_CTEXT = re.compile(r'l10n\.ctext\(\s*"([^"]*)"\s*,\s*"([^"]*)"\s*\)')
QML_PLURAL = re.compile(r'l10n\.plural\(\s*"((?:[^"\\]|\\.)*)"\s*,\s*"((?:[^"\\]|\\.)*)"')


@pytest.fixture
def ru(tmp_path):
    from lucent_migrate.i18n import compile_po
    for po in PO_DIR.glob("*.po"):
        compile_po(po, tmp_path / po.stem / "LC_MESSAGES" / f"{i18n.DOMAIN}.mo")
    i18n.setup(["ru"], tmp_path)
    yield tmp_path
    i18n.setup(["en"])


def context_strings() -> set[tuple[str, str]]:
    found = set()
    for path in (PKG / "qml").glob("*.qml"):
        found |= set(QML_CTEXT.findall(path.read_text(encoding="utf-8")))
    return found


def marked_strings() -> set[str]:
    found = set()
    for path in PKG.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                    and node.func.id in ("_", "N_", "ngettext") and node.args \
                    and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                found.add(node.args[0].value)
    for path in (PKG / "qml").glob("*.qml"):
        text = path.read_text(encoding="utf-8")
        found |= {m.encode().decode("unicode_escape") if "\\" in m else m for m in QML_TEXT.findall(text)}
        found |= {s for s, _p in QML_PLURAL.findall(text)}
    found |= set(catalog.load().translatable_strings())
    return found


def test_english_is_the_source_language():
    assert i18n._("Install") == "Install"
    assert i18n.language() == "en"


def test_russian_catalog_loads(ru):
    assert i18n.language() == "ru"
    assert i18n._("Install") == "Установить"
    assert i18n._("Instead of") == "Вместо"
    assert i18n.pgettext("sidebar", "Installed") == "Установленные"
    assert i18n._("Installed") == "Установлено"
    assert i18n._("Opens and saves .docx without losing formatting") == "Открывает и сохраняет .docx без потерь"


def test_russian_plurals(ru):
    forms = [i18n.ngettext("{n} app found", "{n} apps found", n).format(n=n) for n in (1, 3, 5, 21)]
    assert forms == ["Найдена 1 программа", "Найдены 3 программы", "Найдено 5 программ", "Найдена 21 программа"]


def test_every_ui_string_has_a_russian_translation():
    po = i18n_catalog = {}
    from lucent_migrate.i18n import parse_po
    po = parse_po(PO_DIR / "ru.po")
    i18n_catalog = {msgid: value for (_ctx, msgid), value in po.items()}
    marked = marked_strings()
    assert len(marked) > 150
    missing = sorted(m for m in marked if not i18n_catalog.get(m))
    assert missing == []
    assert context_strings() and all(po.get(k) for k in context_strings())


def test_no_unused_translations():
    from lucent_migrate.i18n import parse_po
    po = parse_po(PO_DIR / "ru.po")
    plain = {msgid for (ctx, msgid) in po if msgid and ctx is None}
    assert sorted(plain - marked_strings()) == []
    assert sorted(k for k in po if k[0] is not None and k not in context_strings()) == []


def test_no_russian_left_in_source():
    for path in list(PKG.glob("*.py")) + list((PKG / "qml").glob("*.qml")) + [PKG / "catalog.toml"]:
        assert not CYRILLIC.search(path.read_text(encoding="utf-8")), path.name
