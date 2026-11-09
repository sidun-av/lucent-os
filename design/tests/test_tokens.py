"""The theme generators read Pebble Drift's tokens straight from
docs/mockups/concepts-2026/pebble-drift/pebble-drift.css (part 1)."""
import re
from pathlib import Path

import pytest

import tokens
from lucent_theme import accents

ROOT = Path(__file__).resolve().parents[2]
CSS = ROOT / "docs/mockups/concepts-2026/pebble-drift/pebble-drift.css"


def test_parses_light_and_dark_blocks():
    t = tokens.load(CSS)
    assert t.light["accent"] == "#4257e8"
    assert t.dark["accent"] == "#7088ff"
    assert t.light["surface-window"] == "rgba(244, 245, 251, .93)"
    assert t.dark["surface-window-solid"] == "#1d1f2e"


def test_dark_inherits_what_it_does_not_override():
    t = tokens.load(CSS)
    assert t.dark["radius-window"] == t.light["radius-window"] == "18px"
    assert t.dark["space-4"] == "16px"


def test_var_references_resolve_per_mode():
    t = tokens.load(CSS)
    # --gauge-1: var(--accent) is declared once, in :root
    assert t.light["gauge-1"] == "#4257e8"
    assert t.dark["gauge-1"] == "#7088ff"
    assert t.dark["gauge-track"] == t.dark["surface-sunken-strong"]


def test_comments_and_several_declarations_per_line():
    css = """:root {
      /* --fake: #000000; */
      --a: 1px;  --b: 2px; /* trailing */
      --c: var(--b);
    }
    .dark { --a: 3px; }
    .other { --a: 9px; }"""
    t = tokens.parse(css)
    assert t.light == {"a": "1px", "b": "2px", "c": "2px"}
    assert t.dark == {"a": "3px", "b": "2px", "c": "2px"}


def test_unknown_var_is_an_error():
    with pytest.raises(KeyError):
        tokens.parse(":root { --a: var(--missing); }")


def test_color_parsing():
    assert tokens.color("#4257e8") == pytest.approx((66 / 255, 87 / 255, 232 / 255, 1.0))
    assert tokens.color("rgba(48, 58, 120, .065)") == pytest.approx((48 / 255, 58 / 255, 120 / 255, 0.065))
    with pytest.raises(ValueError):
        tokens.color("linear-gradient(#fff, #000)")


def test_px():
    assert tokens.px("18px") == 18
    assert tokens.px("15.5px") == 15.5


def test_flatten_composites_a_translucent_colour_on_a_solid_one():
    # indigo-grey 6.5 % well on the solid window colour
    # 48*.065 + 242*.935 = 229.4 -> e5; 58/243 -> e7; 120/250 -> f2
    assert tokens.flatten("rgba(48, 58, 120, .065)", "#f2f3fa") == "#e5e7f2"
    assert tokens.flatten("#123456", "#ffffff") == "#123456"


def test_shadow_list_parsing():
    s = tokens.shadows("0 0 0 1px rgba(30, 40, 100, .10), 0 16px 34px -6px rgba(25, 35, 90, .15)")
    assert s == [(0, 0, 0, 1, "rgba(30, 40, 100, .10)"), (0, 16, 34, -6, "rgba(25, 35, 90, .15)")]
    assert tokens.shadows("inset 0 1px 0 rgba(255, 255, 255, .9)") == [(0, 1, 0, 0, "rgba(255, 255, 255, .9)", "inset")]


def test_accents_match_the_settings_mockup_swatches():
    html = (ROOT / "docs/mockups/concepts-2026/pebble-drift/04-settings.html").read_text()
    swatches = re.findall(r'<span class="sw[^"]*" style="background:(#[0-9a-f]{6})"', html)
    names = re.findall(r"<(?:b|span)>(\w+)</(?:b|span)>", html.split('class="swn"')[1].split("</div>")[0])
    assert [a.hex for a in accents.ACCENTS] == swatches
    assert [a.name for a in accents.ACCENTS] == names
    assert accents.ACCENTS[0].id == "indigo"


def test_indigo_uses_the_design_tokens_in_both_modes():
    t = tokens.load(CSS)
    for mode, tok in (("light", t.light), ("dark", t.dark)):
        a = accents.palette("indigo", mode == "dark")
        assert a["accent"] == tok["accent"]
        assert a["accent-hover"] == tok["accent-hover"]
        assert a["accent-pressed"] == tok["accent-pressed"]
        assert a["accent-text"] == tok["accent-text"]
        assert a["text-on-accent"] == tok["text-on-accent"]


def test_other_accents_follow_the_settings_app_formulas():
    # Settings (qml/Lucent/Theme.qml): the swatch itself in both modes,
    # Qt.lighter/darker for the variants, white text on it.
    az = accents.palette("azure", dark=False)
    assert az["accent"] == "#2f7ae0"
    assert az["text-on-accent"] == "#ffffff"
    assert az["accent-pressed"] == accents.qt_darker("#2f7ae0", 1.12)
    assert accents.palette("azure", dark=True)["accent-text"] == accents.qt_lighter("#2f7ae0", 1.35)


# (colour, lighter(108), darker(112), lighter(135), darker(115)) from PySide6 6.11 QColor
QCOLOR = [
    ('#4257e8', '#475efb', '#3b4ecf', '#8392ff', '#394cca'),
    ('#2f7ae0', '#3384f2', '#2a6dc8', '#65a6ff', '#296ac3'),
    ('#1f96a8', '#21a2b5', '#1c8696', '#2acbe3', '#1b8292'),
    ('#7a55e0', '#845cf2', '#6d4cc8', '#ae90ff', '#6a4ac3'),
    ('#a54fc4', '#b255d4', '#9347af', '#d970ff', '#8f45aa'),
    ('#cf4f86', '#e05591', '#b94778', '#ff7ab3', '#b44575'),
    ('#3f8f68', '#449a70', '#38805d', '#55c18c', '#377c5a'),
    ('#5f6684', '#676e8f', '#555b76', '#808ab2', '#535973'),
    ('#f0f0ff', '#ffffff', '#d6d6e4', '#ffffff', '#d1d1de'),
    ('#000000', '#000000', '#000000', '#000000', '#000000'),
]


@pytest.mark.parametrize("c,l108,d112,l135,d115", QCOLOR)
def test_qt_lighter_and_darker_match_qcolor(c, l108, d112, l135, d115):
    assert accents.qt_lighter(c, 1.08) == l108
    assert accents.qt_darker(c, 1.12) == d112
    assert accents.qt_lighter(c, 1.35) == l135
    assert accents.qt_darker(c, 1.15) == d115


def test_accent_lookup_by_name_or_hex():
    assert accents.find("Rose").id == "rose"
    assert accents.find("#CF4F86").id == "rose"
    assert accents.find("nope") is None
    # any other colour (Plasma's "accent from wallpaper") maps to the closest swatch
    assert accents.nearest("#3060f0").id in {"indigo", "azure"}
    assert accents.nearest("#40a070").id == "pine"
