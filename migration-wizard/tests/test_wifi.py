from lucent_migrate import wifi
from lucent_migrate.wifi import WifiProfile


def test_find_profiles_dedups_and_skips_broken(windows_root):
    profiles = wifi.find_profiles(windows_root)
    assert profiles == [
        WifiProfile(ssid="HomeNet", security="wpa-psk", had_password=True),
        WifiProfile(ssid="Office", security="wpa-eap", had_password=True),
        WifiProfile(ssid="Кафе & Ко", security="open", had_password=False),
    ]


def test_find_profiles_without_programdata(tmp_path):
    assert wifi.find_profiles(tmp_path) == []


def test_nmcli_psk_asks_password_on_connect():
    args = wifi.nmcli_add_args(WifiProfile("HomeNet", "wpa-psk", True))
    assert args[:4] == ["nmcli", "connection", "add", "type"]
    assert args[args.index("ssid") + 1] == "HomeNet"
    assert args[args.index("con-name") + 1] == "HomeNet"
    assert args[args.index("wifi-sec.key-mgmt") + 1] == "wpa-psk"
    # 1 = agent-owned: Plasma asks the password on first connect, nothing is stored
    assert args[args.index("wifi-sec.psk-flags") + 1] == "1"


def test_nmcli_open_network_has_no_security():
    args = wifi.nmcli_add_args(WifiProfile("Кафе & Ко", "open", False))
    assert "wifi-sec.key-mgmt" not in args


def test_nmcli_eap_is_not_importable():
    assert wifi.nmcli_add_args(WifiProfile("Office", "wpa-eap", True)) is None
