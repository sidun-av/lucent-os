"""Flathub's AppStream data, read from the local flatpak cache, and search.

flatpak keeps each remote's AppStream collection at
`<installation>/appstream/<remote>/<arch>/active/appstream.xml.gz`, with
cached icons next to it. Search reads only that file: typing in the search
field never touches the network and nothing about it leaves the computer.

Apps are keyed by their Flatpak id (from `<bundle>`), which for some KDE
apps differs from the AppStream `<id>` ("org.kde.okular.desktop").
"""

from __future__ import annotations

import gzip
import html
import re
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from .catalog import Catalog

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
SYSTEM_DIRS = [Path("/var/lib/flatpak")]


@dataclass(frozen=True)
class Screenshot:
    url: str
    caption: str = ""


@dataclass(frozen=True)
class AppInfo:
    id: str
    name: str
    summary: str = ""
    description: str = ""          # simple rich text: <p>, <ul>/<ol>, <li>
    developer: str = ""
    license: str = ""
    verified: bool = False
    version: str = ""
    homepage: str = ""
    icon: str = ""                 # file name in the cached icon dirs
    remote_icon: str = ""
    categories: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()  # lower-case
    screenshots: tuple[Screenshot, ...] = ()
    desktop_id: str = ""
    runtime: str = ""
    _fold: dict = field(default_factory=dict, compare=False, repr=False)


def find_file(bases: Iterable[Path], remote: str = "flathub", arch: str = "x86_64") -> Path | None:
    for base in bases:
        for name in ("appstream.xml.gz", "appstream.xml"):
            p = Path(base) / "appstream" / remote / arch / "active" / name
            if p.exists():
                return p
    return None


def icon_dirs(appstream_path: Path) -> list[Path]:
    icons = appstream_path.parent / "icons"
    return [icons / "128x128", icons / "64x64"]


def _pick(elems: list[ET.Element], lang: str) -> ET.Element | None:
    """The element in the UI language ("ru", "ru_RU", "ru-RU"), else the untranslated one."""
    default = None
    for e in elems:
        el = e.get(XML_LANG)
        if el is None:
            default = e if default is None else default
        elif lang != "en" and re.split(r"[_@-]", el)[0] == lang:
            return e
    return default


def _text(e: ET.Element | None) -> str:
    return " ".join((e.text or "").split()) if e is not None else ""


def _rich(desc: ET.Element | None) -> str:
    """AppStream description markup -> the small HTML subset Qt's rich text shows."""
    if desc is None:
        return ""
    out = []
    for child in desc:
        tag = child.tag
        if tag == "p":
            out.append(f"<p>{html.escape(' '.join(''.join(child.itertext()).split()))}</p>")
        elif tag in ("ul", "ol"):
            items = "".join(f"<li>{html.escape(' '.join(''.join(li.itertext()).split()))}</li>"
                            for li in child if li.tag == "li")
            out.append(f"<{tag}>{items}</{tag}>")
    return "".join(out)


def _screenshots(comp: ET.Element, lang: str) -> tuple[Screenshot, ...]:
    shots = []
    root = comp.find("screenshots")
    if root is None:
        return ()
    for s in root.findall("screenshot"):
        images = s.findall("image")
        thumbs = [(int(i.get("width") or 0), i) for i in images if i.get("type") == "thumbnail"]
        # ~1250 px wide thumbnails look sharp in the app page without the full source size.
        mid = [t for t in thumbs if 900 <= t[0] <= 1700]
        if mid:
            url = _text(min(mid, key=lambda t: t[0])[1])
        else:
            src = [i for i in images if i.get("type") in (None, "source")]
            url = _text(src[0]) if src else (_text(max(thumbs, key=lambda t: t[0])[1]) if thumbs else "")
        if url:
            shots.append(Screenshot(url=url, caption=_text(_pick(s.findall("caption"), lang))))
    return tuple(shots)


def _component(comp: ET.Element, lang: str) -> AppInfo | None:
    if comp.get("type") not in ("desktop-application", "desktop"):
        return None
    bundle = comp.find("bundle")
    ref = _text(bundle) if bundle is not None and bundle.get("type") == "flatpak" else ""
    if not ref.startswith("app/"):
        return None
    app_id = ref.split("/")[1]

    dev = comp.find("developer")
    developer = _text(_pick(dev.findall("name"), lang)) if dev is not None else ""
    developer = developer or _text(_pick(comp.findall("developer_name"), lang))

    icon = remote = ""
    best = -1
    for i in comp.findall("icon"):
        size = int(i.get("width") or 0)
        if i.get("type") == "cached" and not i.get("scale") and size > best:
            icon, best = _text(i), size
        elif i.get("type") == "remote" and not i.get("scale") and not remote:
            remote = _text(i)

    custom = {v.get("key"): _text(v) for v in comp.iterfind("custom/value")}
    release = comp.find("releases/release")
    keywords: list[str] = []
    for kw in comp.findall("keywords"):
        kl = kw.get(XML_LANG)
        if kl is None or kl.split("-")[0].split("_")[0] == lang:
            keywords += [_text(k).lower() for k in kw.findall("keyword")]
    homepage = next((_text(u) for u in comp.findall("url") if u.get("type") == "homepage"), "")
    launch = comp.find("launchable")

    return AppInfo(
        id=app_id,
        name=_text(_pick(comp.findall("name"), lang)) or app_id,
        summary=_text(_pick(comp.findall("summary"), lang)),
        description=_rich(_pick(comp.findall("description"), lang)),
        developer=developer,
        license=_text(comp.find("project_license")),
        verified=custom.get("flathub::verification::verified") == "true",
        version=release.get("version", "") if release is not None else "",
        homepage=homepage,
        icon=icon,
        remote_icon=remote,
        categories=tuple(_text(c) for c in comp.iterfind("categories/category")),
        keywords=tuple(dict.fromkeys(k for k in keywords if k)),
        screenshots=_screenshots(comp, lang),
        desktop_id=_text(launch) if launch is not None and launch.get("type") == "desktop-id" else "",
        runtime=bundle.get("runtime", "") if bundle is not None else "",
    )


