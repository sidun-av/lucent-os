"""lucent-devices on recorded (and one constructed) udev/kernel-log fixtures.

See fixtures/README.md for where each fixture comes from.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from lucent_devices import inventory, kernellog, render, udevdb
from lucent_devices.cli import main

HERE = Path(__file__).resolve().parent
FIX = HERE / "fixtures"
ROOT = HERE.parents[1]


def load(name, udev="udev.txt", firmware_dirs=()):
    d = FIX / name
    records = udevdb.parse((d / udev).read_text())
    log = (d / "kernel.log").read_text()
    return inventory.build(records, kernellog.parse(log), kernel_log_source="file",
                           firmware_dirs=firmware_dirs)


def by_name(report, needle):
    hits = [d for d in report["devices"] if needle in d["name"]]
    assert len(hits) == 1, (needle, [d["name"] for d in report["devices"]])
    return hits[0]


# --- udev database parser ---------------------------------------------------

def test_parse_record_fields():
    recs = udevdb.parse(
        "P: /devices/pci0000:00/0000:00:14.3\nM: 0000:00:14.3\nU: pci\nV: iwlwifi\n"
        "E: PCI_CLASS=28000\nE: ID_MODEL_FROM_DATABASE=Wi-Fi 6E AX211\n\n"
        "P: /devices/pci0000:00/0000:00:14.3/net/wlan0\nU: net\nT: wlan\nE: SUBSYSTEM=net\n"
    )
    assert len(recs) == 2
    a, b = recs
    assert a.path == "/devices/pci0000:00/0000:00:14.3"
    assert a.sysname == "0000:00:14.3"
    assert a.subsystem == "pci" and a.driver == "iwlwifi"
    assert a.props["ID_MODEL_FROM_DATABASE"] == "Wi-Fi 6E AX211"
    assert b.sysname == "wlan0" and b.devtype == "wlan" and b.driver is None


def test_parse_real_runner_dump():
    recs = udevdb.parse((FIX / "ci-runner-azure" / "udev.txt").read_text())
    assert len(recs) > 400
    mlx = [r for r in recs if r.sysname == "791e:00:02.0"]
    assert mlx and mlx[0].driver == "mlx5_core"


# --- kernel log ---------------------------------------------------------------

def test_kernel_log_soft_and_hard_firmware_failures():
    ev = kernellog.parse((FIX / "laptop-constructed" / "kernel.log").read_text())
    iwl = [e for e in ev if e.device == "0000:00:14.3"]
    assert {e.file for e in iwl} == {"iwlwifi-so-a0-gf-a0-93.ucode", "iwlwifi-so-a0-gf-a0-92.ucode"}
    assert all(e.kind == "firmware" and not e.fatal for e in iwl)
    i915 = [e for e in ev if e.device == "0000:00:02.0" and e.fatal]
    assert i915 and i915[0].file == "i915/adlp_dmc.bin"
    bt = [e for e in ev if e.device == "hci0"]
    assert any(e.fatal and e.file == "intel/ibt-0040-0041.sfi" for e in bt)
    probe = [e for e in ev if e.kind == "probe"]
    assert probe and probe[0].device == "0000:04:00.0" and probe[0].error == -2


def test_kernel_log_formats_dmesg_and_short():
    text = (
        "[    4.123456] iwlwifi 0000:00:14.3: Direct firmware load for x.ucode failed with error -2\n"
        "Nov 09 10:00:00 lucent-pc kernel: mt7921e 0000:01:00.0: probe with driver mt7921e failed with error -110\n"
        "Nov 09 10:00:01 lucent-pc kernel: r8169: probe of 0000:03:00.0 failed with error -5\n"
    )
    ev = kernellog.parse(text)
    assert [(e.kind, e.device, e.error) for e in ev] == [
        ("firmware", "0000:00:14.3", -2), ("probe", "0000:01:00.0", -110), ("probe", "0000:03:00.0", -5)]


# --- real: GitHub runner (Hyper-V), image as a container ---------------------

def test_runner_all_working_and_grouped():
    r = load("ci-runner-azure")
    assert r["kernel_log"]["readable"] is True
    s = r["summary"]
    assert s["problem"] == 0 and s["needs_driver"] == 0
    assert s["working"] == s["total"] >= 5
    eth = by_name(r, "ConnectX-5")
    assert eth["group"] == "ethernet" and eth["driver"] == "mlx5_core" and eth["status"] == "working"
    assert eth["vendor"] == "Mellanox Technologies"
    assert by_name(r, "Hyper-V Video")["group"] == "display"
    assert by_name(r, "Hyper-V SCSI Controller")["group"] == "storage"
    kbd = by_name(r, "AT Translated Set 2 keyboard")
    assert kbd["group"] == "input" and kbd["driver"] == "atkbd"
    assert by_name(r, "HID-compliant Mouse")["group"] == "input"


def test_runner_with_nic_unknown_to_hwdb_gets_a_class_name():
    # A second real runner: Microsoft MANA NIC, whose model the hwdb doesn't know.
    r = load("ci-runner-azure-mana")
    nic = [d for d in r["devices"] if d["ids"] == {"vendor": "1414", "device": "00ba"}][0]
    assert nic["name"] == "Ethernet controller 1414:00ba"
    assert nic["group"] == "ethernet" and nic["status"] == "working" and nic["driver"] == "mana"
    assert r["summary"]["problem"] == 0


def test_runner_regulatory_db_noise_is_not_pinned_on_a_device():
    r = load("ci-runner-azure")
    for d in r["devices"]:
        assert all("regulatory" not in f["file"] for f in d["firmware"]), d


# --- constructed laptop -----------------------------------------------------

@pytest.fixture
def laptop(tmp_path):
    fw = tmp_path / "firmware"
    fw.mkdir()
    (fw / "iwlwifi-so-a0-gf-a0-89.ucode").write_bytes(b"")
    return load("laptop-constructed", firmware_dirs=[fw])


def test_wifi_firmware_fallback_is_working_not_a_problem(laptop):
    wifi = by_name(laptop, "AX211 160MHz")
    assert wifi["group"] == "wifi" and wifi["status"] == "working" and wifi["driver"] == "iwlwifi"
    assert len(wifi["firmware"]) == 2 and not any(f["fatal"] for f in wifi["firmware"])
    assert wifi["problems"] == []


def test_gpu_missing_dmc_firmware_is_a_problem(laptop):
    gpu = by_name(laptop, "Iris Xe")
    assert gpu["group"] == "display" and gpu["status"] == "problem"
    assert gpu["problems"] == [{"code": "firmware_missing", "file": "i915/adlp_dmc.bin", "error": -2,
                                "present": False}]


def test_bluetooth_firmware_failure_via_hci_name(laptop):
    bt = by_name(laptop, "AX211 Bluetooth")
    assert bt["group"] == "bluetooth" and bt["status"] == "problem" and bt["driver"] == "btusb"
    assert bt["problems"][0]["code"] == "firmware_missing"
    assert bt["problems"][0]["file"] == "intel/ibt-0040-0041.sfi"
    assert bt["bus"] == "usb" and bt["ids"] == {"vendor": "8087", "device": "0033"}


def test_unclaimed_broadcom_needs_driver_with_hint(laptop):
    bcm = by_name(laptop, "BCM4352")
    assert bcm["group"] == "wifi" and bcm["status"] == "needs_driver" and bcm["driver"] is None
    assert bcm["problems"] == [{"code": "no_driver"}]
    assert bcm["hint"] == "broadcom-wl"


def test_probe_failure_with_firmware_is_a_problem(laptop):
    rtw = by_name(laptop, "RTL8852BE")
    assert rtw["status"] == "problem" and rtw["driver"] is None
    codes = [p["code"] for p in rtw["problems"]]
    assert "firmware_missing" in codes and "probe_failed" in codes


def test_groups_from_children_and_interfaces(laptop):
    assert by_name(laptop, "Integrated Camera")["group"] == "camera"
    assert by_name(laptop, "Integrated Camera")["driver"] == "uvcvideo"
    assert by_name(laptop, "Ultra Fit")["group"] == "storage"
    assert by_name(laptop, "Mouse")["group"] == "input"
    assert by_name(laptop, "Touchpad")["group"] == "input"
    assert by_name(laptop, "Touchpad")["driver"] == "i2c_hid_acpi"
    assert by_name(laptop, "High Definition Audio")["group"] == "sound"
    assert by_name(laptop, "NVMe SSD")["group"] == "storage"
    assert by_name(laptop, "RTL8111")["group"] == "ethernet"
    assert by_name(laptop, "USB 3.2 xHCI")["group"] == "other"


def test_infrastructure_is_hidden_or_system(laptop):
    names = [d["name"] for d in laptop["devices"]]
    assert not any("Host Bridge" in n or "Root Port" in n for n in names)   # bridges: never
    assert not any("root hub" in n for n in names)
    assert not any(n == "Power Button" for n in names)
    smbus = by_name(laptop, "SMBus")
    assert smbus["system"] is True and smbus["status"] == "working"
    dptf = by_name(laptop, "Innovation Platform Framework")
    assert dptf["system"] is True and dptf["status"] == "unused"


def test_vendor_specific_usb_without_driver_is_unused_not_missing(laptop):
    fp = [d for d in laptop["devices"] if d["ids"] == {"vendor": "06cb", "device": "00a8"}][0]
    assert fp["status"] == "unused" and fp["name"]


def test_summary_and_order(laptop):
    s = laptop["summary"]
    assert s == {"total": s["total"], "working": s["working"], "needs_driver": 1, "problem": 3,
                 "unused": s["unused"], "system": s["system"]}
    # total counts what a person sees: not system parts, not unused ones
    visible = [d for d in laptop["devices"] if not d["system"] and d["status"] != "unused"]
    assert s["total"] == len(visible) == s["working"] + s["needs_driver"] + s["problem"]
    statuses = [d["status"] for d in laptop["devices"]]
    first_ok = statuses.index("working")
    assert set(statuses[:first_ok]) <= {"problem", "needs_driver"}
    assert "problem" not in statuses[first_ok:] and "needs_driver" not in statuses[first_ok:]


def test_hard_rfkill_switch_marks_wifi(tmp_path):
    text = (FIX / "laptop-constructed" / "udev.txt").read_text() + (
        "\nP: /devices/platform/ideapad_acpi/rfkill/rfkill0\nU: rfkill\n"
        "E: RFKILL_TYPE=wlan\nE: RFKILL_STATE=2\nE: SUBSYSTEM=rfkill\n")
    r = inventory.build(udevdb.parse(text), [], kernel_log_source="file")
    wifi = by_name(r, "AX211 160MHz")
    assert wifi["status"] == "problem"
    assert {"code": "switched_off"} in wifi["problems"]


def test_soft_rfkill_is_only_a_note(laptop):
    text = (FIX / "laptop-constructed" / "udev.txt").read_text().replace(
        "E: RFKILL_NAME=hci0\nE: RFKILL_TYPE=bluetooth\nE: RFKILL_STATE=1",
        "E: RFKILL_NAME=hci0\nE: RFKILL_TYPE=bluetooth\nE: RFKILL_STATE=0")
    r = inventory.build(udevdb.parse(text), [], kernel_log_source="file")
    bt = by_name(r, "AX211 Bluetooth")
    assert bt["status"] == "working" and "turned_off" in bt["notes"]


def test_unreadable_kernel_log_is_reported_not_guessed():
    recs = udevdb.parse((FIX / "laptop-constructed" / "udev.txt").read_text())
    r = inventory.build(recs, None, kernel_log_source=None)
    assert r["kernel_log"] == {"readable": False, "source": None}
    assert by_name(r, "Iris Xe")["status"] == "working"   # nothing known against it


# --- output -------------------------------------------------------------------

def test_json_is_stable_and_serialisable(laptop):
    data = json.loads(json.dumps(laptop))
    assert data["schema"] == 1
    for d in data["devices"]:
        assert set(d) >= {"id", "group", "name", "vendor", "bus", "ids", "driver", "drivers",
                          "status", "problems", "firmware", "notes", "system", "hint", "syspath"}


def test_text_english(laptop):
    out = render.text(laptop, lang="en")
    assert out.splitlines()[0] == "4 of 14 devices need attention."
    assert "Needs a driver" in out and "Has a problem" in out
    assert "Broadcom" in out and "i915/adlp_dmc.bin" in out
    assert "SMBus" not in out             # system parts only with --all
    assert render.text(laptop, lang="en", show_all=True).count("SMBus") == 1


def test_text_russian(laptop):
    out = render.text(laptop, lang="ru")
    assert out.splitlines()[0] == "Устройств, требующих внимания: 4 из 14."
    assert "Нужен драйвер" in out and "Есть проблема" in out


def test_text_all_working_summary():
    r = load("ci-runner-azure")
    n = r["summary"]["total"]
    assert render.text(r, lang="en").splitlines()[0] == f"All {n} devices are working."
    assert render.text(r, lang="ru").splitlines()[0] == f"Все устройства работают ({n})."


# --- command line ------------------------------------------------------------

def test_cli_json_from_files(capsys):
    d = FIX / "ci-runner-azure"
    rc = main(["--json", "--udev-db", str(d / "udev.txt"), "--kernel-log", str(d / "kernel.log")])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["summary"]["problem"] == 0 and data["kernel_log"]["source"] == "file"


def test_cli_exit_code_signals_problems(capsys):
    d = FIX / "laptop-constructed"
    assert main(["--udev-db", str(d / "udev.txt"), "--kernel-log", str(d / "kernel.log")]) == 1


def test_wrapper_script_runs():
    env = {"PYTHONPATH": "", "PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}
    d = FIX / "ci-runner-azure"
    script = ROOT / "system_files" / "usr" / "bin" / "lucent-devices"
    src = script.read_text().replace('"/usr/lib/lucent"', repr(str(ROOT / "system_files/usr/lib/lucent")))
    p = subprocess.run([sys.executable, "-c", src, "--json", "--udev-db", str(d / "udev.txt"),
                        "--kernel-log", str(d / "kernel.log")], capture_output=True, text=True, env=env)
    assert p.returncode == 0, p.stderr
    assert json.loads(p.stdout)["schema"] == 1


def test_no_network_imports():
    pkg = ROOT / "system_files" / "usr" / "lib" / "lucent" / "lucent_devices"
    for f in pkg.glob("*.py"):
        src = f.read_text()
        for bad in ("socket", "urllib", "http.client", "requests"):
            assert f"import {bad}" not in src and f"from {bad}" not in src, (f, bad)
