import json

from conftest import FakeRunner, fixture

from lucent_settings.backends import display


def test_outputs_from_kscreen_doctor():
    r = FakeRunner().on("kscreen-doctor", "-j", out=fixture("kscreen.json"))
    outs = display.Display(r).outputs()
    assert len(outs) == 1
    o = outs[0]
    assert (o.name, o.width, o.height, o.scale) == ("Virtual-1", 2560, 1440, 1.0)
    assert o.current_mode == "1"
    sizes = [(m.width, m.height) for m in o.modes]
    assert sizes[0] == (5120, 2160) and (2560, 1440) in sizes
    assert len(sizes) == len(set(sizes)), "one entry per resolution"
    assert sizes == sorted(sizes, key=lambda s: (-s[0] * s[1], -s[0]))


def test_highest_refresh_wins_per_size():
    data = json.loads(fixture("kscreen.json"))
    out = data["outputs"][0]
    out["modes"].append({"id": "99", "name": "2560x1440@144", "refreshRate": 143.9,
                         "size": {"width": 2560, "height": 1440}})
    r = FakeRunner().on("kscreen-doctor", "-j", out=json.dumps(data))
    o = display.Display(r).outputs()[0]
    qhd = next(m for m in o.modes if (m.width, m.height) == (2560, 1440))
    assert qhd.id == "99" and o.current_size == (2560, 1440)
    fhd = [m for m in o.modes if (m.width, m.height) == (1920, 1080)]
    assert [m.id for m in fhd] == ["13"]  # 60 Hz beats 50 Hz


def test_disconnected_outputs_are_skipped():
    data = json.loads(fixture("kscreen.json"))
    data["outputs"].append(dict(data["outputs"][0], id=2, name="HDMI-A-1", connected=False))
    r = FakeRunner().on("kscreen-doctor", "-j", out=json.dumps(data))
    assert [o.name for o in display.Display(r).outputs()] == ["Virtual-1"]


def test_set_mode_and_scale_commands(runner):
    d = display.Display(runner)
    d.set_mode("Virtual-1", "10")
    d.set_scale("Virtual-1", 1.25)
    d.set_scale("Virtual-1", 2.0)
    assert runner.calls == [["kscreen-doctor", "output.Virtual-1.mode.10"],
                            ["kscreen-doctor", "output.Virtual-1.scale.1.25"],
                            ["kscreen-doctor", "output.Virtual-1.scale.2"]]


def test_scale_choices_and_labels():
    assert display.SCALES == [1.0, 1.25, 1.5, 1.75, 2.0]
    assert display.scale_label(1.25) == "125%"
    assert display.recommended_scale(2560, 1440, 650) == 1.0     # 27" QHD
    assert display.recommended_scale(2880, 1800, 300) == 2.0     # 14" laptop, high DPI
    assert display.recommended_scale(1920, 1080, 344) == 1.25    # 15.6" FHD


def test_night_light(xdg_config):
    home, _ = xdg_config
    r = FakeRunner().on("busctl", "--user", "--json=short", "get-property", "org.kde.KWin",
                        out='{"type":"b","data":true}\n{"type":"b","data":false}\n')
    d = display.Display(r)
    assert d.night_light() == (True, False)
    d.set_night_light(True)
    assert r.calls[-1] == ["kwriteconfig6", "--file", "kwinrc", "--group", "NightColor", "--key", "Active",
                           "--notify", "--type", "bool", "true"]
