import json

from conftest import FakeRunner, fixture

from lucent_settings.backends import winapps


def bridge_runner(tmp_path):
    prefix = tmp_path / "prefixes" / "notepadplusplus-bdf24a17"
    prog = prefix / "drive_c" / "Program Files" / "Notepad++"
    prog.mkdir(parents=True)
    (prog / "notepad++.exe").write_bytes(b"x" * 3000)
    (prog / "plugins").mkdir()
    (prog / "plugins" / "a.dll").write_bytes(b"y" * 1000)
    (prog / "link").symlink_to(prog / "notepad++.exe")
    old = "/var/home/lucent/.local/share/lucent-bridge/prefixes/notepadplusplus-bdf24a17"
    desktop = tmp_path / "npp.desktop"
    desktop.write_text(fixture("bridge-app.desktop").replace(old, str(prefix)))
    apps = json.loads(fixture("bridge-list.json"))
    apps[0]["desktop_entries"] = [str(desktop)]
    icon = tmp_path / "icons" / "notepadplusplus.png"
    icon.parent.mkdir()
    icon.write_bytes(b"png")
    apps[0]["icons"] = [str(icon)]
    plan = fixture("bridge-plan.json").replace(old, str(prefix))
    return (FakeRunner()
            .on("lucent-bridge", "list", "--json", out=json.dumps(apps))
            .on("lucent-bridge", "plan", "--json", out=plan)), prefix, prog


def test_list_installed_programs(tmp_path):
    r, prefix, prog = bridge_runner(tmp_path)
    apps = winapps.WinApps(r).apps()
    assert len(apps) == 1
    a = apps[0]
    assert (a.app_id, a.name) == ("notepadplusplus-bdf24a17", "Notepad++")
    assert a.folder == str(prog)
    assert a.exe == str(prog / "notepad++.exe")
    assert a.icon.endswith("notepadplusplus.png")
    assert a.status == "works" and a.exe_arch == "x86_64" and a.runner == "wine-fex"
    assert a.size == 4000  # symlinks are not counted twice
    plan = r.called("lucent-bridge", "plan")[0]
    assert plan == ["lucent-bridge", "plan", "--json", "--assume-tools", str(prog / "notepad++.exe")]


def test_unknown_compat_and_missing_desktop_entry(tmp_path):
    apps = [{"app_id": "foo-00000001", "name": "Foo", "source": "/gone/setup.exe", "runner": "wine",
             "created": 1, "desktop_entries": [], "icons": []}]
    r = FakeRunner().on("lucent-bridge", "list", "--json", out=json.dumps(apps))
    a = winapps.WinApps(r).apps()[0]
    assert a.status == "unknown" and a.exe == "" and a.size is None
    assert a.icon == ""  # a missing icon file is not offered to the UI
    assert not r.called("lucent-bridge", "plan")


def test_no_bridge_or_no_apps():
    assert winapps.WinApps(FakeRunner().on("lucent-bridge", code=127)).apps() == []
    assert winapps.WinApps(FakeRunner().on("lucent-bridge", "list", "--json", out="[]")).apps() == []


def test_remove_and_open_folder(runner):
    w = winapps.WinApps(runner)
    w.remove("notepadplusplus-bdf24a17")
    w.open_folder("/home/x/Program Files/Notepad++")
    assert runner.calls == [["lucent-bridge", "remove", "--yes", "notepadplusplus-bdf24a17"]]
    assert runner.spawned == [["xdg-open", "/home/x/Program Files/Notepad++"]]


def test_mode_line():
    assert winapps.mode("x86_64") == "native"
    assert winapps.mode("aarch64") == "translated"
    assert winapps.mode("riscv64") == "unsupported"


def test_human_size():
    assert winapps.human_size(4000) == "3.9 KB"
    assert winapps.human_size(2570322711) == "2.4 GB"
    assert winapps.human_size(0) == "0 B"
