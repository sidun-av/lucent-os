"""Tests for the performance helpers: the guest's PSS table (guest/perf.py)
and the harness's screen-change detector (harness.frames_differ)."""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "guest"))

import harness  # noqa: E402
import perf  # noqa: E402


def fake_proc(root, pid, comm, uid, pss, rss, anon=0, file=0, shmem=0, cmdline=None):
    d = root / str(pid)
    d.mkdir(parents=True)
    (d / "comm").write_text(comm + "\n")
    (d / "status").write_text(f"Name:\t{comm}\nUid:\t{uid}\t{uid}\t{uid}\t{uid}\n")
    (d / "cmdline").write_bytes(("\0".join(cmdline or [f"/usr/bin/{comm}"]) + "\0").encode())
    (d / "smaps_rollup").write_text(
        "55d0c0000000-7ffc00000000 ---p 00000000 00:00 0    [rollup]\n"
        f"Rss:             {rss} kB\n"
        f"Pss:             {pss} kB\n"
        f"Pss_Dirty:       {pss // 2} kB\n"
        f"Pss_Anon:        {anon} kB\n"
        f"Pss_File:        {file} kB\n"
        f"Pss_Shmem:       {shmem} kB\n"
        "Swap:                  0 kB\n")


def test_pss_rows_sorted_largest_first_with_users(tmp_path):
    fake_proc(tmp_path, 10, "kwin_wayland", 1000, pss=200_000, rss=360_000, anon=150_000, file=50_000)
    fake_proc(tmp_path, 11, "plasmashell", 1000, pss=300_000, rss=480_000)
    fake_proc(tmp_path, 1, "systemd", 0, pss=9_000, rss=23_000)
    (tmp_path / "self").mkdir()          # not a pid: ignored
    (tmp_path / "meminfo").write_text("MemTotal: 1 kB\n")
    users = {0: "root", 1000: "anna"}
    rows = perf.pss_rows(tmp_path, users.get)
    assert [r.name for r in rows] == ["plasmashell", "kwin_wayland", "systemd"]
    assert rows[1].user == "anna" and rows[1].pss_kib == 200_000 and rows[1].rss_kib == 360_000
    assert rows[1].anon_kib == 150_000 and rows[1].file_kib == 50_000
    assert rows[2].user == "root"


def test_pss_skips_kernel_threads_and_vanished_processes(tmp_path):
    fake_proc(tmp_path, 5, "plasmashell", 1000, pss=1000, rss=2000)
    kthread = tmp_path / "2"
    kthread.mkdir()
    (kthread / "comm").write_text("kthreadd\n")
    (kthread / "smaps_rollup").write_text("")      # kernel threads have no mappings
    (kthread / "cmdline").write_bytes(b"")
    gone = tmp_path / "7"
    gone.mkdir()                                  # exited between listdir and read
    rows = perf.pss_rows(tmp_path, lambda uid: str(uid))
    assert [r.pid for r in rows] == [5]


def test_python_programs_are_named_by_their_script(tmp_path):
    fake_proc(tmp_path, 20, "python3", 0, pss=40_000, rss=44_000,
              cmdline=["/usr/bin/python3", "-Es", "/usr/sbin/tuned", "-l", "-P"])
    fake_proc(tmp_path, 21, "tuned-ppd", 0, pss=30_000, rss=40_000,
              cmdline=["/usr/bin/python3", "-Es", "/usr/sbin/tuned-ppd", "-l"])
    rows = perf.pss_rows(tmp_path, lambda uid: "root")
    assert [r.name for r in rows] == ["tuned", "tuned-ppd"]


