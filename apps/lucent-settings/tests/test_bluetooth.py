from conftest import FakeRunner, fixture

from lucent_settings.backends import bluetooth

OBJS = ("busctl", "--system", "--json=short", "call", "org.bluez", "/")


def test_no_adapter_when_bluez_cant_start():
    r = FakeRunner().on(*OBJS, code=1, err="Call failed: Could not activate remote peer 'org.bluez': unit failed")
    st = bluetooth.Bluetooth(r).state()
    assert st.adapter is None and st.devices == []


def test_state_parses_adapter_and_devices():
    r = FakeRunner().on(*OBJS, out=fixture("bluez-objects.json"))
    st = bluetooth.Bluetooth(r).state()
    assert st.adapter == "/org/bluez/hci0" and st.powered and not st.discovering
    paired = [d for d in st.devices if d.paired]
    assert [(d.name, d.connected, d.kind, d.battery) for d in paired] == [
        ("WH-1000XM5", True, "headphones", 80), ("MX Master 3", False, "mouse", None)]
    nearby = [d for d in st.devices if not d.paired]
    # unnamed devices (alias is just the address) are not offered for pairing
    assert [d.name for d in nearby] == ["JBL Flip 6"]


def test_power_and_discovery_calls(runner):
    bt = bluetooth.Bluetooth(runner)
    bt.set_powered("/org/bluez/hci0", True)
    bt.discover("/org/bluez/hci0", True)
    assert runner.calls == [
        ["busctl", "--system", "set-property", "org.bluez", "/org/bluez/hci0", "org.bluez.Adapter1",
         "Powered", "b", "true"],
        ["busctl", "--system", "--json=short", "call", "org.bluez", "/org/bluez/hci0", "org.bluez.Adapter1",
         "StartDiscovery"],
    ]


def test_pair_trusts_and_connects(runner):
    dev = "/org/bluez/hci0/dev_AA_BB_CC_00_00_04"
    assert bluetooth.Bluetooth(runner).pair(dev).ok
    methods = [c[c.index("org.bluez.Device1") + 1] if "call" in c else c[-3] for c in runner.calls]
    assert methods == ["Pair", "Trusted", "Connect"]
    assert "--timeout=90" in runner.calls[0]


def test_pair_failure_stops(runner):
    r = FakeRunner().on("busctl", "--system", "--json=short", "--timeout=90", code=1,
                        err="Call failed: Authentication Rejected")
    res = bluetooth.Bluetooth(r).pair("/org/bluez/hci0/dev_X")
    assert not res.ok and len(r.calls) == 1


def test_forget_device(runner):
    bluetooth.Bluetooth(runner).forget("/org/bluez/hci0", "/org/bluez/hci0/dev_X")
    assert runner.calls == [["busctl", "--system", "--json=short", "call", "org.bluez", "/org/bluez/hci0",
                             "org.bluez.Adapter1", "RemoveDevice", "o", "/org/bluez/hci0/dev_X"]]
