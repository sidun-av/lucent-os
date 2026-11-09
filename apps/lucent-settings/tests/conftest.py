"""Shared test helpers: a fake Runner and the captured fixtures.

Fixtures in tests/fixtures/ were captured on the Lucent OS test VM (aarch64,
Fedora 45 base) with the command named in each test; the few that a VM
can't produce (Wi-Fi scan, BlueZ devices, a staged update) are marked
"constructed" in tests/fixtures/README.md and follow the tools' documented
output format.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from lucent_settings import i18n
from lucent_settings.run import Result

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class FakeRunner:
    """Replays canned output for argv prefixes and records every call."""

    def __init__(self, replies: dict[tuple[str, ...], Result | str] | None = None):
        self.replies = dict(replies or {})
        self.calls: list[list[str]] = []
        self.stdin: list[str | None] = []
        self.spawned: list[list[str]] = []

    def on(self, *prefix: str, out: str = "", code: int = 0, err: str = "") -> "FakeRunner":
        self.replies[tuple(prefix)] = Result(code, out, err)
        return self

    def run(self, argv, *, timeout=30, stdin=None):
        self.calls.append(list(argv))
        self.stdin.append(stdin)
        best = None
        for prefix, reply in self.replies.items():
            if tuple(argv[: len(prefix)]) == prefix and (best is None or len(prefix) > len(best[0])):
                best = (prefix, reply)
        if best is None:
            return Result(0, "", "")
        reply = best[1]
        return Result(0, reply, "") if isinstance(reply, str) else reply

    def spawn(self, argv):
        self.spawned.append(list(argv))
        return True

    def called(self, *prefix: str) -> list[list[str]]:
        return [c for c in self.calls if tuple(c[: len(prefix)]) == prefix]


@pytest.fixture
def runner():
    return FakeRunner()


@pytest.fixture(autouse=True)
def english_ui():
    i18n.setup(["en"])
    yield
    i18n.setup(["en"])


@pytest.fixture
def xdg_config(tmp_path, monkeypatch):
    home = tmp_path / "config"
    sysdir = tmp_path / "etc-xdg"
    home.mkdir()
    sysdir.mkdir()
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_DIRS", str(sysdir))
    return home, sysdir
