import json

from lucent_migrate import volumes
from lucent_migrate.volumes import Volume

GIB = 1024**3

LSBLK = {
    "blockdevices": [
        {
            "name": "nvme0n1", "path": "/dev/nvme0n1", "type": "disk", "fstype": None,
            "size": 512 * GIB, "label": None, "uuid": None, "parttype": None,
            "rm": False, "hotplug": False, "mountpoints": [None],
            "children": [
                {"name": "nvme0n1p1", "path": "/dev/nvme0n1p1", "type": "part", "fstype": "vfat",
                 "size": 260 * 1024**2, "label": "SYSTEM", "uuid": "AB12-CD34",
                 "parttype": "c12a7328-f81f-11d2-ba4b-00a0c93ec93b", "rm": False, "hotplug": False,
                 "mountpoints": ["/boot/efi"]},
                {"name": "nvme0n1p3", "path": "/dev/nvme0n1p3", "type": "part", "fstype": "ntfs",
                 "size": 300 * GIB, "label": "OS", "uuid": "01D9AAAA",
                 "parttype": "ebd0a0a2-b9e5-4433-87c0-68b6b72699c7", "rm": False, "hotplug": False,
                 "mountpoints": [None]},
                {"name": "nvme0n1p4", "path": "/dev/nvme0n1p4", "type": "part", "fstype": "ntfs",
                 "size": 700 * 1024**2, "label": None, "uuid": "01D9BBBB",
                 "parttype": "de94bba4-06d1-4d40-a16a-bfd50179d6ac", "rm": False, "hotplug": False,
                 "mountpoints": [None]},
                {"name": "nvme0n1p5", "path": "/dev/nvme0n1p5", "type": "part", "fstype": "ntfs",
                 "size": 150 * GIB, "label": "Data", "uuid": "01D9CCCC",
                 "parttype": "ebd0a0a2-b9e5-4433-87c0-68b6b72699c7", "rm": False, "hotplug": False,
                 "mountpoints": ["/run/media/u/Data"]},
                {"name": "nvme0n1p6", "path": "/dev/nvme0n1p6", "type": "part", "fstype": "btrfs",
                 "size": 60 * GIB, "label": "fedora", "uuid": "f-f-f",
                 "parttype": "0fc63daf-8483-4772-8e79-3d69d8477de4", "rm": False, "hotplug": False,
                 "mountpoints": ["/sysroot", "/var"]},
            ],
        },
        {
            "name": "sda", "path": "/dev/sda", "type": "disk", "fstype": None, "size": 64 * GIB,
            "label": None, "uuid": None, "parttype": None, "rm": True, "hotplug": True,
            "mountpoints": [None],
            "children": [
                {"name": "sda1", "path": "/dev/sda1", "type": "part", "fstype": "BitLocker",
                 "size": 64 * GIB, "label": None, "uuid": None, "parttype": "0x7",
                 "rm": True, "hotplug": True, "mountpoints": [None]},
            ],
        },
        {
            "name": "sdb", "path": "/dev/sdb", "type": "disk", "fstype": "ntfs", "size": "1000204886016",
            "label": "Archive", "uuid": "5555", "parttype": None, "rm": "0", "hotplug": "1",
            "mountpoints": [None],
        },
    ]
}


def test_parse_lsblk_finds_only_windows_volumes():
    found = volumes.parse_lsblk(json.dumps(LSBLK))
    assert [v.path for v in found] == [
        "/dev/nvme0n1p3", "/dev/nvme0n1p4", "/dev/nvme0n1p5", "/dev/sda1", "/dev/sdb",
    ]


def test_volume_attributes():
    found = {v.path: v for v in volumes.parse_lsblk(LSBLK)}
    os_vol = found["/dev/nvme0n1p3"]
    assert os_vol.label == "OS" and os_vol.size == 300 * GIB
    assert os_vol.disk == "/dev/nvme0n1"
    assert not os_vol.removable and not os_vol.bitlocker and not os_vol.recovery
    assert os_vol.mountpoint is None
    assert found["/dev/nvme0n1p4"].recovery
    assert found["/dev/nvme0n1p5"].mountpoint == "/run/media/u/Data"
    assert found["/dev/sda1"].bitlocker and found["/dev/sda1"].removable
    # lsblk from older util-linux prints numbers/bools as strings
    archive = found["/dev/sdb"]
    assert archive.size == 1000204886016 and archive.removable and archive.disk == "/dev/sdb"


def test_usable_for_migration_excludes_recovery_and_bitlocker():
    found = volumes.parse_lsblk(LSBLK)
    assert [v.path for v in volumes.migratable(found)] == [
        "/dev/nvme0n1p3", "/dev/nvme0n1p5", "/dev/sdb",
    ]


def test_parse_udisks_mount_output():
    assert volumes.parse_udisksctl_mount("Mounted /dev/nvme0n1p3 at /run/media/ivan/OS\n") == "/run/media/ivan/OS"
    assert volumes.parse_udisksctl_mount("Mounted /dev/sdb at /run/media/ivan/My Disk.") == "/run/media/ivan/My Disk"
    assert volumes.parse_udisksctl_mount("garbage") is None


def test_udisksctl_mount_command_is_read_only():
    cmd = volumes.udisksctl_mount_cmd(Volume(path="/dev/sdb", fstype="ntfs", size=1))
    assert cmd[:2] == ["udisksctl", "mount"]
    assert "-b" in cmd and "/dev/sdb" in cmd
    assert cmd[cmd.index("-o") + 1] == "ro"
    assert "--no-user-interaction" in cmd


def test_human_size():
    assert volumes.human_size(0) == "0 Б"
    assert volumes.human_size(1023) == "1023 Б"
    assert volumes.human_size(1536) == "1,5 КБ"
    assert volumes.human_size(300 * GIB) == "300 ГБ"
    assert volumes.human_size(int(2.25 * 1024**4)) == "2,2 ТБ"
