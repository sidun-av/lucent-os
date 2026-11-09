from lucent_store.screenshots import ScreenshotCache

URL = "https://dl.flathub.org/media/gimp-1.png"


def test_downloads_once_and_reuses_the_file(tmp_path):
    calls, ready = [], []
    cache = ScreenshotCache(tmp_path, fetch=lambda u: calls.append(u) or b"PNG", on_ready=ready.append,
                            threaded=False)
    path = cache.get(URL)
    assert path is not None and path.read_bytes() == b"PNG" and path.suffix == ".png"
    assert cache.get(URL) == path
    assert calls == [URL] and ready == [URL]


def test_failures_are_not_retried_and_not_fatal(tmp_path):
    calls = []

    def boom(url):
        calls.append(url)
        raise OSError("offline")

    cache = ScreenshotCache(tmp_path, fetch=boom, threaded=False)
    assert cache.get(URL) is None and cache.get(URL) is None
    assert calls == [URL]


def test_only_https(tmp_path):
    cache = ScreenshotCache(tmp_path, fetch=lambda u: b"x", threaded=False)
    assert cache.get("http://example.com/a.png") is None
    assert cache.get("file:///etc/passwd") is None


def test_xdg_cache_home(monkeypatch, tmp_path):
    from lucent_store import screenshots
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    assert screenshots.cache_dir() == tmp_path / "lucent-store" / "screenshots"
