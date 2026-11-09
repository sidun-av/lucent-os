"""English is the source language; Russian is a gettext translation. Every
string the sheet shows must have one (lucent-bridge translates its own
error explanations)."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from lucent_bridge_sheet import i18n, model

PKG = Path(i18n.__file__).parent
PO_DIR = Path(__file__).parents[1] / "po"
CYRILLIC = re.compile("[Ѐ-ӿ]")


@pytest.fixture
def ru(tmp_path):
    from lucent_migrate.i18n import compile_po
    for po in PO_DIR.glob("*.po"):
        compile_po(po, tmp_path / po.stem / "LC_MESSAGES" / f"{i18n.DOMAIN}.mo")
    i18n.setup(["ru"], tmp_path)
    yield tmp_path
    i18n.setup(["en"])


def marked_strings() -> set[str]:
    found = set()
    for path in PKG.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_"
                    and node.args and isinstance(node.args[0], ast.Constant)
                    and isinstance(node.args[0].value, str)):
                found.add(node.args[0].value)
    return found


def test_every_string_has_russian():
    from lucent_migrate.i18n import parse_po
    catalog = parse_po(PO_DIR / "ru.po")
    have = {k if isinstance(k, str) else k[-1] for k in catalog}
    marked = marked_strings()
    assert len(marked) >= 15, marked
    missing = sorted(m for m in marked if m not in have)
    assert not missing, f"no Russian for: {missing}"
    for key, value in catalog.items():
        msgid = key if isinstance(key, str) else key[-1]
        if not msgid:
            continue  # the header
        text = value if isinstance(value, str) else value[0]
        assert text, f"{msgid!r} is not translated"
        if re.search("[A-Za-z]", msgid):
            assert CYRILLIC.search(text), f"{msgid!r} is not translated"
        assert msgid.count("{}") == text.count("{}"), msgid


def test_russian_sheet(ru):
    s = model.State()
    for e in ({"v": 1, "event": "start", "name": "Установщик Notepad++", "file": "npp.exe", "size": 4_823_449,
               "installer": True, "program_arch": "x86-64", "host_arch": "ARM64", "translation": True},
              {"v": 1, "event": "step", "step": "prepare"}, {"v": 1, "event": "progress", "fraction": 0.34}):
        s = model.apply(s, e)
    assert model.title(s) == "Подготовка Windows-программы"
    assert model.mode_line(s) == "x86-64 → ARM · перевод инструкций"
    assert model.status_line(s) == "Первый запуск чуть дольше — дальше будет быстро"
    assert model.file_line(s) == "npp.exe · 4,6 МБ"
    assert model.percent(s) == "34 %"
    assert model.buttons(s) == [("cancel", "Отмена", False)]
