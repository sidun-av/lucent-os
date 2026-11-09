"""This PC's per-user defaults in /usr/libexec/lucent/design-defaults:
the "This PC" place at the top of Files' sidebar, and the view of thispc:/
(grouped by section, the grey detail line under each name)."""

import importlib.machinery
import importlib.util
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LIBEXEC = ROOT / "system_files/usr/libexec/lucent"


def load(name):
    """A /usr/libexec/lucent script as a module (no __pycache__ in the tree)."""
    sys.dont_write_bytecode = True
    loader = importlib.machinery.SourceFileLoader(name.replace("-", "_"), str(LIBEXEC / name))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


dd = load("design-defaults")
eject = load("thispc-eject")
dd.this_pc_available = lambda: True  # the worker is in the image


def test_no_this_pc_when_the_worker_did_not_build(monkeypatch):
    monkeypatch.setattr(dd, "this_pc_available", lambda: False)
    assert "thispc:/" not in dd.places_xbel()
    assert bookmarks(dd.places_xbel())[0].findtext("title") == "Desktop"


def bookmarks(xbel: str):
    return ET.fromstring(xbel).findall("bookmark")


def test_new_user_gets_this_pc_first():
    marks = bookmarks(dd.places_xbel())
    assert marks[0].get("href") == "thispc:/"
    assert marks[0].findtext("title") == "This PC"
    icon = marks[0].find("info/metadata/{http://www.freedesktop.org/standards/desktop-bookmarks}icon")
    assert icon.get("name") == "lucent-place-pc"
    assert [m.get("href").rsplit("/", 1)[-1] for m in marks[1:4]] == ["Desktop", "Documents", "Downloads"]


def test_existing_places_get_this_pc_once(tmp_path):
    # a sidebar from before This PC existed
    old = re.sub(r' <bookmark href="thispc:/">.*?</bookmark>\n', "", dd.places_xbel(), flags=re.S)
    assert "thispc:/" not in old
    new = dd.add_this_pc(old, "This PC")
    marks = bookmarks(new)
    assert marks[0].get("href") == "thispc:/"
    assert len([m for m in marks if m.get("href") == "thispc:/"]) == 1
    assert dd.add_this_pc(new, "This PC") == new  # idempotent
    assert len(marks) == len(bookmarks(old)) + 1


def test_this_pc_title_is_translated(monkeypatch):
    class Ru:
        def pgettext(self, ctx, text):
            return {"This PC": "Этот компьютер"}[text]
    monkeypatch.setattr(dd, "_thispc_catalog", lambda: Ru())
    assert dd.this_pc_title() == "Этот компьютер"
    assert bookmarks(dd.places_xbel())[0].findtext("title") == "Этот компьютер"


def test_remote_view_props_group_this_pc_by_section(tmp_path):
    dd.seed_thispc_view(tmp_path)
    props = (tmp_path / "dolphin/view_properties/remote/.directory").read_text()
    assert "[Dolphin]" in props
    for line in ("GroupedSorting=true", "GroupRole=type", "SortRole=text", "ViewMode=0", "PreviewsShown=false"):
        assert line in props.splitlines()
    assert "Icons_owner" in props  # the detail line under each name
    # a user's own choice is kept
    (tmp_path / "dolphin/view_properties/remote/.directory").write_text("[Dolphin]\nViewMode=1\n")
    dd.seed_thispc_view(tmp_path)
    assert (tmp_path / "dolphin/view_properties/remote/.directory").read_text() == "[Dolphin]\nViewMode=1\n"


# ---- the Eject action (thispc-eject)

def test_eject_accepts_only_this_pc_drives():
    no_mounts = lambda path: None
    assert eject.device_for("thispc:/drive-sdb1", no_mounts) == "/dev/sdb1"
    assert eject.device_for("thispc:///drive-sdb1/", no_mounts) == "/dev/sdb1"
    assert eject.device_for("thispc:/drive-mmcblk0p1", no_mounts) == "/dev/mmcblk0p1"
    for bad in ("thispc:/drive-../sda", "thispc:/drive-sdb1;rm", "file:///dev/sdb1", "thispc:/folder-Documents", "thispc:/drive-"):
        assert eject.device_for(bad, no_mounts) is None, bad


def test_eject_gets_the_mount_point_of_a_mounted_drive():
    # Dolphin hands a mounted drive's action its target, the mount point
    # (seen in the VM: ['/usr/libexec/lucent/thispc-eject', '/run/media/lucent/KINGSTON'])
    mounts = {"/run/media/lucent/KINGSTON": "/dev/sda", "/run/media/lucent/My Stick": "/dev/sdb1"}.get
    assert eject.device_for("/run/media/lucent/KINGSTON", mounts) == "/dev/sda"
    assert eject.device_for("file:///run/media/lucent/My%20Stick", mounts) == "/dev/sdb1"
    assert eject.device_for("/var/home/lucent", mounts) is None


def test_eject_powers_off_only_removable_disks():
    assert eject.removable('{"blockdevices": [{"rm": true, "hotplug": false, "tran": "usb"}]}')
    assert eject.removable('{"blockdevices": [{"rm": false, "hotplug": true, "tran": null}]}')
    assert eject.removable('{"blockdevices": [{"rm": false, "hotplug": false, "tran": "usb"}]}')
    assert not eject.removable('{"blockdevices": [{"rm": false, "hotplug": false, "tran": "nvme"}]}')
    assert not eject.removable("")


def test_eject_unmounts_every_mounted_partition():
    lsblk = """{"blockdevices": [{"path": "/dev/sdb", "mountpoints": [null], "children": [
        {"path": "/dev/sdb1", "mountpoints": ["/run/media/anna/KINGSTON"]},
        {"path": "/dev/sdb2", "mountpoints": [null]},
        {"path": "/dev/sdb3", "mountpoints": ["/run/media/anna/DATA"]}]}]}"""
    assert eject.mounted_partitions(lsblk) == ["/dev/sdb1", "/dev/sdb3"]
