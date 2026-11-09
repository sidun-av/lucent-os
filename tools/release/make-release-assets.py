#!/usr/bin/python3
"""Turn the iso workflow's ISOs into release assets.

Usage: make-release-assets.py VERSION ISO_DIR OUT_DIR

ISO_DIR holds lucent-os-<arch>.iso files (with their .sha256), in any
subfolder, as actions/download-artifact leaves them. Each ISO is checked
against its .sha256, then split into lucent-os-<VERSION>-<arch>.iso.001,
.002, ... under GitHub's 2 GiB limit per release asset, in one pass that
also hashes every part. OUT_DIR gets the parts, SHA256SUMS (the parts and
the whole ISOs) and the join scripts. A source ISO is deleted once its parts
are written, so the disk holds each ISO only once.

LUCENT_PART_BYTES overrides the part size (tests).
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import sys
from pathlib import Path

# "Each file included in a release must be under 2 GiB" (GitHub docs,
# About releases). 1900 MiB leaves room and keeps the parts few.
PART_BYTES = 1900 * 1024 * 1024
CHUNK = 8 << 20
HERE = Path(__file__).resolve().parent
SCRIPTS = ("join-lucent-iso.sh", "join-lucent-iso.ps1", "join-lucent-iso.cmd")
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.]+)?$")
ISO_RE = re.compile(r"^lucent-os-([a-z0-9_]+)\.iso$")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(CHUNK):
            h.update(chunk)
    return h.hexdigest()


def split(iso: Path, out: Path, base: str, part_bytes: int) -> tuple[str, list[tuple[str, str]]]:
    """Write base.001, base.002, ...; return (whole hash, [(part name, hash)])."""
    whole = hashlib.sha256()
    parts: list[tuple[str, str]] = []
    with open(iso, "rb") as f:
        n = 0
        while True:
            first = f.read(min(CHUNK, part_bytes))
            if not first:
                break
            n += 1
            name = f"{base}.{n:03d}"
            h = hashlib.sha256()
            left = part_bytes
            with open(out / name, "wb") as p:
                chunk = first
                while chunk:
                    whole.update(chunk)
                    h.update(chunk)
                    p.write(chunk)
                    left -= len(chunk)
                    if left <= 0:
                        break
                    chunk = f.read(min(CHUNK, left))
            parts.append((name, h.hexdigest()))
    if n > 999:
        raise SystemExit(f"{iso.name}: more than 999 parts")
    return whole.hexdigest(), parts


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    version, src, out = argv[0], Path(argv[1]), Path(argv[2])
    if not VERSION_RE.match(version):
        print(f"not a version (X.Y.Z or X.Y.Z-suffix): {version!r}", file=sys.stderr)
        return 2
    part_bytes = int(os.environ.get("LUCENT_PART_BYTES") or PART_BYTES)
    isos = sorted((p for p in src.rglob("*.iso") if ISO_RE.match(p.name)), key=lambda p: p.name)
    if not isos:
        print(f"no lucent-os-<arch>.iso under {src}", file=sys.stderr)
        return 1
    out.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    for iso in isos:
        arch = ISO_RE.match(iso.name).group(1)
        sidecar = iso.with_name(iso.name + ".sha256")
        expected = sidecar.read_text().split()[0] if sidecar.exists() else None
        base = f"lucent-os-{version}-{arch}.iso"
        whole, parts = split(iso, out, base, part_bytes)
        if expected and whole != expected:
            for name, _ in parts:
                (out / name).unlink()
            print(f"{iso.name}: content is {whole}, but {sidecar.name} says {expected}", file=sys.stderr)
            return 1
        iso.unlink()
        lines += [f"{h}  {name}" for name, h in parts]
        lines.append(f"{whole}  {base}")
        print(f"{base}: {len(parts)} parts, sha256 {whole}")

    (out / "SHA256SUMS").write_text("\n".join(lines) + "\n")
    for s in SCRIPTS:
        shutil.copyfile(HERE / s, out / s)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
