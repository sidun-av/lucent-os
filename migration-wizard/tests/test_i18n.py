"""English is the source language; Russian is a gettext translation."""

import ast
import re
from pathlib import Path

import pytest

from lucent_migrate import drive_letters, i18n, volumes

PKG = Path(i18n.__file__).parent
PO_DIR = Path(__file__).parents[1] / "po"
CYRILLIC = re.compile("[Ѐ-ӿ]")


@pytest.fixture
def ru(tmp_path):
    for po in PO_DIR.glob("*.po"):
        out = tmp_path / po.stem / "LC_MESSAGES" / f"{i18n.DOMAIN}.mo"
        out.parent.mkdir(parents=True)
        i18n.compile_po(po, out)
    i18n.setup(["ru"], tmp_path)
    yield tmp_path
    i18n.setup(["en"])


def test_english_is_the_source_language():
    i18n.setup(["en"])
    assert i18n._("Move from Windows") == "Move from Windows"
    assert drive_letters.display_name("C", None) == "Local Disk (C:)"
    assert volumes.human_size(1536) == "1.5 KB"


def test_russian_catalog_loads(ru):
    assert i18n._("Move from Windows") == "Переезд с Windows"
    assert drive_letters.display_name("C", None) == "Локальный диск (C:)"
    assert drive_letters.display_name("D", "Data") == "Data (D:)"
    assert volumes.human_size(1536) == "1,5 КБ"


def test_russian_plurals(ru):
    forms = [i18n.ngettext("{n} file", "{n} files", n).format(n=n) for n in (1, 2, 5, 21)]
    assert forms == ["1 файл", "2 файла", "5 файлов", "21 файл"]


def test_language_follows_environment(ru, monkeypatch):
    for var in ("LANGUAGE", "LC_ALL", "LC_MESSAGES"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("LANG", "ru_RU.UTF-8")
    i18n.setup(localedir=ru)
    assert i18n._("Done") == "Готово"
    monkeypatch.setenv("LANG", "en_US.UTF-8")
    i18n.setup(localedir=ru)
    assert i18n._("Done") == "Done"
    monkeypatch.setenv("LANG", "C.UTF-8")
    i18n.setup(localedir=ru)
    assert i18n._("Done") == "Done"


def _marked_strings():
    """Every literal passed to _(), N_(), ngettext() or pgettext() in the package."""
    found = set()
    for path in PKG.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
                continue
            args = [a.value for a in node.args if isinstance(a, ast.Constant) and isinstance(a.value, str)]
            if node.func.id in ("_", "N_") and args:
                found.add((None, args[0]))
            elif node.func.id == "ngettext" and len(args) >= 2:
                found.add((None, args[0]))
            elif node.func.id == "pgettext" and len(args) >= 2:
                found.add((args[0], args[1]))
    return found


def test_every_ui_string_has_a_russian_translation():
    catalog = i18n.parse_po(PO_DIR / "ru.po")
    marked = _marked_strings()
    assert len(marked) > 40
    missing = sorted(m for m in marked if not catalog.get(m))
    assert missing == []


def test_no_untranslatable_russian_left_in_source():
    for path in PKG.glob("*.py"):
        assert not CYRILLIC.search(path.read_text(encoding="utf-8")), path.name
