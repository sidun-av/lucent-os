"""Plan and execute copying a Windows folder tree into the Linux home.

`plan()` is a pure walk that decides what to do with each file; `execute()`
performs it, never aborting on a single bad file (errors are collected and
shown to the user at the end).
"""

from __future__ import annotations

import enum
import os
import shutil
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

# Explorer metadata that is meaningless on Linux.
JUNK = {"desktop.ini", "thumbs.db", "ehthumbs.db", "$recycle.bin", "system volume information"}


class Policy(enum.Enum):
    SKIP = "skip"        # keep what is already there
    RENAME = "rename"    # keep both: "file (2).ext", like Explorer does
    NEWER = "newer"      # replace only if the Windows copy is newer


class Action(enum.Enum):
    COPY = "copy"
    SKIP = "skip"
    RENAME = "rename"
    OVERWRITE = "overwrite"


@dataclass(frozen=True)
class Stats:
    files: int
    bytes: int


@dataclass(frozen=True)
class CopyOp:
    src: Path
    dst: Path
    action: Action
    size: int


@dataclass
class Result:
    copied: int = 0
    skipped: int = 0
    errors: list[tuple[Path, str]] = field(default_factory=list)
    cancelled: bool = False


def _walk(root: Path):
    """Yield (path, stat) of regular files; never follows symlinks/junctions."""
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            entries = sorted(os.scandir(current), key=lambda e: e.name)
        except OSError:
            continue
        for entry in entries:
            if entry.name.lower() in JUNK:
                continue
            try:
                if entry.is_symlink():
                    continue
                if entry.is_dir(follow_symlinks=False):
                    stack.append(Path(entry.path))
                elif entry.is_file(follow_symlinks=False):
                    yield Path(entry.path), entry.stat(follow_symlinks=False)
            except OSError:
                continue


def scan(root: Path) -> Stats:
    files = total = 0
    for _, st in _walk(root):
        files += 1
        total += st.st_size
    return Stats(files, total)


def unique_name(path: Path) -> Path:
    if not path.exists():
        return path
    name = path.name
    stem, dot, ext = name.partition(".")
    if not stem:  # dotfile like ".bashrc"
        stem, dot, ext = name, "", ""
    n = 2
    while True:
        candidate = path.with_name(f"{stem} ({n}){dot}{ext}")
        if not candidate.exists():
            return candidate
        n += 1


def plan(src: Path, dst: Path, policy: Policy) -> list[CopyOp]:
    ops: list[CopyOp] = []
    for path, st in _walk(src):
        target = dst / path.relative_to(src)
        if not target.exists():
            ops.append(CopyOp(path, target, Action.COPY, st.st_size))
        elif policy is Policy.RENAME:
            ops.append(CopyOp(path, unique_name(target), Action.RENAME, st.st_size))
        elif policy is Policy.NEWER and st.st_mtime > target.stat().st_mtime + 2:
            # +2 s: FAT/NTFS timestamp rounding must not count as "newer"
            ops.append(CopyOp(path, target, Action.OVERWRITE, st.st_size))
        else:
            ops.append(CopyOp(path, target, Action.SKIP, st.st_size))
    return ops


Progress = Callable[[int, int, CopyOp], None]


def execute(
    ops: list[CopyOp],
    progress: Progress | None = None,
    cancelled: Callable[[], bool] = lambda: False,
) -> Result:
    result = Result()
    total = sum(op.size for op in ops)
    done = 0
    for op in ops:
        if cancelled():
            result.cancelled = True
            break
        if op.action is Action.SKIP:
            result.skipped += 1
        else:
            try:
                op.dst.parent.mkdir(parents=True, exist_ok=True)
                tmp = op.dst.with_name(f".{op.dst.name}.lucent-part")
                shutil.copy2(op.src, tmp)
                os.replace(tmp, op.dst)
                result.copied += 1
            except OSError as exc:
                result.errors.append((op.src, str(exc)))
                try:
                    tmp.unlink(missing_ok=True)
                except (OSError, UnboundLocalError):
                    pass
        done += op.size
        if progress:
            progress(done, total, op)
    return result