def load(path: Path | None, lang: str = "en") -> dict[str, AppInfo]:
    """Parse an AppStream collection (gzipped or not); {} if it isn't there."""
    if path is None or not Path(path).exists():
        return {}
    opener = gzip.open if str(path).endswith(".gz") else open
    apps: dict[str, AppInfo] = {}
    try:
        with opener(path, "rb") as f:
            depth = 0
            for event, elem in ET.iterparse(f, events=("start", "end")):
                if event == "start":
                    depth += 1
                    continue
                depth -= 1
                if depth == 1 and elem.tag == "component":
                    app = _component(elem, lang)
                    if app is not None:
                        apps[app.id] = app
                    elem.clear()
    except (OSError, ET.ParseError, EOFError):
        return apps
    return apps


# --- search ------------------------------------------------------------------

def fold(s: str) -> str:
    """Lower-case and strip accents, so "Café" matches "cafe"."""
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))   # also folds Cyrillic yo


_WORD = re.compile(r"[\w+#.]+")


def _score_token(t: str, app: AppInfo) -> int:
    f = app._fold
    if not f:
        f["name"] = fold(app.name)
        f["words"] = _WORD.findall(f["name"])
        f["id"] = fold(app.id.rsplit(".", 1)[-1])
        f["kw"] = [fold(k) for k in app.keywords]
        f["summary"] = fold(app.summary)
        f["swords"] = _WORD.findall(f["summary"])
        f["dev"] = fold(app.developer)
    name = f["name"]
    score = 0
    if name == t:
        score = 100
    elif t in f["words"]:
        score = 70
    elif name.startswith(t):
        score = 60
    elif any(w.startswith(t) for w in f["words"]):
        score = 40
    elif t in name:
        score = 25
    if f["id"] == t:
        score = max(score, 50)
    elif t in f["id"]:
        score = max(score, 20)
    if t in f["kw"]:
        score += 15
    elif any(k.startswith(t) for k in f["kw"]):
        score += 10
    if any(w.startswith(t) for w in f["swords"]):
        score += 8
    elif t in f["summary"]:
        score += 4
    if t in f["dev"]:
        score += 3
    return score


def search(apps: dict[str, AppInfo], query: str, catalog: "Catalog | None" = None,
           limit: int = 100) -> list[AppInfo]:
    """Rank apps for a query. Every word must match somewhere; the name counts
    most, then keywords, then the summary. Verified publishers and apps in the
    curated catalog win ties, a Windows program name ("photoshop") puts its
    curated replacement first, and a category name ("office") its curated apps. No popularity data is used: there is none."""
    q = fold(query).strip()
    tokens = _WORD.findall(q)
    if len(q) < 2 or not tokens:
        return []
    boost: dict[str, int] = {}
    if catalog is not None:
        for c in catalog.categories:       # "office", "games": the curated page first
            words = _WORD.findall(fold(c.name))
            if len(q) >= 3 and any(w.startswith(q) for w in words):
                for a in c.apps:
                    boost[a] = 60
        for r in catalog.replacements_matching(query):
            for a in r.apps:
                boost[a] = 200
    curated: dict[str, list[str]] = {}
    if catalog is not None:   # our own one-liners count too ("pdf" finds Okular)
        curated = {a: _WORD.findall(fold(c.summary)) for a, c in catalog.apps.items()}
    scored = []
    for app in apps.values():
        total = 0
        for t in tokens:
            s = _score_token(t, app)
            if any(w.startswith(t) for w in curated.get(app.id, ())):
                s += 12
            if s == 0 and app.id not in boost:
                break
            total += s
        else:
            total += boost.get(app.id, 0)
            if total == 0:
                continue
            total += 5 if app.verified else 0
            if catalog is not None and app.id in catalog.apps:
                total += 10
            scored.append((-total, app.name.lower(), app))
    scored.sort(key=lambda x: (x[0], x[1]))
    return [a for _s, _n, a in scored[:limit]]


def license_kind(spdx: str) -> str:
    """"free" (open source), "proprietary" or "unknown", from AppStream's SPDX expression."""
    s = spdx.strip()
    if not s:
        return "unknown"
    if "LicenseRef-proprietary" in s or s.lower() in ("proprietary", "custom"):
        return "proprietary"
    if s.startswith("LicenseRef-") and " " not in s:
        return "unknown"
    return "free"
