from conftest import FakeRunner, fixture

from lucent_settings.backends import network


def wifi_runner():
    return (FakeRunner()
            .on("nmcli", "-t", "-f", "WIFI-HW,WIFI,NETWORKING", "general", out=fixture("nmcli-general-wifi.txt"))
            .on("nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "device", out=fixture("nmcli-device-wifi.txt"))
            .on("nmcli", "-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY,BSSID", out=fixture("nmcli-wifi-list.txt"))
            .on("nmcli", "-t", "-f", "NAME,TYPE,DEVICE", "connection", "show", out=fixture("nmcli-connections.txt")))


def test_split_terse_handles_escapes():
    assert network.split_terse(r"a\:b:c\\d:") == ["a:b", "c\\d", ""]


def test_state_of_the_vm_wired_only():
    r = (FakeRunner()
         .on("nmcli", "-t", "-f", "WIFI-HW,WIFI,NETWORKING", "general", out=fixture("nmcli-general.txt"))
         .on("nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "device", out=fixture("nmcli-device.txt")))
    st = network.Network(r).state()
    assert st.wifi_hardware is False
    assert [(d.name, d.kind, d.connected, d.connection) for d in st.devices] == [
        ("enp0s3", "ethernet", True, "Wired connection 1")]
    assert st.current == "Wired connection 1"
    assert st.wired_connected


def test_state_with_wifi():
    st = network.Network(wifi_runner()).state()
    assert st.wifi_hardware and st.wifi_enabled
    assert st.current == "Home_5G"
    # ethernet without a cable stays listed (to show "Not connected"), p2p does not
    assert [d.name for d in st.devices] == ["wlp2s0", "enp0s31f6"]


def test_scan_dedups_sorts_and_marks_known():
    nets = network.Network(wifi_runner()).scan(rescan=True)
    assert [n.ssid for n in nets] == ["Home_5G", "Office", "Cafe:Guest", "Neighbours", "Back\\slash"]
    home = nets[0]
    assert home.active and home.signal == 82 and home.secure and home.known
    cafe = next(n for n in nets if n.ssid == "Cafe:Guest")
    assert not cafe.secure and cafe.known
    office = next(n for n in nets if n.ssid == "Office")
    assert office.enterprise
    assert network.signal_bars(82) == 4 and network.signal_bars(30) == 2 and network.signal_bars(5) == 1


def test_scan_command(runner):
    network.Network(runner).scan(rescan=True)
    cmd = runner.called("nmcli", "-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY,BSSID")[0]
    assert cmd[-2:] == ["--rescan", "yes"]


def test_wifi_switch(runner):
    network.Network(runner).set_wifi(False)
    assert runner.calls == [["nmcli", "radio", "wifi", "off"]]


def test_connect_with_password_never_puts_it_on_the_command_line(runner):
    res = network.Network(runner).connect("Home 5G", "s3cret pass")
    assert res.ok
    for argv in runner.calls:
        assert "s3cret pass" not in " ".join(argv)
    add, up = runner.calls
    assert add[:4] == ["nmcli", "connection", "add", "type"]
    assert add[add.index("ssid") + 1] == "Home 5G"
    assert add[add.index("con-name") + 1] == "Home 5G"
    assert add[add.index("wifi-sec.key-mgmt") + 1] == "wpa-psk"
    assert up == ["nmcli", "--wait", "30", "connection", "up", "id", "Home 5G", "passwd-file", "/dev/stdin"]
    assert runner.stdin[1] == "802-11-wireless-security.psk:s3cret pass\n"


def test_connect_failure_removes_the_half_made_profile():
    r = FakeRunner().on("nmcli", "--wait", "30", "connection", "up", code=4,
                        err="Error: Connection activation failed: Secrets were required, but not provided.")
    res = network.Network(r).connect("Home", "wrong")
    assert not res.ok
    assert r.calls[-1] == ["nmcli", "connection", "delete", "id", "Home"]


def test_connect_open_or_known_network(runner):
    network.Network(runner).connect("Cafe:Guest", None, known=False)
    assert runner.calls == [["nmcli", "--wait", "30", "device", "wifi", "connect", "Cafe:Guest"]]
    runner.calls.clear()
    network.Network(runner).connect("Home_5G", None, known=True)
    assert runner.calls == [["nmcli", "--wait", "30", "connection", "up", "id", "Home_5G"]]


def test_wired_connect_disconnect(runner):
    n = network.Network(runner)
    n.device_connect("enp0s3")
    n.device_disconnect("enp0s3")
    assert runner.calls == [["nmcli", "--wait", "30", "device", "connect", "enp0s3"],
                            ["nmcli", "device", "disconnect", "enp0s3"]]
