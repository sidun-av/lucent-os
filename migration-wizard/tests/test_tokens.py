"""The wizard's look comes from the Pebble Drift tokens (tokens.css), which
must stay identical to the design's source of truth, pebble-drift.css."""

from pathlib import Path

import pytest

from lucent_migrate import tokens

SOURCE = Path(__file__).resolve().parents[2] / "docs/mockups/concepts-2026/pebble-drift/pebble-drift.css"


def test_light_and_dark_tokens_load():
    light, dark = tokens.load(dark=False), tokens.load(dark=True)
    assert light["accent"] == "#4257e8" and dark["accent"] == "#7088ff"
    assert light["text-primary"] == "#171a2b" and dark["text-primary"] == "#eef0fa"
    assert light["surface-window-solid"] == "#f2f3fa" and dark["surface-window-solid"] == "#1d1f2e"
    # dark only overrides colours; everything else is inherited from :root
    assert dark["radius-card"] == light["radius-card"] == "14px"
    assert dark["type-body"] == "15.5px"


def test_var_references_resolve_in_their_mode():
    # --gauge-1: var(--accent) follows the dark accent in dark mode
    assert tokens.load(dark=False)["gauge-1"] == "#4257e8"
    assert tokens.load(dark=True)["gauge-1"] == "#7088ff"
    assert tokens.load(dark=True)["gauge-track"] == "rgba(0, 0, 10, .30)"


def test_values_with_semicolons_in_quotes_parse():
    light, _dark = tokens.parse(':root { --a: url("data:x;utf8,<b>;</b>"); --b: 2px; }')
    assert light == {"a": 'url("data:x;utf8,<b>;</b>")', "b": "2px"}


def test_unknown_var_is_an_error():
    with pytest.raises(KeyError):
        tokens.resolve({"a": "var(--missing)"})


def test_qss_conversions():
    assert tokens.qss("rgba(48, 58, 120, .065)") == "rgba(48, 58, 120, 0.065)"
    assert tokens.qss("#4257e8") == "#4257e8"
    assert tokens.qss("linear-gradient(#ffffff, #eceef8)") == (
        "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #eceef8)")
    assert tokens.px("15.5px") == 15.5


@pytest.mark.skipif(not SOURCE.exists(), reason="design sources are not part of an installed wizard")
def test_shipped_tokens_match_the_design_source():
    """tokens.css is a copy of pebble-drift.css part 1: refresh it with
    `python3 design/sync-wizard-tokens.py` whenever the design changes."""
    shipped = tokens.parse(tokens.TOKENS_CSS.read_text())
    source = tokens.parse(SOURCE.read_text())
    assert shipped == source
    assert tokens.extract(SOURCE.read_text()) in tokens.TOKENS_CSS.read_text()
