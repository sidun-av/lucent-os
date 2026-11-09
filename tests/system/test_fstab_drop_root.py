"""The installer's fstab fix (system_files/usr/libexec/lucent/fstab-drop-root,
run by iso/lucent-apps.ks): on a composefs system the line for / can never
be applied, so it is kept only as a comment, as bootc's own installs do
(they write no line for / at all)."""
import subprocess
from pathlib import Path

from test_remount_fs_needed import ANACONDA_BTRFS, SCRIPT as NEEDED

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "system_files/usr/libexec/lucent/fstab-drop-root"


def run(path):
    return subprocess.run(["bash", str(SCRIPT), str(path)], capture_output=True, text=True)


def test_root_line_becomes_a_comment_and_the_rest_stays(tmp_path):
    f = tmp_path / "fstab"
    f.write_text(ANACONDA_BTRFS)
    inode = f.stat().st_ino
    assert run(f).returncode == 0
    text = f.read_text()
    root_line = next(ln for ln in ANACONDA_BTRFS.splitlines() if " /  " in ln)
    assert "#" + root_line in text.splitlines()
    for ln in ANACONDA_BTRFS.splitlines():
        if ln != root_line:
            assert ln in text.splitlines()
    assert "composefs" in text            # says why
    assert f.stat().st_ino == inode       # rewritten in place: owner, mode, SELinux label kept


def test_systemd_remount_fs_then_has_nothing_to_skip(tmp_path):
    f = tmp_path / "fstab"
    f.write_text(ANACONDA_BTRFS)
    run(f)
    r = subprocess.run(["bash", str(NEEDED), str(f)], env={"LUCENT_ROOT_FSTYPE": "overlay", "PATH": "/usr/bin:/bin"})
    assert r.returncode == 0


def test_running_twice_changes_nothing_more(tmp_path):
    f = tmp_path / "fstab"
    f.write_text(ANACONDA_BTRFS)
    run(f)
    once = f.read_text()
    assert run(f).returncode == 0
    assert f.read_text() == once


def test_fstab_without_root_line_is_untouched(tmp_path):
    f = tmp_path / "fstab"
    text = "UUID=7e1c /boot ext4 defaults 1 2\n"
    f.write_text(text)
    assert run(f).returncode == 0
    assert f.read_text() == text


def test_missing_fstab_is_not_an_error(tmp_path):
    assert run(tmp_path / "nope").returncode == 0
