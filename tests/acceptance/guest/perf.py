#!/usr/bin/python3
"""Memory per process, for the acceptance test's performance numbers. TEST-ONLY.

  perf.py pss [--top N] [--proc DIR]

Prints a TSV table of the N processes using the most memory by PSS
(proportional set size: each shared page is split between the processes
that map it, so the column adds up to what the processes really cost), with
RSS next to it for comparison, then "# total" and "# user" lines over all
processes. Reads /proc/<pid>/smaps_rollup, which needs root for other users'
processes. Kernel threads (no mappings) are left out.
"""
import argparse
import os
import pwd
import sys
from dataclasses import dataclass
from pathlib import Path

# Programs whose comm is their interpreter: name them by the script instead.
INTERPRETERS = {"python", "python3", "perl", "sh", "bash", "node"}


@dataclass
class Row:
    pid: int
    user: str
    name: str
    pss_kib: int
    rss_kib: int
    anon_kib: int
    file_kib: int
    shmem_kib: int


def _name(comm, cmdline):
    base = comm.split(".")[0] if comm.startswith("python3.") else comm
    if base in INTERPRETERS:
        for arg in cmdline[1:]:
            if arg and not arg.startswith("-"):
                return os.path.basename(arg)
    return comm


def _uid(status_text):
    for line in status_text.splitlines():
        if line.startswith("Uid:"):
            return int(line.split()[1])
    return -1


def pss_rows(proc_root="/proc", user_of=None):
    """Every userspace process's memory, largest PSS first."""
    if user_of is None:
        def user_of(uid):
            try:
                return pwd.getpwuid(uid).pw_name
            except KeyError:
                return None
    rows = []
    for d in Path(proc_root).iterdir():
        if not d.name.isdigit():
            continue
        try:
            rollup = (d / "smaps_rollup").read_text()
            comm = (d / "comm").read_text().strip()
            cmdline = (d / "cmdline").read_bytes().split(b"\0")
            uid = _uid((d / "status").read_text())
        except (OSError, ValueError):
            continue  # exited meanwhile, or not ours to read
        vals = {}
        for line in rollup.splitlines():
            key, _, rest = line.partition(":")
            if rest.strip().endswith("kB"):
                vals[key] = int(rest.split()[0])
        if "Pss" not in vals:
            continue  # kernel thread
        args = [a.decode("utf-8", "replace") for a in cmdline if a]
        rows.append(Row(int(d.name), user_of(uid) or str(uid), _name(comm, args), vals["Pss"],
                        vals.get("Rss", 0), vals.get("Pss_Anon", 0), vals.get("Pss_File", 0),
                        vals.get("Pss_Shmem", 0)))
    rows.sort(key=lambda r: (-r.pss_kib, r.pid))
    return rows


def mib(kib):
    return f"{kib / 1024:.1f}"


def format_table(rows, top=25):
    out = ["pss_mib\trss_mib\tanon_mib\tfile_mib\tshmem_mib\tuser\tpid\tname"]
    for r in rows[:top]:
        out.append("\t".join([mib(r.pss_kib), mib(r.rss_kib), mib(r.anon_kib), mib(r.file_kib),
                              mib(r.shmem_kib), r.user, str(r.pid), r.name]))
    total = sum(r.pss_kib for r in rows)
    out.append(f"# total\t{mib(total)}\t{mib(sum(r.rss_kib for r in rows))}\tprocesses {len(rows)}")
    by_user = {}
    for r in rows:
        by_user[r.user] = by_user.get(r.user, 0) + r.pss_kib
    out.append("# user\t" + "\t".join(f"{u} {mib(k)}" for u, k in sorted(by_user.items(), key=lambda x: -x[1])))
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pss")
    p.add_argument("--top", type=int, default=25)
    p.add_argument("--proc", default="/proc")
    a = ap.parse_args(argv)
    sys.stdout.write(format_table(pss_rows(a.proc), a.top))
    return 0


if __name__ == "__main__":
    sys.exit(main())
