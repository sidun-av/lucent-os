"""The join+verify scripts users run on release downloads
(tools/release/join-lucent-iso.{sh,ps1,cmd}).

The same scenarios run against every implementation available on this
machine: `sh` (macOS, Linux), `pwsh` (PowerShell 7, any OS) and, on Windows,
the built-in Windows PowerShell 5.1 and the double-click `.cmd` wrapper.
A fake `cosign` on PATH stands in for the real one.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
TOOLS = REPO / "tools" / "release"
WINDOWS = sys.platform == "win32"
PART_SIZE = 64 * 1024
IDENTITY_RE = r"^https://github\.com/sidun-av/lucent-os/\.github/workflows/release\.yml@refs/(tags/v.+|heads/main)$"


def _runners():
    out = []
    if not WINDOWS and shutil.which("sh"):
        out.append("sh")
    if shutil.which("pwsh"):
        out.append("pwsh")
    if WINDOWS:
        out += ["powershell", "cmd"]
    return out


RUNNERS = _runners()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_release(folder: Path, version="0.9.0", arch="amd64", nparts=3, seed=1, sums_lines=None):
    """Write the parts of a fake ISO into `folder`; return (iso name, data, sums lines)."""
    iso = f"lucent-os-{version}-{arch}.iso"
    data = (hashlib.sha512(f"{seed}".encode()).digest() * (PART_SIZE * nparts // 64 + 1))[: PART_SIZE * nparts - 1000]
    lines = [] if sums_lines is None else sums_lines
    for i in range(nparts):
        chunk = data[i * PART_SIZE:(i + 1) * PART_SIZE]
        name = f"{iso}.{i + 1:03d}"
        (folder / name).write_bytes(chunk)
        lines.append(f"{sha(chunk)}  {name}")
    lines.append(f"{sha(data)}  {iso}")
    return iso, data, lines


def write_sums(folder: Path, lines, crlf=False):
    nl = "\r\n" if crlf else "\n"
    (folder / "SHA256SUMS").write_bytes((nl.join(lines) + nl).encode())


@pytest.fixture
def rel(tmp_path):
    folder = tmp_path / "Downloads"
    folder.mkdir()
    for f in TOOLS.glob("join-lucent-iso.*"):
        shutil.copy(f, folder / f.name)
    return folder


def run(runner: str, folder: Path, *args, env_extra=None, path_dirs=(), script_dir=None):
    script_dir = script_dir or folder
    env = dict(os.environ)
    env["LUCENT_NO_PAUSE"] = "1"
    # A clean PATH so a real cosign on the test machine doesn't interfere.
    base = [p for p in env.get("PATH", "").split(os.pathsep)
            if p and not (Path(p) / ("cosign.exe" if WINDOWS else "cosign")).exists()]
    env["PATH"] = os.pathsep.join([str(d) for d in path_dirs] + base)
    env.update(env_extra or {})
    if runner == "sh":
        cmd = ["sh", str(script_dir / "join-lucent-iso.sh"), *args]
    elif runner == "pwsh":
        cmd = ["pwsh", "-NoProfile", "-NonInteractive", "-File", str(script_dir / "join-lucent-iso.ps1"), *args]
    elif runner == "powershell":
        cmd = ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
               "-File", str(script_dir / "join-lucent-iso.ps1"), *args]
    elif runner == "cmd":
        cmd = ["cmd", "/c", str(script_dir / "join-lucent-iso.cmd"), *args]
    else:
        raise AssertionError(runner)
    p = subprocess.run(cmd, cwd=folder, env=env, capture_output=True, text=True, timeout=300,
                       stdin=subprocess.DEVNULL)
    return p.returncode, p.stdout + p.stderr


def fake_cosign(tmp_path: Path, exit_code: int) -> Path:
    """A `cosign` stub that records its arguments and exits with exit_code."""
    d = tmp_path / f"bin-{exit_code}"
    d.mkdir()
    log = d / "args.txt"
    if WINDOWS:
        # A .ps1, not a .cmd: cmd.exe would parse the '|' in the identity regexp.
        (d / "cosign.ps1").write_text(f"$args -join \"`n\" | Set-Content -LiteralPath '{log}'\nexit {exit_code}\n")
    else:
        stub = d / "cosign"
        stub.write_text(f"#!/bin/sh\nprintf '%s\\n' \"$@\" > '{log}'\nexit {exit_code}\n")
        stub.chmod(0o755)
    return d


pytestmark = pytest.mark.skipif(not RUNNERS, reason="no shell to run the scripts with")


@pytest.mark.parametrize("runner", RUNNERS)
def test_joins_parts_into_a_verified_iso(runner, rel):
    iso, data, lines = make_release(rel)
    write_sums(rel, lines)
    code, out = run(runner, rel)
    assert code == 0, out
    assert (rel / iso).read_bytes() == data
    assert not list(rel.glob("*.partial"))
    assert iso in out and "ready" in out.lower()
    # The parts are left alone; the message says they can go.
    assert (rel / f"{iso}.001").exists()


@pytest.mark.parametrize("runner", RUNNERS)
def test_a_damaged_part_is_named_and_nothing_is_left_behind(runner, rel):
    iso, _, lines = make_release(rel)
    write_sums(rel, lines)
    p = rel / f"{iso}.002"
    b = bytearray(p.read_bytes())
    b[100] ^= 0xFF
    p.write_bytes(bytes(b))
    code, out = run(runner, rel)
    assert code != 0, out
    assert f"{iso}.002" in out
    assert "damaged" in out.lower()
    assert not (rel / iso).exists()
    assert not list(rel.glob("*.partial"))


@pytest.mark.parametrize("runner", RUNNERS)
def test_a_missing_part_is_named_before_any_work(runner, rel):
    iso, _, lines = make_release(rel)
    write_sums(rel, lines)
    (rel / f"{iso}.003").unlink()
    code, out = run(runner, rel)
    assert code != 0, out
    assert f"{iso}.003" in out
    assert "missing" in out.lower()
    assert not (rel / iso).exists()
    assert not list(rel.glob("*.partial"))


@pytest.mark.parametrize("runner", RUNNERS)
def test_a_truncated_part_counts_as_damaged(runner, rel):
    iso, _, lines = make_release(rel)
    write_sums(rel, lines)
    p = rel / f"{iso}.001"
    p.write_bytes(p.read_bytes()[:1000])
    code, out = run(runner, rel)
    assert code != 0, out
    assert f"{iso}.001" in out
    assert not (rel / iso).exists()


@pytest.mark.parametrize("runner", RUNNERS)
def test_without_sha256sums_it_says_what_to_download(runner, rel):
    make_release(rel)
    code, out = run(runner, rel)
    assert code != 0, out
    assert "SHA256SUMS is missing" in out


@pytest.mark.parametrize("runner", RUNNERS)
def test_without_parts_it_says_where_to_put_them(runner, rel):
    _, _, lines = make_release(rel)
    write_sums(rel, lines)
    for p in rel.glob("*.iso.0*"):
        p.unlink()
    code, out = run(runner, rel)
    assert code != 0, out
    assert ".001" in out and "folder" in out.lower()


@pytest.mark.parametrize("runner", RUNNERS)
def test_joins_each_iso_whose_parts_are_here_and_ignores_the_others(runner, rel):
    iso_a, data_a, lines = make_release(rel, arch="amd64", seed=1)
    iso_b, data_b, lines = make_release(rel, arch="arm64", seed=2, nparts=2, sums_lines=lines)
    # A third ISO listed in SHA256SUMS that the user did not download at all.
    lines.append(f"{'0' * 64}  lucent-os-0.9.0-riscv64.iso.001")
    lines.append(f"{'0' * 64}  lucent-os-0.9.0-riscv64.iso")
    write_sums(rel, lines)
    code, out = run(runner, rel)
    assert code == 0, out
    assert (rel / iso_a).read_bytes() == data_a
    assert (rel / iso_b).read_bytes() == data_b
    assert "riscv64" not in out


@pytest.mark.parametrize("runner", RUNNERS)
def test_running_again_only_checks_the_finished_iso(runner, rel):
    iso, data, lines = make_release(rel)
    write_sums(rel, lines)
    assert run(runner, rel)[0] == 0
    code, out = run(runner, rel)
    assert code == 0, out
    assert "already" in out.lower()
    assert (rel / iso).read_bytes() == data


@pytest.mark.parametrize("runner", RUNNERS)
def test_a_finished_iso_that_does_not_match_is_rebuilt_from_the_parts(runner, rel):
    iso, data, lines = make_release(rel)
    write_sums(rel, lines)
    (rel / iso).write_bytes(b"left over from an interrupted copy")
    code, out = run(runner, rel)
    assert code == 0, out
    assert (rel / iso).read_bytes() == data


@pytest.mark.parametrize("runner", RUNNERS)
def test_parts_that_match_but_join_to_the_wrong_iso_fail(runner, rel):
    iso, _, lines = make_release(rel)
    lines[-1] = f"{'a' * 64}  {iso}"
    write_sums(rel, lines)
    code, out = run(runner, rel)
    assert code != 0, out
    assert "does not match" in out.lower()
    assert not (rel / iso).exists()
    assert not list(rel.glob("*.partial"))


@pytest.mark.parametrize("runner", RUNNERS)
def test_windows_line_endings_in_sha256sums_are_fine(runner, rel):
    iso, data, lines = make_release(rel)
    write_sums(rel, lines, crlf=True)
    code, out = run(runner, rel)
    assert code == 0, out
    assert (rel / iso).read_bytes() == data


@pytest.mark.parametrize("runner", RUNNERS)
def test_folder_with_the_downloads_can_be_given(runner, rel, tmp_path):
    iso, data, lines = make_release(rel)
    write_sums(rel, lines)
    elsewhere = tmp_path / "scripts"
    elsewhere.mkdir()
    for f in rel.glob("join-lucent-iso.*"):
        shutil.move(str(f), elsewhere / f.name)
    code, out = run(runner, tmp_path, str(rel), script_dir=elsewhere)
    assert code == 0, out
    assert (rel / iso).read_bytes() == data


@pytest.mark.parametrize("runner", RUNNERS)
def test_not_enough_free_space_stops_before_writing(runner, rel):
    iso, _, lines = make_release(rel)
    write_sums(rel, lines)
    code, out = run(runner, rel, env_extra={"LUCENT_TEST_FREE_BYTES": "1000"})
    assert code != 0, out
    assert "not enough free space" in out.lower()
    assert not (rel / iso).exists()
    assert not list(rel.glob("*.partial"))


@pytest.mark.parametrize("runner", RUNNERS)
def test_signature_is_skipped_with_a_note_when_cosign_is_absent(runner, rel):
    iso, _, lines = make_release(rel)
    write_sums(rel, lines)
    (rel / "SHA256SUMS.sigstore.json").write_text("{}")
    code, out = run(runner, rel)
    assert code == 0, out
    assert "cosign" in out.lower() and "signature was not checked" in out.lower()


@pytest.mark.parametrize("runner", RUNNERS)
def test_signature_is_checked_with_cosign_when_present(runner, rel, tmp_path):
    iso, data, lines = make_release(rel)
    write_sums(rel, lines)
    (rel / "SHA256SUMS.sigstore.json").write_text("{}")
    ok = fake_cosign(tmp_path, 0)
    code, out = run(runner, rel, path_dirs=[ok])
    assert code == 0, out
    assert "signature verified" in out.lower()
    args = (ok / "args.txt").read_text()
    for want in ("verify-blob", "--bundle", "SHA256SUMS.sigstore.json",
                 "--certificate-oidc-issuer", "https://token.actions.githubusercontent.com",
                 "--certificate-identity-regexp", "SHA256SUMS"):
        assert want in args, args
    assert "lucent-os" in args and "release" in args
    assert (rel / iso).read_bytes() == data


@pytest.mark.parametrize("runner", RUNNERS)
def test_a_bad_signature_stops_everything(runner, rel, tmp_path):
    iso, _, lines = make_release(rel)
    write_sums(rel, lines)
    (rel / "SHA256SUMS.sigstore.json").write_text("{}")
    bad = fake_cosign(tmp_path, 1)
    code, out = run(runner, rel, path_dirs=[bad])
    assert code != 0, out
    assert "signature check failed" in out.lower()
    assert not (rel / iso).exists()


def test_the_scripts_expect_the_same_signer():
    """All three scripts and the release workflow agree on who signs."""
    sh = (TOOLS / "join-lucent-iso.sh").read_text()
    ps = (TOOLS / "join-lucent-iso.ps1").read_text()
    wf = (REPO / ".github" / "workflows" / "release.yml").read_text()
    assert IDENTITY_RE in sh
    assert IDENTITY_RE in ps
    assert IDENTITY_RE in wf and "SHA256SUMS.sigstore.json" in wf


def test_powershell_script_is_plain_ascii_for_windows_powershell():
    """Windows PowerShell 5.1 reads a BOM-less script as the ANSI code page:
    keep it ASCII so no message turns into mojibake."""
    for name in ("join-lucent-iso.ps1", "join-lucent-iso.cmd"):
        raw = (TOOLS / name).read_bytes()
        assert all(b < 128 for b in raw), name
    assert b"\r\n" in (TOOLS / "join-lucent-iso.cmd").read_bytes()