def test_table_has_top_n_and_totals(tmp_path):
    for i in range(30):
        fake_proc(tmp_path, 100 + i, f"p{i}", 1000 if i % 2 else 0, pss=(i + 1) * 1024, rss=(i + 1) * 2048)
    rows = perf.pss_rows(tmp_path, {0: "root", 1000: "anna"}.get)
    text = perf.format_table(rows, top=25)
    lines = text.splitlines()
    assert lines[0].split("\t")[:3] == ["pss_mib", "rss_mib", "anon_mib"]
    body = [ln for ln in lines[1:] if not ln.startswith("#")]
    assert len(body) == 25
    assert body[0].split("\t")[-1].startswith("p29")
    totals = {ln.split("\t")[0]: ln for ln in lines if ln.startswith("#")}
    # sum of 1..30 MiB = 465, split between the two users
    assert "465.0" in totals["# total"]
    assert "processes 30" in totals["# total"]
    assert "anna" in totals["# user"] and "root" in totals["# user"]


def test_cli_writes_the_table(tmp_path):
    fake_proc(tmp_path, 3, "kded6", 0, pss=50_000, rss=100_000)
    r = subprocess.run([sys.executable, str(HERE / "guest" / "perf.py"), "pss", "--proc", str(tmp_path),
                        "--top", "5"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "kded6" in r.stdout and r.stdout.startswith("pss_mib\t")


# ---------------------------------------------------------------- screen changes
def ppm(w, h, fill=(10, 20, 30), box=None, color=(250, 250, 250)):
    pix = bytearray(bytes(fill) * (w * h))
    if box:
        x0, y0, x1, y1 = box
        for y in range(y0, y1):
            for x in range(x0, x1):
                i = (y * w + x) * 3
                pix[i:i + 3] = bytes(color)
    return b"P6\n%d %d\n255\n" % (w, h) + bytes(pix)


def test_identical_frames_do_not_differ():
    a = harness.Frame.parse(ppm(64, 48))
    assert harness.frames_differ(a, harness.Frame.parse(ppm(64, 48))) is False


def test_a_popup_is_a_change_but_a_blinking_caret_is_not():
    base = harness.Frame.parse(ppm(160, 120))
    caret = harness.Frame.parse(ppm(160, 120, box=(50, 50, 51, 62)))   # 0.06 % of the screen
    popup = harness.Frame.parse(ppm(160, 120, box=(20, 20, 120, 100)))
    assert harness.frames_differ(base, caret) is False
    assert harness.frames_differ(base, popup) is True


def test_small_colour_noise_is_not_a_change():
    a = harness.Frame.parse(ppm(80, 60, fill=(100, 100, 100)))
    b = harness.Frame.parse(ppm(80, 60, fill=(108, 100, 100)))
    assert harness.frames_differ(a, b) is False


def test_frames_of_another_size_always_differ():
    assert harness.frames_differ(harness.Frame.parse(ppm(64, 48)), harness.Frame.parse(ppm(48, 64))) is True


def test_measure_reports_first_change_and_when_it_settled():
    # frames at t = 0, 50, 100, ...: unchanged, then an animation from 150 to 300, then still
    base = ppm(160, 120)
    seq = [base, base, base] + [ppm(160, 120, box=(20, 20, 40 + 10 * i, 100)) for i in range(4)]
    seq += [seq[-1]] * 20
    clock = {"t": 0.0}

    def grab():
        f = harness.Frame.parse(seq[min(round(clock["t"] / 0.05), len(seq) - 1)])
        clock["t"] += 0.05
        return f

    ref = harness.Frame.parse(base)
    first, settled = harness.watch_change(grab, ref, start=0.0, timeout=2.0, stable=0.3,
                                          now=lambda: clock["t"])
    assert abs(first - 0.15) < 1e-6
    assert abs(settled - 0.30) < 1e-6


def test_measure_without_any_change_times_out():
    base = ppm(32, 24)
    clock = {"t": 0.0}

    def grab():
        clock["t"] += 0.05
        return harness.Frame.parse(base)

    first, settled = harness.watch_change(grab, harness.Frame.parse(base), start=0.0, timeout=1.0,
                                          stable=0.3, now=lambda: clock["t"])
    assert first is None and settled is None
