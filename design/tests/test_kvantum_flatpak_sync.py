"""/usr/libexec/lucent/kvantum-flatpak-sync: Flatpak Qt apps get the active
Lucent Kvantum theme (accent and light/dark) in their own config dir."""
import importlib.machinery
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "system_files/usr/libexec/lucent/kvantum-flatpak-sync"


def load():
    loader = importlib.machinery.SourceFileLoader("kvantum_flatpak_sync", str(SCRIPT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


@pytest.fixture
def sync(tmp_path, monkeypatch):
    mod = load()
    share = tmp_path / "share/Kvantum"
    for folder in ("Lucent", "LucentRose"):
        (share / folder).mkdir(parents=True)
        (share / folder / f"{folder}.kvconfig").write_text(folder)
        (share / folder / f"{folder}Dark.kvconfig").write_text(folder + "Dark")
    home = tmp_path / "home"
    (home / ".config/Kvantum").mkdir(parents=True)
    monkeypatch.setattr(mod, "THEMES", share)
    monkeypatch.setattr(mod, "HOME", home)
    monkeypatch.setattr(mod, "CONFIG", home / ".config")
    monkeypatch.setattr(mod, "kde_apps", lambda: ["org.kde.okular"])
    return mod, home


def app_conf(home):
    return home / ".var/app/org.kde.okular/config/Kvantum"


def test_accent_and_dark_variant(sync):
    mod, home = sync
    (home / ".config/Kvantum/kvantum.kvconfig").write_text("[General]\ntheme=LucentRose\n")
    mod.desktop_is_dark = lambda: True
    mod.main()
    assert (app_conf(home) / "kvantum.kvconfig").read_text().endswith("theme=LucentRoseDark\n")
    assert (app_conf(home) / "LucentRose/LucentRoseDark.kvconfig").read_text() == "LucentRoseDark"


def test_switching_back_drops_the_old_accent_copy(sync):
    mod, home = sync
    (home / ".config/Kvantum/kvantum.kvconfig").write_text("[General]\ntheme=LucentRose\n")
    mod.desktop_is_dark = lambda: False
    mod.main()
    (home / ".config/Kvantum/kvantum.kvconfig").write_text("[General]\ntheme=Lucent\n")
    mod.main()
    assert (app_conf(home) / "kvantum.kvconfig").read_text().endswith("theme=Lucent\n")
    assert not (app_conf(home) / "LucentRose").exists()


def test_foreign_theme_falls_back_to_lucent(sync):
    mod, home = sync
    (home / ".config/Kvantum/kvantum.kvconfig").write_text("[General]\ntheme=KvArc\n")
    mod.desktop_is_dark = lambda: False
    mod.main()
    assert (app_conf(home) / "kvantum.kvconfig").read_text().endswith("theme=Lucent\n")


def test_the_apps_own_choice_is_kept(sync):
    mod, home = sync
    app_conf(home).mkdir(parents=True)
    (app_conf(home) / "kvantum.kvconfig").write_text("[General]\ntheme=KvArc\n")
    mod.desktop_is_dark = lambda: False
    mod.main()
    assert (app_conf(home) / "kvantum.kvconfig").read_text() == "[General]\ntheme=KvArc\n"
