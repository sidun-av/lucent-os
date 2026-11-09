"""The curated, versioned catalog shipped with the store (catalog.toml).

Everything the store shows without being asked comes from here: the
"Instead of Windows programs" cards, the category pages and the ArtCraft
beta apps. Loading validates cross-references so a typo fails the tests,
not the user's store.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

PATH = Path(__file__).with_name("catalog.toml")
SCHEMA = 1


class CatalogError(ValueError):
    pass


@dataclass(frozen=True)
class CatalogApp:
    id: str
    name: str
    summary: str
    system: str | None = None   # desktop id of an app that is part of Lucent itself


@dataclass(frozen=True)
class Replacement:
    windows: str                # the Windows program, shown as is (a product name)
    apps: tuple[str, ...]
    name: str
    description: str
    icon: str | None = None     # a store tile (icons/app-<icon>.svg) instead of the app icon
    note: str | None = None


@dataclass(frozen=True)
class Category:
    id: str
    name: str
    icon: str
    description: str
    apps: tuple[str, ...]


@dataclass(frozen=True)
class NextGenApp:
    key: str
    id: str
    name: str
    description: str
    repo: str
    version: str
    sha256: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Catalog:
    schema: int
    version: str
    apps: dict[str, CatalogApp]
    replacements: list[Replacement]
    categories: list[Category]
    nextgen: list[NextGenApp]

    def category(self, cid: str) -> Category | None:
        return next((c for c in self.categories if c.id == cid), None)

    def replacements_matching(self, query: str) -> list[Replacement]:
        """Cards whose Windows program matches the query ("photoshop" -> GIMP)."""
        q = query.strip().lower()
        if len(q) < 2:
            return []
        out = []
        for r in self.replacements:
            words = r.windows.lower().replace("adobe ", "").replace("microsoft ", "")
            if q in r.windows.lower() or any(w.startswith(q) for w in words.split()):
                out.append(r)
        return out

    def nextgen_app(self, key: str) -> NextGenApp | None:
        return next((n for n in self.nextgen if n.key == key or n.id == key), None)

    def translatable_strings(self) -> list[str]:
        """User-visible English text in the catalog (product names excluded)."""
        out: list[str] = []
        for r in self.replacements:
            out += [r.description] + ([r.note] if r.note else [])
            if r.name not in {self.apps[a].name for a in r.apps}:
                out.append(r.name)
        for c in self.categories:
            out += [c.name, c.description]
        for a in self.apps.values():
            out.append(a.summary)
            if a.system:
                out.append(a.name)
        for n in self.nextgen:
            out.append(n.description)
        return [s for s in out if s and not _is_product_name(s)]


def _is_product_name(s: str) -> bool:
    """Combined product names ("Okular + PDF Arranger") need no translation."""
    return " + " in s


def _req(d: dict, key: str, where: str):
    if key not in d:
        raise CatalogError(f"{where}: missing '{key}'")
    return d[key]


def load(path: Path = PATH) -> Catalog:
    try:
        raw = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as e:
        raise CatalogError(f"{path}: {e}") from e
    if raw.get("schema") != SCHEMA:
        raise CatalogError(f"{path}: unsupported schema {raw.get('schema')!r} (expected {SCHEMA})")

    apps = {
        app_id: CatalogApp(id=app_id, name=_req(a, "name", app_id), summary=_req(a, "summary", app_id),
                           system=a.get("system"))
        for app_id, a in raw.get("apps", {}).items()
    }
    replacements = [
        Replacement(windows=_req(r, "windows", "replacement"), apps=tuple(_req(r, "apps", r["windows"])),
                    name=_req(r, "name", r["windows"]), description=_req(r, "description", r["windows"]),
                    icon=r.get("icon"), note=r.get("note"))
        for r in raw.get("replacement", [])
    ]
    categories = [
        Category(id=_req(c, "id", "category"), name=_req(c, "name", c["id"]), icon=_req(c, "icon", c["id"]),
                 description=_req(c, "description", c["id"]), apps=tuple(c.get("apps", [])))
        for c in raw.get("category", [])
    ]
    nextgen = [
        NextGenApp(key=_req(n, "key", "nextgen"), id=_req(n, "id", n["key"]), name=_req(n, "name", n["key"]),
                   description=_req(n, "description", n["key"]), repo=_req(n, "repo", n["key"]),
                   version=_req(n, "version", n["key"]), sha256=dict(_req(n, "sha256", n["key"])))
        for n in raw.get("nextgen", [])
    ]

    for owner, ids in [(r.windows, r.apps) for r in replacements] + [(c.id, c.apps) for c in categories]:
        for app_id in ids:
            if app_id not in apps:
                raise CatalogError(f"{path}: {owner} refers to {app_id}, which has no [apps] entry")
    return Catalog(schema=SCHEMA, version=str(_req(raw, "version", str(path))), apps=apps,
                   replacements=replacements, categories=categories, nextgen=nextgen)
