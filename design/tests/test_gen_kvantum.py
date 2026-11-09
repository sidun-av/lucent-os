import re
from pathlib import Path

import pytest

import gen_kvantum
import tokens
from lucent_theme import accents

ROOT = Path(__file__).resolve().parents[2]
KV = ROOT / "system_files/usr/share/Kvantum"


def kv_values(text):
    out, sec = {}, None
    for line in text.splitlines():
        if line.startswith("["):
            sec = line.strip()[1:-1]
        elif "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            out[(sec, k)] = v
    return out


def test_one_theme_per_accent_and_mode():
    names = {(folder, t["name"]) for folder, t in gen_kvantum.themes()}
    assert ("Lucent", "Lucent") in names and ("Lucent", "LucentDark") in names
    assert ("LucentAzure", "LucentAzureDark") in names
    assert len(names) == 2 * len(accents.ACCENTS)


@pytest.mark.parametrize("accent,dark,highlight,on_accent", [
    ("indigo", False, "#4257e8", "#ffffff"),
    ("indigo", True, "#7088ff", "#0e1230"),
    ("rose", True, "#cf4f86", "#ffffff"),
])
def test_palette_follows_the_accent(accent, dark, highlight, on_accent):
    t = gen_kvantum.theme_dict(tokens.load().mode(dark), accent, dark)
    v = kv_values(gen_kvantum.kvconfig(t))
    assert v[("GeneralColors", "highlight.color")] == highlight
    assert v[("GeneralColors", "highlight.text.color")] == on_accent
    assert v[("GeneralColors", "window.color")] == tokens.load().mode(dark)["surface-window-solid"]
    assert v[("Hacks", "transparent_dolphin_view")] == "true"


def test_every_element_the_config_names_is_drawn():
    t = gen_kvantum.theme_dict(tokens.load().light, "indigo", False)
    svg = gen_kvantum.build(t)
    v = kv_values(gen_kvantum.kvconfig(t))
    # Kvantum falls back to the -normal state, so that one must exist
    # (as an interior, a frame, or a menu/tooltip shadow frame).
    for (sec, key), base in v.items():
        if key in ("frame.element", "interior.element") and base != "focus":
            assert {f"{base}-normal", f"{base}-normal-top", f"{base}-shadow-top"} & svg.ids, (sec, key, base)
    assert "focus-top" in svg.ids


def test_pieces_stay_inside_their_cells():
    """QtSvg sizes an element by its content, so no piece may draw outside its cell."""
    svg = gen_kvantum.Svg()
    t = gen_kvantum.theme_dict(tokens.load().light, "indigo", False)
    gen_kvantum.layered(svg, "x", 10, gen_kvantum.pillow(t, t["raised"], t["raised2"]), (0, 0, 0, 1))
    for item in svg.items:
        w, h = map(float, re.search(r'<rect width="([\d.]+)" height="([\d.]+)"', item).groups())
        for d in re.findall(r' d="([^"]+)"', item):
            for x, y in re.findall(r"(-?[\d.]+),(-?[\d.]+)", d):
                assert -0.001 <= float(x) <= w + 0.001 and -0.001 <= float(y) <= h + 0.001, (item[:60], x, y)


def test_svg_renders_with_qtsvg():
    QtSvg = pytest.importorskip("PySide6.QtSvg")
    from PySide6.QtCore import QByteArray
    t = gen_kvantum.theme_dict(tokens.load().dark, "pine", True)
    r = QtSvg.QSvgRenderer(QByteArray(gen_kvantum.build(t).text().encode()))
    assert r.isValid()
    b = r.boundsOnElement("expand-button-normal-bottomleft")
    assert (round(b.width()), round(b.height())) == (11, 11)


def test_committed_themes_match_the_generator():
    for folder, t in gen_kvantum.themes():
        base = KV / folder / t["name"]
        assert base.with_suffix(".kvconfig").read_text() == gen_kvantum.kvconfig(t), f"run design/gen_kvantum.py ({t['name']})"
        assert base.with_suffix(".svg").read_text() == gen_kvantum.build(t).text(), f"run design/gen_kvantum.py ({t['name']})"


@pytest.mark.parametrize("dark", [False, True])
def test_nothing_is_sunken(dark):
    """Glass Card: fields and segmented strips are light glass that sits on
    the surface (drop below, top highlight), tracks are a flat tint, and a
    selection is a soft accent pill with no outline."""
    t = gen_kvantum.theme_dict(tokens.load().mode(dark), "indigo", dark)
    assert not hasattr(gen_kvantum, "well")
    layers = gen_kvantum.glass(t, t["field"])
    assert layers[0] == ("shape", t["card_drop"], 0, 1)
    assert layers[-1] == ("topline", t["glass_hl"], 1, 1)
    text = gen_kvantum.build(t).text()
    for eid in ("progress-normal", "slider-normal"):
        assert gen_kvantum.paint(t["track"]) in text.split(f'id="{eid}')[1][:400], eid
    sel = text.split('id="itemview-pressed')[1][:600]
    assert gen_kvantum.paint(t["accent_ring"], "stroke") not in sel
