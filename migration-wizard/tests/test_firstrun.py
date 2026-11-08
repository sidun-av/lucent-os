from lucent_migrate import firstrun
from lucent_migrate.volumes import Volume


def test_autostart_only_once_and_only_with_windows_volumes(tmp_path):
    vols = [Volume(path="/dev/sda1", fstype="ntfs", size=10**11, uuid="X")]
    assert firstrun.should_autostart(tmp_path, vols, uid=1000)
    assert not firstrun.should_autostart(tmp_path, [], uid=1000)
    firstrun.mark_done(tmp_path)
    assert (tmp_path / "lucent" / "migration-done").exists()
    assert not firstrun.should_autostart(tmp_path, vols, uid=1000)


def test_bitlocker_only_still_autostarts_to_explain(tmp_path):
    vols = [Volume(path="/dev/sda1", fstype="BitLocker", size=10**11)]
    assert firstrun.should_autostart(tmp_path, vols, uid=1000)


def test_never_autostarts_for_system_accounts(tmp_path):
    # Fedora 45's first-boot wizard (plasma-setup) runs a full Plasma session
    # as the system user "plasma-setup" (uid < 1000), and /etc/xdg/autostart
    # applies there too.
    vols = [Volume(path="/dev/sda1", fstype="ntfs", size=10**11, uuid="X")]
    assert not firstrun.should_autostart(tmp_path, vols, uid=969)
    assert firstrun.should_autostart(tmp_path, vols, uid=1000)
