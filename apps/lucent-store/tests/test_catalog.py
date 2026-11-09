"""The curated catalog we ship (lucent_store/catalog.toml)."""

import re

import pytest

from lucent_store import catalog
from lucent_store.catalog import CatalogError

APP_ID = re.compile(r"^[A-Za-z_][\w-]*(\.[A-Za-z_][\w-]*){2,}$")


@pytest.fixture(scope="module")
def cat():
    return catalog.load()


def test_ships_a_versioned_catalog(cat):
    assert cat.schema == 1
    assert re.fullmatch(r"\d{4}\.\d{2}\.\d{2}(\.\d+)?", cat.version)


def test_home_starts_with_the_mockup_cards(cat):
    first = [(r.windows, r.name) for r in cat.replacements[:6]]
    assert first == [
        ("Microsoft Word", "ONLYOFFICE Docs"), ("Adobe Photoshop", "GIMP"),
        ("Adobe Acrobat", "Okular + PDF Arranger"), ("Adobe Illustrator", "Inkscape"),
        ("Adobe Lightroom", "darktable"), ("Adobe Premiere", "Kdenlive"),
    ]
    windows = {r.windows for r in cat.replacements}
    for name in ("Microsoft Excel", "Microsoft PowerPoint", "Adobe InDesign", "Adobe Audition",
                 "Notepad++", "7-Zip"):
        assert name in windows


def test_every_referenced_app_is_described(cat):
    for r in cat.replacements:
        assert r.apps and all(a in cat.apps for a in r.apps), r.windows
    for c in cat.categories:
        assert all(a in cat.apps for a in c.apps), c.id
        assert len(set(c.apps)) == len(c.apps), c.id


def test_app_ids_look_like_flatpak_ids(cat):
    for app_id, app in cat.apps.items():
        assert APP_ID.match(app_id), app_id
        assert app.name and app.summary
    for ng in cat.nextgen:
        assert APP_ID.match(ng.id), ng.id


def test_sidebar_categories_in_mockup_order(cat):
    assert [c.id for c in cat.categories] == [
        "office", "graphics", "media", "internet", "games", "development", "windows"]
    assert cat.category("graphics").icon == "brush"
    assert cat.category("nope") is None


def test_system_apps_are_not_flatpaks(cat):
    ark = cat.apps["org.kde.ark"]
    assert ark.system == "org.kde.ark.desktop"
    assert cat.apps["org.gimp.GIMP"].system is None


def test_no_artcraft_app_with_machine_learning(cat):
    # PhotoCraft (face detection) and PdfCraft (neural OCR, AI menu) are held
    # back, and so is the launcher (sandbox escape, unchecked installs).
    ids = {n.id for n in cat.nextgen}
    assert not ids & {"ai.storyteller.photocraft", "ai.storyteller.pdfcraft", "ai.storyteller.artcraft-launcher"}


def test_nextgen_is_pinned_and_hashed(cat):
    keys = [n.key for n in cat.nextgen]
    assert keys == ["vectorcraft", "wordcraft", "gridcraft", "deckcraft"]
    for n in cat.nextgen:
        assert re.fullmatch(r"v\d+\.\d+\.\d+", n.version)
        assert set(n.sha256) == {"x86_64", "aarch64"}
        assert all(re.fullmatch(r"[0-9a-f]{64}", h) for h in n.sha256.values())
        assert n.repo == f"storytold/{n.key}"


def test_replacements_for_a_windows_name(cat):
    hits = cat.replacements_matching("photoshop")
    assert [r.name for r in hits] == ["GIMP"]
    assert [r.name for r in cat.replacements_matching("word")][0] == "ONLYOFFICE Docs"
    assert cat.replacements_matching("") == []


def test_translatable_strings_cover_all_visible_text(cat):
    strings = set(cat.translatable_strings())
    assert "Opens and saves .docx without losing formatting" in strings
    assert "Graphics & Photo" in strings
    assert "Word processor" in strings
    assert "Microsoft Word" not in strings      # product names stay as they are


def test_rejects_unknown_schema(tmp_path):
    bad = tmp_path / "c.toml"
    bad.write_text('schema = 2\nversion = "2026.01.01"\n')
    with pytest.raises(CatalogError, match="schema"):
        catalog.load(bad)


def test_rejects_dangling_references(tmp_path):
    bad = tmp_path / "c.toml"
    bad.write_text('schema = 1\nversion = "2026.01.01"\n'
                   '[[replacement]]\nwindows = "X"\napps = ["org.example.Missing"]\nname = "Y"\ndescription = "Z"\n')
    with pytest.raises(CatalogError, match="org.example.Missing"):
        catalog.load(bad)
