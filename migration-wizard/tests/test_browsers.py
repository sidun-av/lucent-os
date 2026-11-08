import json
import sqlite3

from lucent_migrate import browsers
from lucent_migrate.browsers import Folder, Link

from conftest import CHROME_BOOKMARKS


def test_find_profiles(windows_root):
    ivan = windows_root / "Users" / "Ivan"
    found = [(p.browser, p.name) for p in browsers.find_profiles(ivan)]
    assert found == [
        ("Google Chrome", "Default"),
        ("Google Chrome", "Profile 1"),
        ("Microsoft Edge", "Default"),
        ("Mozilla Firefox", "abcd1234.default-release"),
    ]


def test_find_profiles_none(windows_root):
    assert browsers.find_profiles(windows_root / "Users" / "maria") == []


def test_chromium_bookmarks():
    tree = browsers.parse_chromium(json.dumps(CHROME_BOOKMARKS))
    assert [c.title for c in tree.children] == ["Bookmarks bar", "Mobile bookmarks"]  # empty "other" dropped
    bar = tree.children[0]
    assert bar.toolbar
    assert bar.children[0] == Link("Госуслуги", "https://www.gosuslugi.ru/", 1655526400)
    assert bar.children[1].children[0].add_date is None


def test_firefox_bookmarks(windows_root):
    places = (windows_root / "Users" / "Ivan" / "AppData" / "Roaming" / "Mozilla" / "Firefox"
              / "Profiles" / "abcd1234.default-release" / "places.sqlite")
    tree = browsers.parse_firefox(places)
    titles = [c.title for c in tree.children]
    assert titles == ["Bookmarks Menu", "Bookmarks Toolbar"]
    menu, toolbar = tree.children
    assert toolbar.toolbar and toolbar.children == [Link("Mozilla", "https://mozilla.org/", 1700000000)]
    # place: queries and separators are dropped
    assert menu.children == [Folder("Новости", [Link("Яндекс", "https://ya.ru/", None)])]


def test_firefox_reads_uncheckpointed_wal(tmp_path):
    """places.sqlite of a running/crashed Firefox keeps recent rows in -wal."""
    db = tmp_path / "places.sqlite"
    from conftest import make_places_sqlite
    make_places_sqlite(db)
    con = sqlite3.connect(db)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA wal_autocheckpoint=0")
    con.execute("INSERT INTO moz_places VALUES (10, 'https://new.example/', 'New')")
    con.execute("INSERT INTO moz_bookmarks VALUES (20, 1, 10, 3, 5, 'Свежая', 0, 'ffffffffffff')")
    con.commit()
    assert (tmp_path / "places.sqlite-wal").stat().st_size > 0
    tree = browsers.parse_firefox(db)
    # the source directory (a read-only Windows mount in real life) is untouched
    assert sorted(p.name for p in tmp_path.iterdir()) == ["places.sqlite", "places.sqlite-shm", "places.sqlite-wal"]
    con.close()
    toolbar = tree.children[-1]
    assert "Свежая" in [c.title for c in toolbar.children]


def test_netscape_html_escapes_and_nests():
    tree = browsers.parse_chromium(CHROME_BOOKMARKS)
    html = browsers.to_netscape_html(tree)
    assert html.startswith("<!DOCTYPE NETSCAPE-Bookmark-file-1>")
    assert '<H3 PERSONAL_TOOLBAR_FOLDER="true">Bookmarks bar</H3>' in html
    assert '<A HREF="https://mail.example.com/?a=1&amp;b=2">Почта &lt;&amp;&gt;</A>' in html
    assert 'ADD_DATE="1655526400"' in html
    assert html.count("<DL><p>") == html.count("</DL><p>")


def test_count_links():
    assert browsers.count_links(browsers.parse_chromium(CHROME_BOOKMARKS)) == 3


def test_export_file_name():
    p = browsers.Profile("Google Chrome", "Profile 1", None)
    assert browsers.export_name(p) == "Bookmarks — Google Chrome (Profile 1).html"
