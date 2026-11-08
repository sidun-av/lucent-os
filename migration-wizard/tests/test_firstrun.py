from lucent_migrate import firstrun
from lucent_migrate.volumes import Volume


def test_autostart_only_once_and_only_with_windows_volumes(tmp_path):
    vols = [Volume(path="/dev/sda1", fstype="ntfs", size=10**11, uuid="X")]
    assert firstrun.should_autostart(tmp_path, vols)
    assert not firstrun.should_autostart(tmp_path, [])
    firstrun.mark_done(tmp_path)
    assert (tmp_path / "lucent" / "migration-done").exists()
    assert not firstrun.should_autostart(tmp_path, vols)


def test_bitlocker_only_still_autostarts_to_explain(tmp_path):
    vols = [Volume(path="/dev/sda1", fstype="BitLocker", size=10**11)]
    assert firstrun.should_autostart(tmp_path, vols)
