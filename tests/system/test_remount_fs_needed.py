"""systemd-remount-fs on a composefs root (system_files/usr/libexec/lucent/remount-fs-needed).

On composefs, / is a read-only overlay; remounting it with the btrfs options
of an installer-written /etc/fstab line fails ("overlay: No changes allowed
in reconfigure") and leaves a failed unit on every boot. The ExecCondition
skips systemd-remount-fs exactly then, and lets it run in every other case.
"""
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "system_files/usr/libexec/lucent/remount-fs-needed"

ANACONDA_BTRFS = """\
#
# /etc/fstab
# Created by anaconda on Mon Nov  9 16:58:01 2026
#
UUID=e4fa4e2e-f901-4a2e-99b9-c445062f7f4f /                       btrfs   subvol=root,compress=zstd:1,ro 0 0
UUID=7e1cda14-0988-4f3a-b6a3-4b9d81a67f09 /boot                   ext4    defaults        1 2
UUID=B82D-857E          /boot/efi               vfat    umask=0077,shortname=winnt 0 2
UUID=e4fa4e2e-f901-4a2e-99b9-c445062f7f4f /home                   btrfs   subvol=home,compress=zstd:1 0 0
UUID=e4fa4e2e-f901-4a2e-99b9-c445062f7f4f /var                    btrfs   subvol=var,compress=zstd:1 0 0
"""


def needed(tmp_path, fstab, root_fstype):
    f = tmp_path / "fstab"
    f.write_text(fstab)
    env = dict(os.environ, LUCENT_ROOT_FSTYPE=root_fstype)
    return subprocess.run(["bash", str(SCRIPT), str(f)], env=env, capture_output=True, text=True).returncode


def test_composefs_root_listed_in_fstab_is_skipped(tmp_path):
    assert needed(tmp_path, ANACONDA_BTRFS, "overlay") == 1


def test_root_not_listed_runs(tmp_path):
    without_root = "".join(ln + "\n" for ln in ANACONDA_BTRFS.splitlines() if " /  " not in ln)
    assert needed(tmp_path, without_root, "overlay") == 0


def test_commented_root_line_does_not_count(tmp_path):
    commented = ANACONDA_BTRFS.replace("UUID=e4fa4e2e-f901-4a2e-99b9-c445062f7f4f /  ",
                                       "#UUID=e4fa4e2e-f901-4a2e-99b9-c445062f7f4f /  ")
    assert needed(tmp_path, commented, "overlay") == 0


def test_without_composefs_it_always_runs(tmp_path):
    assert needed(tmp_path, ANACONDA_BTRFS, "btrfs") == 0
    assert needed(tmp_path, ANACONDA_BTRFS, "xfs") == 0


def test_api_file_system_lines_keep_it_running(tmp_path):
    # systemd-remount-fs also applies fstab options of /proc, /sys, /dev/shm...
    extra = ANACONDA_BTRFS + "tmpfs /dev/shm tmpfs defaults,size=2G 0 0\n"
    assert needed(tmp_path, extra, "overlay") == 0
    extra = ANACONDA_BTRFS + "proc /proc proc hidepid=2 0 0\n"
    assert needed(tmp_path, extra, "overlay") == 0


def test_tab_separated_and_missing_fstab(tmp_path):
    assert needed(tmp_path, "LABEL=root\t/\tbtrfs\tsubvol=root\t0 0\n", "overlay") == 1
    env = dict(os.environ, LUCENT_ROOT_FSTYPE="overlay")
    r = subprocess.run(["bash", str(SCRIPT), str(tmp_path / "nope")], env=env)
    assert r.returncode == 0   # nothing to decide on: let systemd do what it does
