"""Find browser profiles in a Windows home and export their bookmarks.

Bookmarks are written as a standard Netscape bookmarks.html, which Firefox
(Library -> Import and Backup -> Import Bookmarks from HTML) and every
other browser import. Passwords and cookies are DPAPI-encrypted on Windows
and are deliberately not touched.
"""

from __future__ import annotations

import html
import json
import shutil
import sqlite3
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from .i18n import N_, _
from .windows import child_ci

CHROMIUM = [
    ("Google Chrome", ("AppData", "Local", "Google", "Chrome", "User Data")),
    ("Microsoft Edge", ("AppData", "Local", "Microsoft", "Edge", "User Data")),
    ("Yandex Browser", ("AppData", "Local", "Yandex", "YandexBrowser", "User Data")),
    ("Opera", ("AppData", "Roaming", "Opera Software", "Opera Stable")),
]
FIREFOX = ("AppData", "Roaming", "Mozilla", "Firefox", "Profiles")

CHROME_EPOCH_OFFSET = 11_644_473_600  # seconds between 1601-01-01 and 1970-01-01


@dataclass(frozen=True)
class Link:
    title: str
    url: str
    add_date: int | None = None


@dataclass
class Folder:
    title: str
    children: list = field(default_factory=list)
    toolbar: bool = False


@dataclass(frozen=True)
class Profile:
    browser: str
    name: str
    path: Path | None

    @property
    def kind(self) -> str:
        return "firefox" if self.browser == "Mozilla Firefox" else "chromium"


def _resolve(home: Path, parts: tuple[str, ...]) -> Path | None:
    cur: Path | None = home
    for part in parts:
        cur = child_ci(cur, part) if cur else None
    return cur


def find_profiles(home: Path) -> list[Profile]:
    found: list[Profile] = []
    for browser, parts in CHROMIUM:
        base = _resolve(home, parts)
        if not base or not base.is_dir():
            continue
        if (base / "Bookmarks").is_file():  # Opera keeps a single profile here
            found.append(Profile(browser, "Default", base))
        for prof in sorted(base.iterdir(), key=lambda p: p.name):
            if prof.is_dir() and (prof / "Bookmarks").is_file():
                found.append(Profile(browser, prof.name, prof))
    ff = _resolve(home, FIREFOX)
    if ff and ff.is_dir():
        for prof in sorted(ff.iterdir(), key=lambda p: p.name):
            if (prof / "places.sqlite").is_file():
                found.append(Profile("Mozilla Firefox", prof.name, prof))
    return found


# --- Chromium -----------------------------------------------------------------

def _chrome_time(value) -> int | None:
    try:
        micros = int(value)
    except (TypeError, ValueError):
        return None
    if micros <= 0:
        return None
    return micros // 1_000_000 - CHROME_EPOCH_OFFSET


def _chromium_node(node: dict):
    if node.get("type") == "url":
        return Link(node.get("name") or node.get("url", ""), node.get("url", ""), _chrome_time(node.get("date_added")))
    children = [c for c in (_chromium_node(ch) for ch in node.get("children", [])) if c is not None]
    return Folder(node.get("name", ""), children)


def parse_chromium(data: str | dict) -> Folder:
    if isinstance(data, str):
        data = json.loads(data)
    root = Folder("Bookmarks")
    for key in ("bookmark_bar", "other", "synced"):
        node = data.get("roots", {}).get(key)
        if not node:
            continue
        folder = _chromium_node(node)
        folder.toolbar = key == "bookmark_bar"
        if folder.children:
            root.children.append(folder)
    return root


# --- Firefox --------------------------------------------------------------------

FIREFOX_ROOTS = {"menu________": (N_("Bookmarks Menu"), False), "toolbar_____": (N_("Bookmarks Toolbar"), True),
                 "unfiled_____": (N_("Other Bookmarks"), False), "mobile______": (N_("Mobile Bookmarks"), False)}


def parse_firefox(places: Path) -> Folder:
    """Read places.sqlite from a *copy*: the source is a read-only Windows
    mount, and recent bookmarks may still live only in places.sqlite-wal."""
    with tempfile.TemporaryDirectory(prefix="lucent-places-") as tmp:
        copy = Path(tmp) / "places.sqlite"
        shutil.copy2(places, copy)
        for suffix in ("-wal", "-shm"):
            side = places.with_name(places.name + suffix)
            if side.exists():
                shutil.copy2(side, copy.with_name(copy.name + suffix))
        con = sqlite3.connect(copy)
        try:
            rows = con.execute(
                "SELECT b.id, b.type, b.parent, b.title, b.dateAdded, b.guid, p.url, p.title "
                "FROM moz_bookmarks b LEFT JOIN moz_places p ON p.id = b.fk "
                "ORDER BY b.parent, b.position"
            ).fetchall()
        finally:
            con.close()

    children: dict[int, list] = {}
    by_id = {}
    for row in rows:
        children.setdefault(row[2], []).append(row)
        by_id[row[0]] = row

    def build(parent_id: int) -> list:
        out = []
        for bid, btype, _parent, title, added, _guid, url, ptitle in children.get(parent_id, []):
            if btype == 1 and url and not url.startswith("place:"):
                out.append(Link(title or ptitle or url, url, (added // 1_000_000) if added else None))
            elif btype == 2:
                out.append(Folder(title or "", build(bid)))
        return out

    root = Folder("Bookmarks")
    for guid, (title, toolbar) in FIREFOX_ROOTS.items():
        node = next((r for r in rows if r[5] == guid), None)
        if node is None:
            continue
        kids = build(node[0])
        if kids:
            root.children.append(Folder(_(title), kids, toolbar))
    return root


def read_profile(profile: Profile) -> Folder:
    assert profile.path is not None
    if profile.kind == "firefox":
        return parse_firefox(profile.path / "places.sqlite")
    return parse_chromium((profile.path / "Bookmarks").read_text(encoding="utf-8"))


# --- Export --------------------------------------------------------------------

def count_links(folder: Folder) -> int:
    return sum(count_links(c) if isinstance(c, Folder) else 1 for c in folder.children)


def _emit(folder: Folder, indent: int, out: list[str]) -> None:
    pad = "    " * indent
    out.append(f"{pad}<DL><p>")
    for child in folder.children:
        if isinstance(child, Folder):
            attr = ' PERSONAL_TOOLBAR_FOLDER="true"' if child.toolbar else ""
            out.append(f"{pad}    <DT><H3{attr}>{html.escape(child.title, quote=False)}</H3>")
            _emit(child, indent + 1, out)
        else:
            date = f' ADD_DATE="{child.add_date}"' if child.add_date else ""
            out.append(
                f'{pad}    <DT><A HREF="{html.escape(child.url, quote=True)}"{date}>'
                f"{html.escape(child.title, quote=False)}</A>"
            )
    out.append(f"{pad}</DL><p>")


def to_netscape_html(root: Folder) -> str:
    out = [
        "<!DOCTYPE NETSCAPE-Bookmark-file-1>",
        '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
        "<TITLE>Bookmarks</TITLE>",
        "<H1>Bookmarks</H1>",
    ]
    _emit(root, 0, out)
    return "\n".join(out) + "\n"


def export_name(profile: Profile) -> str:
    return _("Bookmarks — {browser} ({profile}).html").format(browser=profile.browser, profile=profile.name)
