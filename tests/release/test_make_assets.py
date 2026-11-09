"""tools/release/make-release-assets.py: ISOs -> release assets (parts under
GitHub's 2 GiB limit, SHA256SUMS, the join scripts), and back with the
join script."""
from __future__ import annotations

import hashlib
import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "tools" / "release" / "make-release-assets.py"


def load_module():
    spec = importlib.util.spec_from_file_location("make_release_assets", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def make_isos(d: Path) -> dict[str, bytes]:
    d.mkdir()
    isos = {"amd64": os.urandom(2500), "arm64": os.urandom(4000)}
    for arch, data in isos.items():
        # As the iso workflow's artifacts download: one folder per artifact.
        (d / f"lucent-os-{arch}-iso").mkdir()
        (d / f"lucent-os-{arch}-iso" / f"lucent-os-{arch}.iso").write_bytes(data)
        (d / f"lucent-os-{arch}-iso" / f"lucent-os-{arch}.iso.sha256").write_text(f"{sha(data)}  lucent-os-{arch}.iso\n")
    return isos


def run(src: Path, out: Path, *extra, part_bytes="1000"):
    env = dict(os.environ, LUCENT_PART_BYTES=part_bytes) if part_bytes else dict(os.environ)
    return subprocess.run([sys.executable, str(SCRIPT), "0.9.0", str(src), str(out), *extra],
                          capture_output=True, text=True, env=env)


def test_default_part_size_is_safely_under_githubs_limit():
    mod = load_module()
    assert mod.PART_BYTES < 2 * 1024**3
    assert mod.PART_BYTES >= 1024**3  # and not needlessly many parts


def test_parts_sums_and_scripts(tmp_path):
    isos = make_isos(tmp_path / "in")
    out = tmp_path / "out"
    p = run(tmp_path / "in", out)
    assert p.returncode == 0, p.stderr
    names = sorted(f.name for f in out.iterdir())
    assert names == sorted([
        "lucent-os-0.9.0-amd64.iso.001", "lucent-os-0.9.0-amd64.iso.002", "lucent-os-0.9.0-amd64.iso.003",
        "lucent-os-0.9.0-arm64.iso.001", "lucent-os-0.9.0-arm64.iso.002", "lucent-os-0.9.0-arm64.iso.003",
        "lucent-os-0.9.0-arm64.iso.004",
        "SHA256SUMS", "join-lucent-iso.sh", "join-lucent-iso.ps1", "join-lucent-iso.cmd"])
    for arch, data in isos.items():
        parts = sorted(out.glob(f"lucent-os-0.9.0-{arch}.iso.0*"))
        assert b"".join(p.read_bytes() for p in parts) == data
        assert all(p.stat().st_size <= 1000 for p in parts)
    sums = (out / "SHA256SUMS").read_text().splitlines()
    want = {f"{sha(isos['amd64'])}  lucent-os-0.9.0-amd64.iso", f"{sha(isos['arm64'])}  lucent-os-0.9.0-arm64.iso"}
    assert want <= set(sums)
    for f in out.glob("*.iso.0*"):
        assert f"{sha(f.read_bytes())}  {f.name}" in sums
    assert len(sums) == 2 + 7
    # The source ISOs are consumed (they would double the disk space).
    assert not list((tmp_path / "in").rglob("*.iso"))


def test_a_source_iso_that_does_not_match_its_sha256_file_fails(tmp_path):
    make_isos(tmp_path / "in")
    f = tmp_path / "in" / "lucent-os-arm64-iso" / "lucent-os-arm64.iso"
    f.write_bytes(f.read_bytes() + b"!")
    p = run(tmp_path / "in", tmp_path / "out")
    assert p.returncode != 0
    assert "lucent-os-arm64.iso" in p.stderr


def test_round_trip_with_the_join_script(tmp_path):
    if not shutil.which("sh") or sys.platform == "win32":
        pytest.skip("needs sh")
    isos = make_isos(tmp_path / "in")
    out = tmp_path / "out"
    assert run(tmp_path / "in", out).returncode == 0
    j = subprocess.run(["sh", str(out / "join-lucent-iso.sh")], capture_output=True, text=True,
                       env=dict(os.environ, LUCENT_NO_PAUSE="1"))
    assert j.returncode == 0, j.stdout + j.stderr
    for arch, data in isos.items():
        assert (out / f"lucent-os-0.9.0-{arch}.iso").read_bytes() == data


def test_version_must_look_like_a_version(tmp_path):
    make_isos(tmp_path / "in")
    p = subprocess.run([sys.executable, str(SCRIPT), "v0.9 beta", str(tmp_path / "in"), str(tmp_path / "out")],
                       capture_output=True, text=True)
    assert p.returncode != 0 and "version" in p.stderr.lower()
