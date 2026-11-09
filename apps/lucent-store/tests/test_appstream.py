"""Reading Flathub's local AppStream data and searching it."""

from pathlib import Path

from lucent_store import appstream, catalog
from lucent_store.appstream import search


def load(path, lang="en"):
    return appstream.load(path, lang=lang)


def test_loads_desktop_apps_keyed_by_flatpak_id(appstream_file):
    apps = load(appstream_file)
    # okular's AppStream <id> is "org.kde.okular.desktop"; the Flatpak id wins.
    assert set(apps) == {"org.gimp.GIMP", "org.kde.okular", "org.kde.krita",
                         "com.example.PhotoShopPro", "com.example.Photon"}


def test_app_fields(appstream_file):
    gimp = load(appstream_file)["org.gimp.GIMP"]
    assert gimp.name == "GNU Image Manipulation Program"
    assert gimp.summary == "High-end image creation and manipulation"
    assert gimp.license == "GPL-3.0+ AND LGPL-3.0+"
    assert gimp.verified is True
    assert gimp.developer == "The GIMP team"
    assert gimp.version == "3.2.8"
    assert gimp.homepage == "https://www.gimp.org/"
    assert gimp.icon == "org.gimp.GIMP.png"
    assert gimp.remote_icon.endswith("/128x128/org.gimp.GIMP.png")
    assert gimp.categories == ("Graphics", "2DGraphics")
    assert "photoshop" in gimp.keywords
    assert gimp.desktop_id == "org.gimp.GIMP.desktop"
    assert gimp.runtime == "org.gnome.Platform/x86_64/51"


def test_description_becomes_simple_rich_text(appstream_file):
    gimp = load(appstream_file)["org.gimp.GIMP"]
    assert gimp.description == ("<p>GIMP is an acronym for GNU Image Manipulation Program.</p>"
                                "<p>It can be used as:</p>"
                                "<ul><li>a paint program</li><li>a photo retouching program</li></ul>")


def test_screenshots_prefer_a_mid_size_thumbnail(appstream_file):
    shots = load(appstream_file)["org.gimp.GIMP"].screenshots
    assert shots[0].url == "https://dl.flathub.org/media/gimp-1-1248.png"
    assert shots[0].caption == "Editing an illustration"
    assert shots[1].url == "https://dl.flathub.org/media/gimp-2.png"


def test_localised_fields(appstream_file):
    gimp = load(appstream_file, lang="ru")["org.gimp.GIMP"]
    assert gimp.name == "Редактор изображений GNU"
    assert gimp.summary == "Профессиональная обработка и создание изображений"
    assert gimp.developer == "Команда GIMP"
    assert gimp.description == "<p>GIMP — свободный редактор.</p>"
    assert gimp.screenshots[0].caption == "Редактирование иллюстрации"
    # Keywords from both languages, so English searches still work.
    assert {"photoshop", "фото"} <= set(gimp.keywords)
    krita = load(appstream_file, lang="ru")["org.kde.krita"]
    assert krita.name == "Krita"                       # falls back to the default


def test_unverified_and_developer_name(appstream_file):
    apps = load(appstream_file)
    assert apps["org.kde.okular"].developer == "KDE"
    assert apps["org.kde.krita"].verified is False


def test_missing_file_gives_an_empty_index(tmp_path):
    assert appstream.load(tmp_path / "nope.xml.gz") == {}


def test_find_appstream_file(tmp_path):
    base = tmp_path / "flatpak"
    path = base / "appstream" / "flathub" / "x86_64" / "active" / "appstream.xml.gz"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"")
    assert appstream.find_file([base], "flathub", "x86_64") == path
    assert appstream.find_file([base], "flathub", "aarch64") is None
    assert appstream.icon_dirs(path) == [path.parent / "icons" / "128x128", path.parent / "icons" / "64x64"]


# --- search -----------------------------------------------------------------

def names(results):
    return [a.id for a in results]


def test_search_ranks_name_matches_first(appstream_file):
    apps = load(appstream_file)
    assert names(search(apps, "krita")) == ["org.kde.krita"]
    res = names(search(apps, "photo"))
    # Whole word in the name > name prefix > keyword; console apps never show.
    assert res[:2] == ["com.example.PhotoShopPro", "com.example.Photon"]
    assert "org.kde.krita" in res and "com.example.photocli" not in res


def test_search_all_words_must_match(appstream_file):
    apps = load(appstream_file)
    assert names(search(apps, "document viewer")) == ["org.kde.okular"]
    assert search(apps, "document painting") == []
    assert search(apps, "   ") == []


def test_search_is_case_and_accent_insensitive(appstream_file):
    apps = load(appstream_file, lang="ru")
    assert names(search(apps, "ФОТО"))[0] == "org.gimp.GIMP"
    assert names(search(apps, "OKULAR")) == ["org.kde.okular"]


def test_windows_program_names_find_the_replacement(appstream_file):
    apps = load(appstream_file)
    cat = catalog.load()
    # "photoshop" is only a GIMP keyword, but the catalog card puts it first
    # even above an app literally named "Photo Shop Pro".
    assert names(search(apps, "photoshop", cat))[0] == "org.gimp.GIMP"
    assert names(search(apps, "acrobat", cat)) == ["org.kde.okular"]


def test_verified_and_curated_apps_win_ties(appstream_file):
    apps = load(appstream_file)
    cat = catalog.load()
    res = names(search(apps, "photo", cat))
    # Krita has the exact keyword, GIMP only "photoshop", but GIMP is
    # verified and in the curated catalog.
    assert res.index("org.gimp.GIMP") < res.index("org.kde.krita")


def test_category_names_bring_the_curated_page(appstream_file):
    apps = load(appstream_file)
    res = names(search(apps, "office", catalog.load()))
    assert res == ["org.kde.okular"]       # in the Office category, no "office" in its text


def test_one_letter_is_not_a_query(appstream_file):
    assert search(load(appstream_file), "p") == []


def test_license_kind():
    assert appstream.license_kind("GPL-3.0+ AND LGPL-3.0+") == "free"
    assert appstream.license_kind("MIT") == "free"
    assert appstream.license_kind("LicenseRef-proprietary") == "proprietary"
    assert appstream.license_kind("LicenseRef-proprietary=https://zoom.us/terms") == "proprietary"
    assert appstream.license_kind("LicenseRef-scancode-free-unknown") == "unknown"
    assert appstream.license_kind("") == "unknown"


def test_fold():
    assert appstream.fold("Café") == "cafe"
    assert appstream.fold("ЁЖ") == appstream.fold("ЕЖ")   # yo == ye


def test_curated_summaries_are_searched(appstream_file):
    apps = load(appstream_file)
    # Okular's own AppStream text says "Document Viewer"; the catalog says PDFs.
    assert "org.kde.okular" in names(search(apps, "sign", catalog.load()))
    assert "org.kde.okular" not in names(search(apps, "sign"))
