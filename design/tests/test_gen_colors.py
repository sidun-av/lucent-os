from pathlib import Path

import gen_colors
import tokens

ROOT = Path(__file__).resolve().parents[2]


def groups(text):
    out, cur = {}, None
    for line in text.splitlines():
        if line.startswith("["):
            cur = out.setdefault(line.strip()[1:-1], {})
        elif "=" in line and cur is not None:
            k, v = line.split("=", 1)
            cur[k] = v
    return out


def test_light_scheme_uses_the_pebble_drift_surfaces():
    t = tokens.load()
    g = groups(gen_colors.scheme(gen_colors.palette(t.light, False)))
    assert g["Colors:Window"]["BackgroundNormal"] == "242,243,250"      # --surface-window-solid
    assert g["Colors:Window"]["ForegroundNormal"] == "23,26,43"         # --text-primary
    assert g["Colors:Header"]["BackgroundNormal"] == g["Colors:Window"]["BackgroundNormal"]
    assert g["Colors:Selection"]["BackgroundNormal"] == "66,87,232"     # --accent
    assert g["Colors:Selection"]["ForegroundNormal"] == "255,255,255"   # --text-on-accent
    assert g["Colors:View"]["ForegroundLink"] == "51,70,207"            # --accent-text
    assert g["Colors:Window"]["ForegroundNegative"] == "207,58,72"      # --status-danger


def test_dark_scheme_has_dark_text_on_the_light_indigo():
    t = tokens.load()
    g = groups(gen_colors.scheme(gen_colors.palette(t.dark, True)))
    assert g["Colors:Window"]["BackgroundNormal"] == "29,31,46"
    assert g["Colors:Selection"]["BackgroundNormal"] == "112,136,255"
    assert g["Colors:Selection"]["ForegroundNormal"] == "14,18,48"
    assert g["General"]["ColorScheme"] == "LucentDark"


def test_committed_schemes_are_generated_from_the_current_tokens():
    t = tokens.load()
    for p in (gen_colors.palette(t.light, False), gen_colors.palette(t.dark, True)):
        committed = (ROOT / f"system_files/usr/share/color-schemes/{p['id']}.colors").read_text()
        assert committed == gen_colors.scheme(p), f"run design/gen_colors.py ({p['id']} is stale)"
    kg = (ROOT / "system_files/etc/xdg/kdeglobals").read_text()
    assert gen_colors.kdeglobals_block(gen_colors.scheme(gen_colors.palette(t.light, False))) in kg
