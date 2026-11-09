from pathlib import Path

from conftest import FakeRunner

from lucent_settings.backends import habits


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def test_double_click_default_and_switch(xdg_config):
    home, sysdir = xdg_config
    write(sysdir / "kdeglobals", "[KDE]\nSingleClick=false\n")
    r = FakeRunner()
    h = habits.Habits(r)
    assert h.double_click() is True
    h.set_double_click(False)
    assert r.calls == [
        ["kwriteconfig6", "--file", "kdeglobals", "--group", "KDE", "--key", "SingleClick", "--notify",
         "--type", "bool", "true"],
        ["busctl", "--user", "emit", "/KGlobalSettings", "org.kde.KGlobalSettings", "notifyChange", "ii", "3", "0"],
    ]


def test_layout_switch_reads_and_keeps_other_options(xdg_config):
    home, sysdir = xdg_config
    write(sysdir / "kxkbrc", "[Layout]\nOptions=grp:alt_shift_toggle\nResetOldOptions=true\n")
    r = FakeRunner()
    h = habits.Habits(r)
    assert h.layout_switch() == "alt_shift"
    assert h.layout_count() == 1
    write(home / "kxkbrc", "[Layout]\nLayoutList=us,ru\nOptions=caps:none,grp:alt_shift_toggle,lv3:ralt_switch\n")
    assert h.layout_count() == 2
    h.set_layout_switch("win_space")
    assert r.calls[0][-1] == "caps:none,lv3:ralt_switch"
    assert r.calls[-1] == ["busctl", "--user", "emit", "/Layouts", "org.kde.keyboard", "reloadConfig"]
    r.calls.clear()
    h.set_layout_switch("ctrl_shift")
    assert r.calls[0][-1] == "caps:none,lv3:ralt_switch,grp:ctrl_shift_toggle"
    write(home / "kxkbrc", "[Layout]\nOptions=\n")
    assert h.layout_switch() == "win_space"


def test_window_buttons(xdg_config):
    home, sysdir = xdg_config
    write(sysdir / "kwinrc", "")
    r = FakeRunner()
    h = habits.Habits(r)
    assert h.buttons_side() == "right"
    h.set_buttons_side("left")
    keys = {c[c.index("--key") + 1]: c[-1] for c in r.calls if c[0] == "kwriteconfig6"}
    assert keys == {"ButtonsOnLeft": "XIA", "ButtonsOnRight": ""}
    assert r.calls[-1][-3:] == ["/KWin", "org.kde.KWin", "reconfigure"]
    write(home / "kwinrc", "[org.kde.kdecoration2]\nButtonsOnLeft=XIA\nButtonsOnRight=\n")
    assert h.buttons_side() == "left"


def test_shortcut_table_is_what_lucent_binds():
    names = [s.action for s in habits.SHORTCUTS]
    assert len(names) == 8 and len(set(names)) == 8
    assert habits.SHORTCUTS[0].keys == ["Win"]
