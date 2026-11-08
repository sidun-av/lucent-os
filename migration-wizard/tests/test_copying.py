import os
from pathlib import Path

import pytest

from lucent_migrate import copying
from lucent_migrate.copying import Action, Policy

from conftest import write


def test_scan_skips_junk_and_symlinks(windows_root):
    docs = windows_root / "Users" / "Ivan" / "Documents"
    stats = copying.scan(docs)
    # Отчёт.docx (100) + Проекты/план.xlsx (50); desktop.ini and the
    # "Моя музыка" junction are ignored
    assert stats.files == 2
    assert stats.bytes == 150


def test_scan_missing_dir_is_empty(tmp_path):
    assert copying.scan(tmp_path / "nope") == copying.Stats(0, 0)


def test_unique_name_windows_style(tmp_path):
    write(tmp_path / "a.txt")
    write(tmp_path / "a (2).txt")
    assert copying.unique_name(tmp_path / "a.txt") == tmp_path / "a (3).txt"
    assert copying.unique_name(tmp_path / "b.txt") == tmp_path / "b.txt"
    write(tmp_path / "archive.tar.gz")
    assert copying.unique_name(tmp_path / "archive.tar.gz") == tmp_path / "archive (2).tar.gz"


def make_conflict(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    write(src / "same.txt", b"new", mtime=2_000_000_000)
    write(dst / "same.txt", b"old", mtime=1_000_000_000)
    write(src / "older.txt", b"src-old", mtime=1_000_000_000)
    write(dst / "older.txt", b"dst-new", mtime=2_000_000_000)
    write(src / "sub" / "fresh.txt", b"fresh")
    write(src / "Thumbs.db", b"junk")
    return src, dst


@pytest.mark.parametrize(
    "policy, expected",
    [
        (Policy.SKIP, {"same.txt": Action.SKIP, "older.txt": Action.SKIP}),
        (Policy.RENAME, {"same.txt": Action.RENAME, "older.txt": Action.RENAME}),
        (Policy.NEWER, {"same.txt": Action.OVERWRITE, "older.txt": Action.SKIP}),
    ],
)
def test_plan_conflicts(tmp_path, policy, expected):
    src, dst = make_conflict(tmp_path)
    plan = {op.src.relative_to(src).as_posix(): op for op in copying.plan(src, dst, policy)}
    assert set(plan) == {"same.txt", "older.txt", "sub/fresh.txt"}
    assert plan["sub/fresh.txt"].action is Action.COPY
    for name, action in expected.items():
        assert plan[name].action is action
    if policy is Policy.RENAME:
        assert plan["same.txt"].dst == dst / "same (2).txt"


def test_execute_rename_keeps_both_and_reports_progress(tmp_path):
    src, dst = make_conflict(tmp_path)
    ops = copying.plan(src, dst, Policy.RENAME)
    seen = []
    result = copying.execute(ops, progress=lambda done, total, op: seen.append((done, total)))
    assert (dst / "same.txt").read_bytes() == b"old"
    assert (dst / "same (2).txt").read_bytes() == b"new"
    assert (dst / "sub" / "fresh.txt").read_bytes() == b"fresh"
    assert result.copied == 3 and result.skipped == 0 and result.errors == []
    assert seen[-1][0] == seen[-1][1] == sum(op.size for op in ops)


def test_execute_newer_overwrites_only_newer_and_preserves_mtime(tmp_path):
    src, dst = make_conflict(tmp_path)
    result = copying.execute(copying.plan(src, dst, Policy.NEWER))
    assert (dst / "same.txt").read_bytes() == b"new"
    assert (dst / "older.txt").read_bytes() == b"dst-new"
    assert int(os.path.getmtime(dst / "same.txt")) == 2_000_000_000
    assert result.copied == 2 and result.skipped == 1


def test_execute_collects_errors_and_continues(tmp_path):
    src, dst = make_conflict(tmp_path)
    ops = copying.plan(src, dst, Policy.SKIP)
    (src / "sub" / "fresh.txt").unlink()  # vanished between plan and copy
    write(src / "zzz.txt", b"z")
    ops += copying.plan(src, dst, Policy.SKIP)[-1:]
    result = copying.execute(ops)
    assert len(result.errors) == 1 and "fresh.txt" in str(result.errors[0][0])
    assert (dst / "zzz.txt").exists()


def test_execute_cancel(tmp_path):
    src, dst = make_conflict(tmp_path)
    result = copying.execute(copying.plan(src, dst, Policy.RENAME), cancelled=lambda: True)
    assert result.cancelled and result.copied == 0
    assert not (dst / "sub").exists()


def test_plan_never_follows_symlinks(windows_root, tmp_path):
    ops = copying.plan(windows_root / "Users" / "Ivan" / "Documents", tmp_path / "out", Policy.SKIP)
    names = {Path(op.src).name for op in ops}
    assert names == {"Отчёт.docx", "план.xlsx"}
