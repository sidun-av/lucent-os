"""The read-only rule for Windows partitions
(system_files/usr/lib/udev/rules.d/99-lucent-windows-readonly.rules) must
catch the computer's own internal Windows disk and nothing a user plugs in:
a Windows user expects to write to their own NTFS USB stick or external
drive.

A USB stick gets ID_BUS=usb from udev's usb_id, but a USB hard disk or SSD
in a SATA enclosure ("non-removable USB mass storage") gets ID_BUS=ata:
60-persistent-storage.rules runs ata_id on it, which talks to the disk
through the bridge. So "ID_BUS == usb" alone is not "plugged in by USB".

The rule file is evaluated here by a tiny interpreter for exactly the udev
syntax it uses (match keys on the device, SUBSYSTEMS on the device and its
parents, GOTO/LABEL, ENV assignment); anything else fails the test, so the
interpreter cannot silently diverge from the file.
"""
import fnmatch
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RULE = ROOT / "system_files/usr/lib/udev/rules.d/99-lucent-windows-readonly.rules"

TOKEN = re.compile(r'\s*([A-Z]+)(?:\{([^}]*)\})?\s*(==|!=|\+=|=)\s*"([^"]*)"\s*,?')


def parse(text):
    rules = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        pos, toks = 0, []
        while pos < len(line):
            m = TOKEN.match(line, pos)
            assert m, f"unsupported udev syntax: {line[pos:]!r}"
            toks.append(m.groups())
            pos = m.end()
        rules.append(toks)
    return rules


def evaluate(text, dev):
    """dev: {"kernel", "subsystem", "env": {...}, "parents": [subsystems]}.
    Returns the device's ENV after the rule file ran."""
    env = dict(dev["env"])
    rules = parse(text)
    labels = {toks[0][3]: i for i, toks in enumerate(rules) if toks[0][0] == "LABEL"}
    i = 0
    while i < len(rules):
        toks, i, jump = rules[i], i + 1, None
        matched, actions = True, []
        for key, attr, op, val in toks:
            if op in ("==", "!="):
                if key == "SUBSYSTEM":
                    values = [dev["subsystem"]]
                elif key == "SUBSYSTEMS":
                    values = [dev["subsystem"], *dev["parents"]]
                elif key == "KERNEL":
                    values = [dev["kernel"]]
                elif key == "ENV":
                    values = [env.get(attr, "")]
                else:
                    raise AssertionError(f"unsupported match key {key}")
                hit = any(fnmatch.fnmatchcase(v, p) for v in values for p in val.split("|"))
                if hit != (op == "=="):
                    matched = False
                    break
            elif key == "LABEL":
                pass
            elif key == "GOTO":
                actions.append(("goto", val))
            elif key == "ENV" and op == "=":
                actions.append(("env", attr, val))
            else:
                raise AssertionError(f"unsupported action {key}{op}")
        if not matched:
            continue
        for a in actions:
            if a[0] == "goto":
                jump = labels[a[1]]
            else:
                env[a[1]] = a[2]
        if jump is not None:
            i = jump
    return env


def readonly(dev):
    env = evaluate(RULE.read_text(), dev)
    allowed = env.get("UDISKS_MOUNT_OPTIONS_ALLOW")
    return env.get("UDISKS_MOUNT_OPTIONS_DEFAULTS") == "ro" and allowed is not None and "rw" not in allowed.split(",")


def part(kernel, fs="ntfs", bus=None, parents=()):
    env = {"ID_FS_TYPE": fs, "DEVTYPE": "partition"}
    if bus:
        env["ID_BUS"] = bus
    return {"kernel": kernel, "subsystem": "block", "env": env, "parents": list(parents)}


SATA = ["block", "scsi", "ata", "pci"]
USB = ["block", "scsi", "usb", "usb", "pci"]


def test_internal_windows_disks_are_read_only():
    assert readonly(part("sda3", bus="ata", parents=SATA))           # SATA SSD/HDD
    assert readonly(part("nvme0n1p3", parents=["block", "nvme", "pci"]))   # NVMe: no ID_BUS
    assert readonly(part("vdb1", parents=["block", "virtio", "pci"]))       # VM disk


def test_usb_stick_is_writable():
    assert not readonly(part("sdb1", bus="usb", parents=USB))


def test_usb_hard_disk_in_a_sata_enclosure_is_writable():
    # ata_id answered through the USB-SATA bridge: ID_BUS=ata, but the
    # disk hangs off the USB bus.
    assert not readonly(part("sdb1", bus="ata", parents=USB))


def test_sd_cards_are_writable():
    assert not readonly(part("mmcblk0p1", parents=["block", "mmc", "mmc_host", "pci"]))
    assert not readonly(part("sdc1", bus="usb", parents=USB))      # USB card reader


def test_other_file_systems_are_untouched():
    for fs in ("vfat", "exfat", "btrfs", "ext4"):
        assert not readonly(part("sda2", fs=fs, bus="ata", parents=SATA))


def test_whole_disk_ntfs_without_partition_table_on_usb_is_writable():
    d = part("sdb", bus="ata", parents=USB)
    d["env"]["DEVTYPE"] = "disk"
    assert not readonly(d)
