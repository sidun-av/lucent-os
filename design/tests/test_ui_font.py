"""The UI font follows the session's language: Figtree (Pebble Drift's
typeface) where it covers the language, Inter (which covers Cyrillic, Greek
and Vietnamese too) everywhere else, so no session mixes the two."""
from pathlib import Path

import pytest

from lucent_theme import cli, fonts, theme

# what `fc-list Figtree:lang=X family` answers on the image (Figtree 2.001:
# Western and Central European Latin; no Cyrillic, Greek or Vietnamese)
FIGTREE_LANGS = {"en", "de", "fr", "es", "pl", "cs", "tr"}
ROOT = Path(__file__).resolve().parents[2]


class Runner:
    def __init__(self, cfg: Path):
        self.cfg = cfg
        self.calls: list[list[str]] = []

    def run(self, argv, timeout=60):
        self.calls.append(list(argv))
        if argv[0] == "fc-list":
            family, _, lang = argv[1].partition(":lang=")
            ok = family == "Figtree" and lang in FIGTREE_LANGS
            return theme.Result(0, "Figtree\n" if ok else "", "")
        if argv[0] == "kwriteconfig6":
            f = self.cfg / argv[argv.index("--file") + 1]
            groups = theme.parse_kconfig(f.read_text()) if f.exists() else {}
            g = tuple(argv[i + 1] for i, a in enumerate(argv) if a == "--group")
            groups.setdefault(g, {})[argv[argv.index("--key") + 1]] = argv[-1]
            f.write_text(theme.dump_kconfig(groups))
        return theme.Result(0, "", "")

    def wrote(self):
        return [c for c in self.calls if c[0] == "kwriteconfig6"]


@pytest.fixture
def cfg(tmp_path, monkeypatch):
    c = tmp_path / "config"
    c.mkdir()
    monkeypatch.setenv("XDG_CONFIG_HOME", str(c))
    monkeypatch.setenv("HOME", str(tmp_path))
    return c


def kdeglobals(cfg):
    return theme.parse_kconfig((cfg / "kdeglobals").read_text())


@pytest.mark.parametrize("locale,code", [
    ("ru_RU.UTF-8", "ru"), ("en_US.UTF-8", "en"), ("pt_BR.UTF-8@euro", "pt"), ("C.UTF-8", "en"),
    ("POSIX", "en"), ("zh_CN", "zh-cn"), ("", ""), ("de", "de")])
def test_language_codes_as_fontconfig_names_them(locale, code):
    assert fonts.lang_code(locale) == code


def test_languages_from_kde_and_the_environment(cfg):
    (cfg / "plasma-localerc").write_text("[Translations]\nLANGUAGE=ru:en_US\n[Formats]\nLANG=de_DE.UTF-8\n")
    assert fonts.session_languages({"LANG": "en_US.UTF-8"}) == ["ru", "de", "en"]
    # UI language from LANGUAGE's first entry, formats from LC_TIME/LANG
    (cfg / "plasma-localerc").unlink()
    assert fonts.session_languages({"LANGUAGE": "pl:en", "LC_TIME": "tr_TR.UTF-8"}) == ["pl", "tr"]
    assert fonts.session_languages({}) == ["en"]


@pytest.mark.parametrize("env,family", [
    ({"LANG": "en_US.UTF-8"}, "Figtree"),
    ({"LANG": "de_DE.UTF-8"}, "Figtree"),
    ({"LANG": "ru_RU.UTF-8"}, "Inter"),
    ({"LANG": "en_US.UTF-8", "LC_TIME": "ru_RU.UTF-8"}, "Inter"),   # Cyrillic dates in the clock
    ({"LANGUAGE": "el", "LANG": "en_US.UTF-8"}, "Inter"),
    ({"LANG": "vi_VN.UTF-8"}, "Inter"),
    ({"LANG": "zh_CN.UTF-8"}, "Inter"),
])
def test_the_family_for_a_session(cfg, env, family):
    assert fonts.wanted_family(Runner(cfg), env) == family


def test_russian_session_gets_inter_everywhere_and_keeps_sizes(cfg):
    r = Runner(cfg)
    (cfg / "kdeglobals").write_text("[General]\nfont=Figtree,13,-1,5,500,0,0,0,0,0,0,0,0,0,0,1\n")
    fonts.apply(r, {"LANG": "ru_RU.UTF-8"})
    g = kdeglobals(cfg)
    # the size the person chose (13) stays; Figtree's Medium becomes Inter's Regular
    assert g[("General",)]["font"] == "Inter,13,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
    # keys still on the system default get Inter written for them
    assert g[("General",)]["menuFont"] == "Inter,11,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
    assert g[("General",)]["smallestReadableFont"] == "Inter,10,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
    assert g[("WM",)]["activeFont"] == "Inter,11,-1,5,600,0,0,0,0,0,0,0,0,0,0,1"


def test_back_to_english_restores_figtree(cfg):
    r = Runner(cfg)
    fonts.apply(r, {"LANG": "ru_RU.UTF-8"})
    fonts.apply(r, {"LANG": "en_US.UTF-8"})
    g = kdeglobals(cfg)
    assert g[("General",)]["font"] == "Figtree,11,-1,5,500,0,0,0,0,0,0,0,0,0,0,1"
    assert g[("WM",)]["activeFont"] == "Figtree,11,-1,5,600,0,0,0,0,0,0,0,0,0,0,1"


def test_english_on_the_system_default_writes_nothing(cfg):
    r = Runner(cfg)
    assert fonts.apply(r, {"LANG": "en_US.UTF-8"}) == []
    assert r.wrote() == []


def test_a_font_the_person_chose_is_left_alone(cfg):
    r = Runner(cfg)
    (cfg / "kdeglobals").write_text("[General]\nfont=Noto Sans,12,-1,5,400,0,0,0,0,0,0,0,0,0,0,1\n")
    fonts.apply(r, {"LANG": "ru_RU.UTF-8"})
    assert kdeglobals(cfg)[("General",)]["font"].startswith("Noto Sans,12,")


def test_the_system_default_is_figtree_with_the_mockups_body_size():
    kg = theme.parse_kconfig((ROOT / "system_files/etc/xdg/kdeglobals").read_text())
    for group, key, size, weight in fonts.KEYS:
        assert kg[(group,)][key] == fonts.font_string(fonts.FIGTREE, size, weight or fonts.WEIGHT[fonts.FIGTREE])
    assert kg[("General",)]["fixed"].startswith("JetBrains Mono,")


def test_fontconfig_falls_back_from_figtree_to_inter():
    conf = (ROOT / "system_files/etc/fonts/conf.d/60-lucent-fonts.conf").read_text()
    assert "<family>Figtree</family>" in conf and "<accept><family>Inter</family></accept>" in conf


def test_cli_font_subcommand(cfg, capsys):
    r = Runner(cfg)
    assert cli.main(["font", "--json"], runner=r) == 0
    assert '"family": "' in capsys.readouterr().out
