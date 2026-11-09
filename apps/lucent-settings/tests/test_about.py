from conftest import FakeRunner, fixture

from lucent_settings.backends import about


def test_summary_from_vm_files(tmp_path, monkeypatch):
    (tmp_path / "os-release").write_text(fixture("os-release.txt"))
    (tmp_path / "meminfo").write_text(fixture("meminfo.txt"))
    monkeypatch.setattr(about, "OS_RELEASE", tmp_path / "os-release")
    monkeypatch.setattr(about, "MEMINFO", tmp_path / "meminfo")
    monkeypatch.setattr(about, "DMI", tmp_path / "dmi")
    monkeypatch.setattr(about, "DT_MODEL", tmp_path / "dt-model")
    r = FakeRunner().on("lscpu", "--json", out=fixture("lscpu.json"))
    s = about.About(r).summary()
    assert s.os_name.startswith("Lucent OS 0.1")
    assert s.os_version == "0.1"
    assert s.cpu == "Apple (4 cores)"     # VM: no model name, vendor + core count
    assert s.arch == "aarch64"
    assert 5.0 < s.memory_gb < 6.5
    assert s.model == ""


def test_model_name_from_dmi(tmp_path, monkeypatch):
    dmi = tmp_path / "dmi"
    dmi.mkdir()
    (dmi / "sys_vendor").write_text("LENOVO\n")
    (dmi / "product_version").write_text("ThinkPad T14s Gen 4\n")
    (dmi / "product_name").write_text("21F6CTO1WW\n")
    monkeypatch.setattr(about, "DMI", dmi)
    assert about.machine_model() == "LENOVO ThinkPad T14s Gen 4"
    (dmi / "product_version").write_text("To be filled by O.E.M.\n")
    assert about.machine_model() == "LENOVO 21F6CTO1WW"


def test_cpu_model_on_x86():
    lscpu = '{"lscpu":[{"field":"Architecture:","data":"x86_64"},{"field":"CPU(s):","data":"16"},' \
            '{"field":"Vendor ID:","data":"AuthenticAMD"},' \
            '{"field":"Model name:","data":"AMD Ryzen 7 7840U w/ Radeon 780M Graphics"}]}'
    s = about.About(FakeRunner().on("lscpu", "--json", out=lscpu)).cpu()
    assert s == "AMD Ryzen 7 7840U w/ Radeon 780M Graphics (16 cores)"


def test_advanced_settings_opens_kde_system_settings(runner):
    about.About(runner).open_advanced()
    assert runner.spawned == [["systemsettings"]]


HOSTNAMED = ("busctl", "--system", "--json=short", "get-property", "org.freedesktop.hostname1")


def test_computer_name_from_hostnamed():
    r = FakeRunner().on(*HOSTNAMED, out=fixture("hostnamed.txt"))
    assert about.About(r).computer_name() == about.ComputerName(shown="fedora", static="", pretty="")
    pretty = '{"type":"s","data":"lucent-pc"}\n{"type":"s","data":"lucent-pc"}\n{"type":"s","data":"Anna\'s laptop"}\n'
    r = FakeRunner().on(*HOSTNAMED, out=pretty)
    assert about.About(r).computer_name().shown == "Anna's laptop"


def test_host_name_from_a_display_name():
    assert about.host_name("Anna's Laptop") == "annas-laptop"
    assert about.host_name("  Kitchen PC 2 ") == "kitchen-pc-2"
    assert about.host_name("Ноутбук Анны") == "noutbuk-anny"     # transliterated, not dropped
    assert about.host_name("---") == ""
    assert len(about.host_name("x" * 100)) == 63


class FakeHostnamed:
    def __init__(self, fail: str = ""):
        self.calls, self.fail = [], fail

    def __call__(self, method, *args):
        self.calls.append((method, *args))
        return (False, self.fail) if self.fail else (True, "")


def test_rename_sets_pretty_and_static_name_through_hostnamed(runner):
    hn = FakeHostnamed()
    res = about.About(runner, hn).rename("Ноутбук Анны")
    assert res.ok
    # one process asks polkit for both, so the password is typed once
    assert hn.calls == [("SetStaticHostname", "noutbuk-anny", True), ("SetPrettyHostname", "Ноутбук Анны", True)]


def test_rename_to_a_plain_host_name_clears_the_pretty_name(runner):
    hn = FakeHostnamed()
    assert about.About(runner, hn).rename("kitchen").ok
    assert hn.calls == [("SetStaticHostname", "kitchen", True), ("SetPrettyHostname", "", True)]


def test_rename_refuses_an_empty_name(runner):
    hn = FakeHostnamed()
    res = about.About(runner, hn).rename("  ")
    assert not res.ok
    assert hn.calls == []


def test_rename_reports_a_refused_permission(runner):
    hn = FakeHostnamed(fail="Interactive authentication required.")
    res = about.About(runner, hn).rename("kitchen")
    assert not res.ok
    assert "authentication" in res.message
    assert len(hn.calls) == 1
