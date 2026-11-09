"""iso/bundle-members.py: the order of the files in the offline app bundle."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "iso" / "bundle-members.py"


def touch(root: Path, rel: str, data: bytes = b"x"):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)


def members(root: Path) -> list[str]:
    out = subprocess.run([sys.executable, str(SCRIPT), str(root)], capture_output=True, check=True).stdout
    assert out.endswith(b"\0")
    return out[:-1].decode().split("\0")


def test_same_file_of_two_runtime_versions_is_side_by_side(tmp_path):
    for ver, commit in (("6.10", "aaa"), ("6.11", "bbb")):
        for f in ("files/lib/libQt6Core.so.6", "files/lib/libQt6Gui.so.6", "metadata"):
            touch(tmp_path, f"runtime/org.kde.Platform/x86_64/{ver}/{commit}/{f}")
    touch(tmp_path, "app/org.kde.krita/x86_64/stable/ccc/files/bin/krita")
    files = [m for m in members(tmp_path) if not (tmp_path / m).is_dir()]
    core = [m for m in files if m.endswith("libQt6Core.so.6")]
    i = files.index(core[0])
    assert files[i + 1] == core[1]
    assert "6.10" in core[0] and "6.11" in core[1]


def test_directories_first_then_deployed_files_then_the_rest(tmp_path):
    touch(tmp_path, "repo/objects/ab/cdef.file")
    touch(tmp_path, "repo/config")
    touch(tmp_path, "app/org.gimp.GIMP/x86_64/stable/ddd/files/bin/gimp")
    touch(tmp_path, "exports/share/applications/org.gimp.GIMP.desktop")
    (tmp_path / "app/org.gimp.GIMP/current").symlink_to("x86_64/stable")
    order = members(tmp_path)
    kinds = ["dir" if (tmp_path / m).is_dir() and not (tmp_path / m).is_symlink() else "file" for m in order]
    assert kinds == sorted(kinds)  # every "dir" before every "file"
    files = [m for m, k in zip(order, kinds) if k == "file"]
    assert files[0] == "./app/org.gimp.GIMP/x86_64/stable/ddd/files/bin/gimp"
    assert set(files[1:]) == {"./app/org.gimp.GIMP/current", "./exports/share/applications/org.gimp.GIMP.desktop",
                              "./repo/config", "./repo/objects/ab/cdef.file"}


def test_every_entry_once_with_odd_names(tmp_path):
    touch(tmp_path, "app/a b/x86_64/stable/c/files/with space.txt")
    touch(tmp_path, "runtime/r/aarch64/1/c/files/été")
    got = members(tmp_path)
    want = sorted("./" + p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*"))
    assert sorted(got) == want and len(got) == len(set(got))
