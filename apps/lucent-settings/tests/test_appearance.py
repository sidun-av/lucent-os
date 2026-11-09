from pathlib import Path

from conftest import FakeRunner

from lucent_settings.backends import appearance


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def test_mode_from_kdeglobals(xdg_config):
    home, sysdir = xdg_config
    write(sysdir / "kdeglobals", "[KDE]\nLookAndFeelPackage=org.lucent.desktop\n")
    a = appearance.Appearance(FakeRunner())
    assert a.mode() == "light"
    write(home / "kdeglobals", "[KDE]\nLookAndFeelPackage=org.lucent.desktop.dark\n")
    assert a.mode() == "dark"
    write(home / "kdeglobals", "[KDE]\nAutomaticLookAndFeel=true\nLookAndFeelPackage=org.lucent.desktop.dark\n")
    assert a.mode() == "auto"


def test_switch_to_dark_keeps_window_buttons_and_accent(xdg_config):
    home, _ = xdg_config
    write(home / "kwinrc", "[org.kde.kdecoration2]\nButtonsOnLeft=XIA\nButtonsOnRight=\n")
    write(home / "lucent-settingsrc", "[Appearance]\nAccent=#e5487d\n")
    r = FakeRunner()
    appearance.Appearance(r).set_mode("dark")
    assert r.calls[0] == ["plasma-apply-lookandfeel", "-a", "org.lucent.desktop.dark"]
    assert ["plasma-apply-colorscheme", "--accent-color", "#e5487d"] in r.calls
    writes = [c for c in r.calls if c[0] == "kwriteconfig6"]
    assert ["kwriteconfig6", "--file", "kwinrc", "--group", "org.kde.kdecoration2", "--key", "ButtonsOnLeft",
            "--notify", "XIA"] in writes
    assert r.called("busctl", "--user", "--json=short", "call", "org.kde.KWin", "/KWin")


def test_auto_mode_lets_plasma_switch(xdg_config):
    r = FakeRunner()
    appearance.Appearance(r).set_mode("auto")
    assert r.calls[0] == ["kwriteconfig6", "--file", "kdeglobals", "--group", "KDE", "--key",
                          "AutomaticLookAndFeel", "--notify", "--type", "bool", "true"]
    assert not r.called("plasma-apply-lookandfeel")


def test_accent(xdg_config):
    home, _ = xdg_config
    r = FakeRunner()
    a = appearance.Appearance(r)
    assert a.accent() == appearance.ACCENTS[0]
    a.set_accent("#1f9d55")
    assert r.calls[0] == ["plasma-apply-colorscheme", "--accent-color", "#1f9d55"]
    assert "Accent=#1f9d55" in (home / "lucent-settingsrc").read_text()
    assert a.accent() == "#1f9d55"
    # the default blue goes back to the theme's own colours (light and dark differ)
    r.calls.clear()
    a.set_accent(appearance.ACCENTS[0])
    assert r.calls[0] == ["plasma-apply-lookandfeel", "-k", "-a", "org.lucent.desktop"]
    assert "Accent" not in (home / "lucent-settingsrc").read_text()


def test_accent_sync_reapplies_only_when_lost(xdg_config):
    home, _ = xdg_config
    write(home / "lucent-settingsrc", "[Appearance]\nAccent=#e5487d\n")
    write(home / "kdeglobals", "[Colors:Selection]\nBackgroundNormal=91,139,255\n")
    r = FakeRunner()
    assert appearance.sync_accent(r) is True
    assert r.calls == [["plasma-apply-colorscheme", "--accent-color", "#e5487d"]]
    # Plasma derives the selection from the accent; once it is pinkish, nothing to do
    write(home / "kdeglobals", "[Colors:Selection]\nBackgroundNormal=236,126,163\n")
    r.calls.clear()
    assert appearance.sync_accent(r) is False and r.calls == []


def test_wallpapers(tmp_path, monkeypatch, xdg_config):
    home, _ = xdg_config
    sysw = tmp_path / "wallpapers"
    write(sysw / "Lucent" / "metadata.json", '{"KPlugin": {"Id": "Lucent", "Name": "Lucent"}}')
    write(sysw / "Lucent" / "contents" / "images" / "3840x2160.jpg", "x")
    write(sysw / "Lucent" / "contents" / "images_dark" / "3840x2160.jpg", "x")
    write(sysw / "Mountain" / "metadata.json", '{"KPlugin": {"Id": "Mountain", "Name": "Mountain"}}')
    write(sysw / "Mountain" / "contents" / "images" / "1920x1080.png", "x")
    write(sysw / "Broken" / "metadata.json", "{")
    pics = tmp_path / "Pictures"
    write(pics / "beach.JPG", "x")
    write(pics / "notes.txt", "x")
    write(pics / "Wallpapers" / "forest.webp", "x")
    monkeypatch.setattr(appearance, "SYSTEM_WALLPAPERS", sysw)
    monkeypatch.setattr(appearance, "user_wallpaper_packages", lambda: tmp_path / "no-user-packages")
    monkeypatch.setattr(appearance, "user_picture_dirs", lambda: [pics / "Wallpapers", pics])
    write(home / "plasma-org.kde.plasma.desktop-appletsrc",
          "[Containments][1]\nplugin=org.kde.plasma.folder\nwallpaperplugin=org.kde.image\n\n"
          "[Containments][1][Wallpaper][org.kde.image][General]\nImage=file:///usr/share/wallpapers/Lucent/\n")
    a = appearance.Appearance(FakeRunner())
    walls = a.wallpapers()
    assert [(w.name, w.ours) for w in walls] == [("Lucent", True), ("Mountain", True),
                                                ("forest", False), ("beach", False)]
    assert walls[0].thumbnail.endswith("images/3840x2160.jpg")
    assert walls[0].thumbnail_dark.endswith("images_dark/3840x2160.jpg")
    assert walls[1].thumbnail_dark == ""  # Mountain has no night version
    assert a.current_wallpaper() == "/usr/share/wallpapers/Lucent"
    r = FakeRunner()
    appearance.Appearance(r).set_wallpaper(str(sysw / "Lucent"))
    assert r.calls == [["plasma-apply-wallpaperimage", str(sysw / "Lucent")]]


def test_animations_and_text_size(xdg_config):
    home, sysdir = xdg_config
    write(sysdir / "kdeglobals", "[KDE]\nAnimationDurationFactor=0.7\n[General]\n"
          "font=Inter,11,-1,5,400,0,0,0,0,0,0,0,0,0,0,1\n")
    r = FakeRunner()
    a = appearance.Appearance(r)
    assert a.animations() == "fast" and a.text_size() == 11
    a.set_animations("off")
    assert r.calls[-1][-2:] == ["--notify", "0"]
    a.set_text_size(13)
    fonts = {c[c.index("--key") + 1]: c[-1] for c in r.calls if "--key" in c and "font" in c[c.index("--key") + 1].lower()}
    assert fonts["font"] == "Inter,13,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
    assert fonts["smallestReadableFont"].startswith("Inter,12,")
    assert fonts["activeFont"].startswith("Inter,13,") and ",600," in fonts["activeFont"]
    assert r.called("busctl", "--user", "emit", "/KDEPlatformTheme")

