"""Tests for the acceptance harness's pure parts: the verdict and the PPM->PNG
conversion the screenshots fall back to."""
import struct
import subprocess
import sys
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import harness  # noqa: E402
import summarize  # noqa: E402

DONE = {"guest_done": True, "guest_rc": 0, "timed_out": False}


def all_pass():
    return [(cid, "PASS", "ok") for cid, _ in summarize.REQUIRED]


def test_all_required_checks_passing_is_a_pass():
    ok, checks, failures = summarize.evaluate(all_pass(), DONE)
    assert ok and not failures
    assert [c["id"] for c in checks] == [cid for cid, _ in summarize.REQUIRED]


def test_a_check_that_never_reported_fails_the_run():
    results = all_pass()[:-1]
    ok, checks, failures = summarize.evaluate(results, DONE)
    assert not ok
    assert failures == [summarize.REQUIRED[-1][0]]
    assert checks[-1]["status"] == "MISSING"


def test_a_failed_check_fails_even_if_reported_again_as_pass():
    results = all_pass() + [("entry.created", "FAIL", "late")]
    ok, _, failures = summarize.evaluate(results, DONE)
    assert not ok and failures == ["entry.created"]


def test_extra_checks_info_is_fine_but_fail_is_not():
    ok, _, _ = summarize.evaluate(all_pass() + [("entry.after-close", "INFO", "x")], DONE)
    assert ok
    ok, _, failures = summarize.evaluate(all_pass() + [("binfmt.mz", "FAIL", "x")], DONE)
    assert not ok and failures == ["binfmt.mz"]


def test_guest_that_never_finished_or_timed_out_fails():
    ok, _, failures = summarize.evaluate(all_pass(), {"guest_done": False})
    assert not ok and "never finished" in failures[0]
    ok, _, _ = summarize.evaluate(all_pass(), dict(DONE, timed_out=True))
    assert not ok


def test_summary_files_and_exit_code(tmp_path):
    (tmp_path / "results").mkdir()
    (tmp_path / "results" / "results.tsv").write_text(
        "".join(f"{cid}\tPASS\tfine\n" for cid, _ in summarize.REQUIRED))
    (tmp_path / "results" / "metrics.tsv").write_text("ram_used_idle_mib\t1234\n")
    (tmp_path / "harness.json").write_text('{"guest_done": true, "guest_rc": 0, "timed_out": false}')
    r = subprocess.run([sys.executable, str(HERE / "summarize.py"), str(tmp_path)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout
    assert "PASSED" in (tmp_path / "summary.md").read_text()
    assert "| RAM used, idle 2 min after login (MiB) | 1234 |" in (tmp_path / "summary.md").read_text()
    (tmp_path / "results" / "results.tsv").write_text("session.plasma\tPASS\tfine\n")
    r = subprocess.run([sys.executable, str(HERE / "summarize.py"), str(tmp_path)], capture_output=True, text=True)
    assert r.returncode == 1


def test_ppm_to_png_round_trip(tmp_path):
    w, h = 3, 2
    pix = bytes(range(w * h * 3))
    (tmp_path / "a.ppm").write_bytes(b"P6\n# comment\n3 2\n255\n" + pix)
    assert harness.ppm_to_png(tmp_path / "a.ppm", tmp_path / "a.png") == (w, h)
    data = (tmp_path / "a.png").read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert harness.png_size(tmp_path / "a.png") == (w, h)
    # IDAT: filter byte 0 + RGB per row
    idat_len = struct.unpack(">I", data[33:37])[0]
    raw = zlib.decompress(data[41:41 + idat_len])
    assert raw == b"\x00" + pix[:9] + b"\x00" + pix[9:]
