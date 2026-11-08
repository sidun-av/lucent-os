"""Fake Windows filesystem trees for the migration-wizard tests.

Everything here builds plain directories under pytest's tmp_path, so the
core logic is exercised against a realistic layout without NTFS, udisks or
root privileges.
"""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

import pytest

from lucent_migrate import i18n


@pytest.fixture(autouse=True)
def english_ui():
    """Tests see the source (English) strings unless they load a catalog."""
    i18n.setup(["en"])
    yield
    i18n.setup(["en"])


def write(path: Path, data: bytes | str = b"x", mtime: float | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        data = data.encode()
    path.write_bytes(data)
    if mtime is not None:
        os.utime(path, (mtime, mtime))
    return path


CHROME_BOOKMARKS = {
    "checksum": "0",
    "version": 1,
    "roots": {
        "bookmark_bar": {
            "type": "folder",
            "name": "Bookmarks bar",
            "date_added": "13300000000000000",
            "children": [
                {
                    "type": "url",
                    "name": "Госуслуги",
                    "url": "https://www.gosuslugi.ru/",
                    "date_added": "13300000000000000",
                },
                {
                    "type": "folder",
                    "name": "Работа",
                    "date_added": "13300000000000000",
                    "children": [
                        {
                            "type": "url",
                            "name": "Почта <&>",
                            "url": "https://mail.example.com/?a=1&b=2",
                            "date_added": "0",
                        }
                    ],
                },
            ],
        },
        "other": {"type": "folder", "name": "Other bookmarks", "children": []},
        "synced": {
            "type": "folder",
            "name": "Mobile bookmarks",
            "children": [
                {"type": "url", "name": "Wiki", "url": "https://ru.wikipedia.org/"}
            ],
        },
    },
}


def make_places_sqlite(path: Path) -> None:
    """Minimal subset of the Firefox places.sqlite schema."""
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.executescript(
        """
        CREATE TABLE moz_places (id INTEGER PRIMARY KEY, url TEXT, title TEXT);
        CREATE TABLE moz_bookmarks (
            id INTEGER PRIMARY KEY, type INTEGER, fk INTEGER, parent INTEGER,
            position INTEGER, title TEXT, dateAdded INTEGER, guid TEXT);
        INSERT INTO moz_places VALUES (1, 'https://mozilla.org/', 'Mozilla');
        INSERT INTO moz_places VALUES (2, 'https://ya.ru/', 'Яндекс');
        INSERT INTO moz_places VALUES (3, 'place:sort=8', NULL);
        INSERT INTO moz_bookmarks VALUES (1, 2, NULL, 0, 0, '', 0, 'root________');
        INSERT INTO moz_bookmarks VALUES (2, 2, NULL, 1, 0, 'menu', 0, 'menu________');
        INSERT INTO moz_bookmarks VALUES (3, 2, NULL, 1, 1, 'toolbar', 0, 'toolbar_____');
        INSERT INTO moz_bookmarks VALUES (4, 2, NULL, 1, 2, 'tags', 0, 'tags________');
        INSERT INTO moz_bookmarks VALUES (5, 1, 1, 3, 0, 'Mozilla', 1700000000000000, 'aaaaaaaaaaaa');
        INSERT INTO moz_bookmarks VALUES (6, 2, NULL, 2, 0, 'Новости', 0, 'bbbbbbbbbbbb');
        INSERT INTO moz_bookmarks VALUES (7, 1, 2, 6, 0, 'Яндекс', 0, 'cccccccccccc');
        INSERT INTO moz_bookmarks VALUES (8, 1, 3, 2, 1, 'Smart', 0, 'dddddddddddd');
        INSERT INTO moz_bookmarks VALUES (9, 3, NULL, 2, 2, NULL, 0, 'eeeeeeeeeeee');
        """
    )
    con.commit()
    con.close()


WLAN_XML = """<?xml version="1.0"?>
<WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
  <name>{name}</name>
  <SSIDConfig><SSID><hex>{hex}</hex><name>{ssid}</name></SSID></SSIDConfig>
  <connectionType>ESS</connectionType>
  <MSM><security>
    <authEncryption><authentication>{auth}</authentication>
      <encryption>AES</encryption><useOneX>false</useOneX></authEncryption>
    {key}
  </security></MSM>
</WLANProfile>
"""

WLAN_KEY = """<sharedKey><keyType>passPhrase</keyType><protected>true</protected>
      <keyMaterial>01000000D08C9DDF0115D1118C7A00C04FC297EB0100</keyMaterial></sharedKey>"""


def wlan_profile(ssid: str, auth: str, with_key: bool = True) -> str:
    return WLAN_XML.format(
        name=ssid.replace("&", "&amp;"),
        ssid=ssid.replace("&", "&amp;"),
        hex=ssid.encode().hex().upper(),
        auth=auth,
        key=WLAN_KEY if with_key else "",
    )


@pytest.fixture
def windows_root(tmp_path: Path) -> Path:
    """A fake mounted Windows system volume (what udisks would give us)."""
    root = tmp_path / "OS"
    write(root / "Windows" / "System32" / "ntoskrnl.exe")
    write(root / "pagefile.sys")

    ivan = root / "Users" / "Ivan"
    write(ivan / "NTUSER.DAT")
    write(ivan / "Documents" / "Отчёт.docx", b"a" * 100)
    write(ivan / "Documents" / "desktop.ini", b"[.ShellClassInfo]")
    write(ivan / "Documents" / "Проекты" / "план.xlsx", b"b" * 50)
    write(ivan / "Pictures" / "Отпуск" / "IMG_0001.jpg", b"c" * 300)
    write(ivan / "Pictures" / "Thumbs.db", b"junk")
    write(ivan / "Desktop" / "заметка.txt", b"d" * 10)
    write(ivan / "Downloads" / "setup.exe", b"e" * 1000)
    write(ivan / "Music" / "song.mp3", b"f" * 20)
    (ivan / "Videos").mkdir(parents=True)
    # Windows legacy junction ("My Music" inside Documents) shows up as a
    # symlink on Linux NTFS drivers; it must not be followed or double-counted.
    os.symlink(ivan / "Music", ivan / "Documents" / "Моя музыка")

    local = ivan / "AppData" / "Local"
    chrome = local / "Google" / "Chrome" / "User Data"
    write(chrome / "Default" / "Bookmarks", json.dumps(CHROME_BOOKMARKS))
    write(chrome / "Profile 1" / "Bookmarks", json.dumps(CHROME_BOOKMARKS))
    write(chrome / "System Profile" / "Preferences", "{}")
    edge = local / "Microsoft" / "Edge" / "User Data"
    write(edge / "Default" / "Bookmarks", json.dumps(CHROME_BOOKMARKS))
    make_places_sqlite(
        ivan / "AppData" / "Roaming" / "Mozilla" / "Firefox" / "Profiles"
        / "abcd1234.default-release" / "places.sqlite"
    )

    # Second user whose Desktop/Documents are redirected to OneDrive.
    maria = root / "Users" / "maria"
    write(maria / "NTUSER.DAT")
    write(maria / "OneDrive" / "Documents" / "диплом.pdf", b"g" * 70)
    write(maria / "OneDrive" / "Desktop" / "todo.txt", b"h" * 5)
    write(maria / "Pictures" / "cat.png", b"i" * 40)

    for system in ("Public", "Default", "Default User", "All Users", "defaultuser0"):
        write(root / "Users" / system / "Documents" / "readme.txt")
    write(root / "Users" / "desktop.ini")

    ifaces = root / "ProgramData" / "Microsoft" / "Wlansvc" / "Profiles" / "Interfaces"
    guid = "{5E2A7A1B-0000-4000-8000-000000000001}"
    write(ifaces / guid / "{AAAA0001-0000-0000-0000-000000000000}.xml", wlan_profile("HomeNet", "WPA2PSK"))
    write(ifaces / guid / "{AAAA0002-0000-0000-0000-000000000000}.xml", wlan_profile("Кафе & Ко", "open", with_key=False))
    write(ifaces / guid / "{AAAA0003-0000-0000-0000-000000000000}.xml", wlan_profile("Office", "WPA2"))
    write(ifaces / guid / "{AAAA0004-0000-0000-0000-000000000000}.xml", "<not xml")
    write(ifaces / guid / "{AAAA0005-0000-0000-0000-000000000000}.xml", wlan_profile("HomeNet", "WPA2PSK"))
    return root
