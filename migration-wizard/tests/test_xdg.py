from pathlib import Path

from lucent_migrate import xdg

USER_DIRS = """# This file is written by xdg-user-dirs-update
XDG_DESKTOP_DIR="$HOME/Рабочий стол"
XDG_DOWNLOAD_DIR="$HOME/Загрузки"
XDG_DOCUMENTS_DIR="$HOME/Документы"
XDG_MUSIC_DIR="/data/music"
XDG_PICTURES_DIR="$HOME/Изображения"
XDG_VIDEOS_DIR="$HOME/"
XDG_TEMPLATES_DIR="$HOME/Шаблоны"
garbage line
"""


def test_parse_user_dirs():
    home = Path("/home/ivan")
    dirs = xdg.parse_user_dirs(USER_DIRS, home)
    assert dirs["DESKTOP"] == home / "Рабочий стол"
    assert dirs["DOCUMENTS"] == home / "Документы"
    assert dirs["MUSIC"] == Path("/data/music")
    # "$HOME/" means the directory is disabled -> not returned
    assert "VIDEOS" not in dirs


def test_target_dirs_fall_back_to_english_defaults(tmp_path):
    dirs = xdg.target_dirs(tmp_path, config_home=tmp_path / ".config")
    assert dirs["DOCUMENTS"] == tmp_path / "Documents"
    assert dirs["DOWNLOAD"] == tmp_path / "Downloads"
    assert set(dirs) >= {"DESKTOP", "DOCUMENTS", "DOWNLOAD", "MUSIC", "PICTURES", "VIDEOS"}


def test_target_dirs_reads_config(tmp_path):
    cfg = tmp_path / ".config"
    cfg.mkdir()
    (cfg / "user-dirs.dirs").write_text(USER_DIRS)
    dirs = xdg.target_dirs(tmp_path, config_home=cfg)
    assert dirs["DOCUMENTS"] == tmp_path / "Документы"
    assert dirs["VIDEOS"] == tmp_path / "Videos"
