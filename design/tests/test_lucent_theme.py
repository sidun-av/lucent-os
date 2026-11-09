"""lucent-theme: one command that switches light/dark/auto and the accent
consistently (colour scheme, Kvantum, Flatpak apps, wallpaper variant)."""
import json
from pathlib import Path

import pytest

from lucent_theme import cli, theme


class FakeRunner:
    """Records commands; answers like the real tools do."""

    def __init__(self, cfg: Path):
        self.cfg = cfg
        self.calls: list[list[str]] = []
        self.fail: set[str] = set()

    def run(self, argv, timeout=60):
        self.calls.append(list(argv))
        tool = Path(argv[0]).name
        if tool in self.fail:
            return theme.Result(1, "", f"{tool} failed")
        if tool == "plasma-apply-lookandfeel":
            dark = argv[-1].endswith(".dark")
            kg = self.cfg / "kdeglobals"
            groups = theme.parse_kconfig(kg.read_text()) if kg.exists() else {}
            groups.setdefault(("KDE",), {})["LookAndFeelPackage"] = argv[-1]
            groups[("KDE",)]["widgetStyle"] = "lucent-dark" if dark else "lucent"
            groups.setdefault(("General",), {})["ColorScheme"] = "LucentDark" if dark else "LucentLight"
            # a global theme puts the scheme's own colours back (drops the accent)
            groups.setdefault(("Colors:Window",), {})["DecorationFocus"] = "112,136,255" if dark else "66,87,232"
            kg.write_text(theme.dump_kconfig(groups))
        if tool == "plasma-apply-colorscheme" and "--accent-color" in argv:
            kg = self.cfg / "kdeglobals"
            groups = theme.parse_kconfig(kg.read_text()) if kg.exists() else {}
            c = argv[argv.index("--accent-color") + 1].lstrip("#")
            # Plasma 6: the accent goes into DecorationFocus (exactly) of every set
            groups.setdefault(("Colors:Window",), {})["DecorationFocus"] = ",".join(str(int(c[i:i + 2], 16)) for i in (0, 2, 4))
            kg.write_text(theme.dump_kconfig(groups))
        if tool == "kwriteconfig6":
            f = self.cfg / argv[argv.index("--file") + 1]
            groups = theme.parse_kconfig(f.read_text()) if f.exists() else {}
            g = tuple(argv[i + 1] for i, a in enumerate(argv) if a == "--group")
            key = argv[argv.index("--key") + 1]
            if "--delete" in argv:
                groups.get(g, {}).pop(key, None)
            else:
                groups.setdefault(g, {})[key] = argv[-1]
            f.write_text(theme.dump_kconfig(groups))
        return theme.Result(0, "", "")

    def tools(self):
        return [Path(c[0]).name for c in self.calls]


@pytest.fixture
def env(tmp_path, monkeypatch):
    cfg = tmp_path / "config"
    cfg.mkdir()
    monkeypatch.setenv("XDG_CONFIG_HOME", str(cfg))
    monkeypatch.setenv("HOME", str(tmp_path))
    (cfg / "kdeglobals").write_text("[KDE]\nLookAndFeelPackage=org.lucent.desktop\nwidgetStyle=lucent\n"
                                    "[General]\nColorScheme=LucentLight\n[Colors:Window]\nDecorationFocus=66,87,232\n")
    return cfg, FakeRunner(cfg)


def kv_theme(cfg):
    return theme.parse_kconfig((cfg / "Kvantum/kvantum.kvconfig").read_text())[("General",)]["theme"]


def test_dark_with_an_accent(env):
    cfg, r = env
    assert theme.apply(r, mode="dark", accent="azure") == 0
    kg = theme.parse_kconfig((cfg / "kdeglobals").read_text())
    assert kg[("KDE",)]["LookAndFeelPackage"] == "org.lucent.desktop.dark"
    assert kg[("Colors:Window",)]["DecorationFocus"] == "47,122,224"   # #2f7ae0
    assert kv_theme(cfg) == "LucentAzure"                            # lucent-dark picks LucentAzureDark
    # order matters: the global theme first (it resets the colours), then the accent
    tools = r.tools()
    assert tools.index("plasma-apply-lookandfeel") < tools.index("plasma-apply-colorscheme")
    assert "kvantum-flatpak-sync" in tools
    st = theme.read_state()
    assert (st.mode, st.accent) == ("dark", "azure")


def test_indigo_removes_the_accent_override(env):
    cfg, r = env
    theme.apply(r, mode="light", accent="rose")
    r.calls.clear()
    theme.apply(r, accent="indigo")
    kg = theme.parse_kconfig((cfg / "kdeglobals").read_text())
    assert kg[("Colors:Window",)]["DecorationFocus"] == "66,87,232"    # the scheme's own indigo
    assert kv_theme(cfg) == "Lucent"
    # the scheme's own colours come back by re-applying the global theme
    assert ["plasma-apply-lookandfeel", "-a", "org.lucent.desktop"] in r.calls


def test_accent_only_keeps_the_mode_and_does_not_reapply_the_global_theme(env):
    cfg, r = env
    theme.apply(r, mode="dark")
    r.calls.clear()
    theme.apply(r, accent="pine")
    assert "plasma-apply-lookandfeel" not in r.tools()
    assert theme.read_state().mode == "dark"
    assert kv_theme(cfg) == "LucentPine"


