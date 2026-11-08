from lucent_migrate import keyboard

ANACONDA_RU = '''# Written by systemd-localed(8) or systemd-localed.service
Section "InputClass"
        Identifier "system-keyboard"
        MatchIsKeyboard "on"
        Option "XkbLayout" "us,ru"
        Option "XkbVariant" ","
        Option "XkbOptions" "grp:win_space_toggle,terminate:ctrl_alt_bksp"
EndSection
'''


def test_parse_localed_x11_config():
    assert keyboard.parse_x11_config(ANACONDA_RU) == (["us", "ru"], ["", ""], ["grp:win_space_toggle", "terminate:ctrl_alt_bksp"])
    assert keyboard.parse_x11_config("") == ([], [], [])


def test_no_installer_layout_means_plain_us_and_nothing_written():
    assert keyboard.kxkb_settings([], [], []) is None
    assert keyboard.kxkb_settings(["us"], [""], []) is None


def test_single_non_us_layout_is_used_without_a_switch_key():
    s = keyboard.kxkb_settings(["de"], ["nodeadkeys"], [])
    assert s == {"Use": "true", "LayoutList": "de", "VariantList": "nodeadkeys"}


def test_two_layouts_get_alt_shift_unless_installer_chose_a_switch():
    s = keyboard.kxkb_settings(["us", "ru"], ["", ""], [])
    assert s["LayoutList"] == "us,ru" and s["VariantList"] == ","
    assert s["Options"] == "grp:alt_shift_toggle" and s["ResetOldOptions"] == "true"
    s = keyboard.kxkb_settings(["us", "ru"], ["", ""], ["grp:win_space_toggle", "terminate:ctrl_alt_bksp"])
    assert s["Options"] == "grp:win_space_toggle,terminate:ctrl_alt_bksp"


def test_kwriteconfig_commands_only_when_user_has_no_layouts():
    s = {"Use": "true", "LayoutList": "de", "VariantList": ""}
    cmds = keyboard.write_cmds(s)
    assert ["kwriteconfig6", "--file", "kxkbrc", "--group", "Layout", "--key", "LayoutList", "--", "de"] in cmds
    assert len(cmds) == 3
