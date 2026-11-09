"""Shared fixtures: English UI, a small AppStream file, sample flatpak output."""

from __future__ import annotations

import gzip
from pathlib import Path

import pytest

from lucent_store import i18n

DATA = Path(__file__).parent / "data"


@pytest.fixture(autouse=True)
def english_ui():
    """Tests see the source (English) strings unless they load a catalog."""
    i18n.setup(["en"])
    yield
    i18n.setup(["en"])


@pytest.fixture
def appstream_file(tmp_path) -> Path:
    """The test AppStream collection, gzipped like flatpak stores it."""
    out = tmp_path / "appstream.xml.gz"
    out.write_bytes(gzip.compress((DATA / "appstream.xml").read_bytes()))
    return out
