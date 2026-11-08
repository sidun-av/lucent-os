from pathlib import Path

from lucent_migrate import windows


def test_is_windows_system(windows_root, tmp_path):
    assert windows.is_windows_system(windows_root)
    assert not windows.is_windows_system(tmp_path / "nothing")


def test_find_users_skips_system_profiles(windows_root):
    users = windows.find_users(windows_root)
    assert [u.name for u in users] == ["Ivan", "maria"]


def test_find_users_on_data_volume_without_users_dir(tmp_path):
    assert windows.find_users(tmp_path) == []


def test_known_folders_mapped(windows_root):
    ivan = windows.find_users(windows_root)[0]
    assert set(ivan.folders) == {"DOCUMENTS", "PICTURES", "DESKTOP", "DOWNLOAD", "MUSIC", "VIDEOS"}
    assert ivan.folders["DOCUMENTS"] == [windows_root / "Users" / "Ivan" / "Documents"]


def test_onedrive_redirected_folders_are_included(windows_root):
    maria = windows.find_users(windows_root)[1]
    assert maria.folders["DOCUMENTS"] == [windows_root / "Users" / "maria" / "OneDrive" / "Documents"]
    assert maria.folders["DESKTOP"] == [windows_root / "Users" / "maria" / "OneDrive" / "Desktop"]
    assert maria.folders["PICTURES"] == [windows_root / "Users" / "maria" / "Pictures"]
    assert "MUSIC" not in maria.folders


def test_case_insensitive_folder_lookup(tmp_path):
    home = tmp_path / "Users" / "Petr"
    (home / "documents").mkdir(parents=True)
    (home / "ntuser.dat").write_bytes(b"")
    (user,) = windows.find_users(tmp_path)
    assert user.folders["DOCUMENTS"] == [home / "documents"]


def test_child_ci(tmp_path: Path):
    (tmp_path / "AppData").mkdir()
    assert windows.child_ci(tmp_path, "appdata") == tmp_path / "AppData"
    assert windows.child_ci(tmp_path, "nope") is None
    assert windows.child_ci(tmp_path / "missing", "x") is None