def test_auto_turns_on_plasmas_automatic_mode(env):
    cfg, r = env
    theme.apply(r, mode="auto")
    kg = theme.parse_kconfig((cfg / "kdeglobals").read_text())
    assert kg[("KDE",)]["AutomaticLookAndFeel"] == "true"
    assert kg[("KDE",)]["DefaultLightLookAndFeel"] == "org.lucent.desktop"
    assert kg[("KDE",)]["DefaultDarkLookAndFeel"] == "org.lucent.desktop.dark"
    theme.apply(r, mode="light")
    kg = theme.parse_kconfig((cfg / "kdeglobals").read_text())
    assert kg[("KDE",)]["AutomaticLookAndFeel"] == "false"


def test_any_colour_snaps_to_the_nearest_swatch(env):
    cfg, r = env
    theme.apply(r, accent="#40a070")
    assert theme.read_state().accent == "pine"
    assert ["plasma-apply-colorscheme", "--accent-color", "#3f8f68"] in r.calls


def test_sync_puts_the_accent_back_after_a_global_theme_switch(env):
    cfg, r = env
    theme.apply(r, mode="light", accent="violet")
    # Plasma's automatic mode switches to dark at sunset: the accent is dropped
    r.run(["plasma-apply-lookandfeel", "-a", "org.lucent.desktop.dark"])
    r.calls.clear()
    theme.sync(r)
    kg = theme.parse_kconfig((cfg / "kdeglobals").read_text())
    assert kg[("Colors:Window",)]["DecorationFocus"] == "122,85,224"
    # and once everything matches, sync changes nothing (no path-unit loop)
    r.calls.clear()
    theme.sync(r)
    assert "plasma-apply-colorscheme" not in r.tools()


def test_sync_follows_the_wallpaper_accent(env):
    cfg, r = env
    (cfg / "kdeglobals").write_text("[KDE]\nLookAndFeelPackage=org.lucent.desktop\nwidgetStyle=lucent\n"
                                    "[General]\nColorScheme=LucentLight\naccentColorFromWallpaper=true\n"
                                    "[Colors:Window]\nDecorationFocus=200,80,135\n")
    theme.sync(r)
    assert kv_theme(cfg) == "LucentRose"
    assert "plasma-apply-colorscheme" not in r.tools()


def test_sync_without_a_lucent_choice_follows_kde(env):
    """Nothing chosen through Lucent yet, accent set in System Settings: sync
    doesn't undo it, Kvantum follows it."""
    cfg, r = env
    (cfg / "kdeglobals").write_text("[KDE]\nLookAndFeelPackage=org.lucent.desktop\nwidgetStyle=lucent\n"
                                    "[General]\nColorScheme=LucentLight\n[Colors:Window]\nDecorationFocus=63,143,104\n")
    theme.sync(r)
    assert "plasma-apply-lookandfeel" not in r.tools()
    assert kv_theme(cfg) == "LucentPine"


def test_settings_choice_is_adopted_and_kept_in_step(env):
    cfg, r = env
    (cfg / "lucent-settingsrc").write_text("[Appearance]\nAccent=#a54fc4\n")
    assert theme.read_state().accent == "orchid"
    theme.apply(r, accent="lagoon")
    own = theme.parse_kconfig((cfg / "lucent-settingsrc").read_text())
    assert own[("Appearance",)]["Accent"] == "#1f96a8"
    theme.apply(r, accent="indigo")
    own = theme.parse_kconfig((cfg / "lucent-settingsrc").read_text())
    assert own[("Appearance",)].get("Accent", "") == ""


def test_users_own_kvantum_choice_is_replaced_only_on_request(env):
    cfg, r = env
    (cfg / "Kvantum").mkdir()
    (cfg / "Kvantum/kvantum.kvconfig").write_text("[General]\ntheme=KvArc\n")
    theme.sync(r)
    assert kv_theme(cfg) == "KvArc"                 # sync leaves a foreign theme alone
    theme.apply(r, accent="slate")
    assert kv_theme(cfg) == "LucentSlate"           # an explicit choice wins


def test_status_json(env, capsys):
    cfg, r = env
    theme.apply(r, mode="dark", accent="rose")
    assert cli.main(["status", "--json"], runner=r) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["mode"] == "dark" and out["accent"] == "rose" and out["accent_hex"] == "#cf4f86"
    assert out["kvantum_theme"] == "LucentRose" and out["effective_mode"] == "dark"


def test_cli_validates_arguments(env, capsys):
    cfg, r = env
    assert cli.main(["apply", "--accent", "chartreuse"], runner=r) == 2
    assert "unknown accent" in capsys.readouterr().err
    assert cli.main(["apply"], runner=r) == 2
    assert cli.main(["apply", "--mode", "light", "--accent", "Indigo"], runner=r) == 0


def test_failure_is_reported(env, capsys):
    cfg, r = env
    r.fail.add("plasma-apply-lookandfeel")
    assert cli.main(["apply", "--mode", "dark"], runner=r) == 1
    assert "plasma-apply-lookandfeel failed" in capsys.readouterr().err


def test_accents_list(env, capsys):
    cfg, r = env
    assert cli.main(["accents", "--json"], runner=r) == 0
    names = [a["id"] for a in json.loads(capsys.readouterr().out)]
    assert names == ["indigo", "azure", "lagoon", "violet", "orchid", "rose", "pine", "slate"]


def test_indigo_in_dark_mode_is_the_schemes_own_accent(env):
    """The dark scheme's own accent is the light indigo #7088ff: nothing to undo."""
    cfg, r = env
    theme.apply(r, mode="dark")
    r.calls.clear()
    theme.sync(r)
    assert "plasma-apply-lookandfeel" not in r.tools() and "plasma-apply-colorscheme" not in r.tools()
