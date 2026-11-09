"""Tests see the source (English) strings unless they load a catalog."""

from __future__ import annotations

import pytest

from lucent_bridge_sheet import i18n


@pytest.fixture(autouse=True)
def english_ui():
    i18n.setup(["en"])
    yield
    i18n.setup(["en"])
