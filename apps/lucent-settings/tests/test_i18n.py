"""English is the source language; Russian is a gettext translation of every
string the Python code (_(), N_(), ngettext()) and the QML (System.tr(),
System.trn()) shows."""

import ast
import re
from pathlib import Path

import pytest

from lucent_migrate.i18n import compile_po, parse_po  # the shared .mo writer
from lucent_settings import i18n

PKG = Path(i18n.__file__).parent
PO = Path(__file__).parents[1] / "po" / "ru.po"
CYRILLIC = re.compile("[Ѐ-ӿ]")
QML_TR = re.compile(r'System\.tr\(\s*"((?:[^"\\]|\\.)*)"\s*\)')
QML_TRN = re.compile(r'System\.trn\(\s*"((?:[^"\\]|\\.)*)"\s*,\s*"((?:[^"\\]|\\.)*)"')


def marked_strings() -> set[str]:
    found = set()
    for path in PKG.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
                continue
            args = [a.value for a in node.args if isinstance(a, ast.Constant) and isinstance(a.value, str)]
            if node.func.id in ("_", "N_", "ngettext") and args:
                found.add(args[0])
    for path in PKG.rglob("*.qml"):
        text = path.read_text(encoding="utf-8")
        found |= {m.encode().decode("unicode_escape") if "\\" in m else m for m in QML_TR.findall(text)}
        found |= {m[0] for m in QML_TRN.findall(text)}
    return found


@pytest.fixture
def ru(tmp_path):
    out = tmp_path / "ru" / "LC_MESSAGES" / f"{i18n.DOMAIN}.mo"
    out.parent.mkdir(parents=True)
    compile_po(PO, out)
    i18n.setup(["ru"], tmp_path)
    yield tmp_path
    i18n.setup(["en"])


def test_english_is_the_source_language():
    i18n.setup(["en"])
    assert i18n._("Wi-Fi & Network") == "Wi-Fi & Network"
    assert i18n.language() == "en"


def test_russian_catalog_loads(ru):
    assert i18n._("Wi-Fi & Network") == "Wi-Fi и сеть"
    assert i18n._("Appearance") == "Оформление"
    assert i18n._("Like Windows") == "Как в Windows"
    assert i18n.language() == "ru"


def test_russian_plurals(ru):
    forms = [i18n.ngettext("{n} app can be updated: {names}", "{n} apps can be updated: {names}", n)
             .format(n=n, names="X") for n in (1, 3, 5)]
    assert forms == ["Можно обновить {n} программу: X".format(n=1), "Можно обновить 3 программы: X",
                     "Можно обновить 5 программ: X"]


def test_every_ui_string_has_a_russian_translation():
    catalog = parse_po(PO)
    marked = marked_strings()
    assert len(marked) > 150
    missing = sorted(m for m in marked if not catalog.get((None, m)))
    assert missing == []


def test_catalog_has_no_stale_entries():
    catalog = {k[1] for k in parse_po(PO) if k[1]}
    assert sorted(catalog - marked_strings()) == []


def test_placeholders_survive_translation():
    for (_ctx, msgid), msgstr in parse_po(PO).items():
        if not msgid:
            continue
        for s in (msgstr if isinstance(msgstr, list) else [msgstr]):
            assert set(re.findall(r"\{\w+\}", msgid)) == set(re.findall(r"\{\w+\}", s)), msgid


def test_no_untranslatable_russian_left_in_source():
    for path in list(PKG.rglob("*.py")) + list(PKG.rglob("*.qml")):
        assert not CYRILLIC.search(path.read_text(encoding="utf-8")), path.name
