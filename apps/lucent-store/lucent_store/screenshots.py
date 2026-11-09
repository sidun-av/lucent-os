"""Screenshots from AppStream, downloaded once and kept in ~/.cache.

Only an app's own page asks for them, so opening the store, browsing
categories or searching never downloads anything. Downloads are plain
HTTPS GETs of the URLs in Flathub's AppStream data (no cookies, no ids).
"""

from __future__ import annotations

import hashlib
import os
import threading
import urllib.request
from pathlib import Path
from typing import Callable

MAX_BYTES = 8 * 1024 * 1024
USER_AGENT = "Lucent-Store"     # no version, no machine details


def cache_dir() -> Path:
    base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(base) / "lucent-store" / "screenshots"


def _fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read(MAX_BYTES + 1)


class ScreenshotCache:
    def __init__(self, directory: Path | None = None, fetch: Callable[[str], bytes] = _fetch,
                 on_ready: Callable[[str], None] | None = None, threaded: bool = True):
        self.dir = directory or cache_dir()
        self.fetch = fetch
        self.on_ready = on_ready or (lambda url: None)
        self.threaded = threaded
        self._pending: set[str] = set()
        self._failed: set[str] = set()
        self._lock = threading.Lock()

    def path_for(self, url: str) -> Path:
        ext = os.path.splitext(url.split("?")[0])[1].lower()
        ext = ext if ext in (".png", ".jpg", ".jpeg", ".webp") else ".png"
        return self.dir / (hashlib.sha256(url.encode()).hexdigest()[:32] + ext)

    def get(self, url: str) -> Path | None:
        """The cached file, or None while it is being downloaded (on_ready(url) follows)."""
        if not url.startswith("https://"):
            return None
        path = self.path_for(url)
        if path.exists():
            return path
        with self._lock:
            if url in self._pending or url in self._failed:
                return None
            self._pending.add(url)
        if self.threaded:
            threading.Thread(target=self._download, args=(url, path), daemon=True).start()
        else:
            self._download(url, path)
        return path if path.exists() else None

    def _download(self, url: str, path: Path) -> None:
        try:
            data = self.fetch(url)
            if len(data) > MAX_BYTES:
                raise ValueError("too large")
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(path.suffix + ".part")
            tmp.write_bytes(data)
            tmp.replace(path)
        except Exception:  # noqa: BLE001 - offline, 404, ...: just no screenshot
            with self._lock:
                self._failed.add(url)
        finally:
            with self._lock:
                self._pending.discard(url)
        if path.exists():
            self.on_ready(url)
