#!/usr/bin/env python3
"""Summarise an acceptance run: summarize.py OUT_DIR

Reads OUT_DIR/results/{results.tsv,metrics.tsv} (written by the guest),
OUT_DIR/harness.json and OUT_DIR/screens/, writes OUT_DIR/summary.json and
OUT_DIR/summary.md, and exits 1 unless every required check passed and no
check failed. A check that never reported counts as failed, so a guest that
dies half-way can't pass.
"""
import json
import sys
from pathlib import Path

# Every check the owner's promise needs, in the order they run.
REQUIRED = [
    ("session.plasma", "Plasma session after autologin"),
    ("apps.installed", "10 offline apps installed from the ISO"),
    ("apps.favorites", "all 10 in the launcher's favorites"),
    ("apps.launcher", "all 10 in the launcher (application menu)"),
    ("template.service", "prefix template built by its service within ~5 min of boot"),
    ("exe.download", "Notepad++ installer in ~/Downloads, hash pinned"),
    ("exe.handler", ".exe defaults to lucent-bridge"),
    ("exe.opened-with-bridge", "double-click (KIO) runs lucent-bridge.desktop"),
    ("bridge.launch-sheet", "\"Preparing Windows program\" sheet after the double-click"),
    ("wine.no-download-prompt", "Wine never asks to download anything (Mono, Gecko)"),
    ("installer.gui", "installer GUI driven to the end"),
    ("entry.created", "Notepad++ launcher entry appears"),
    ("entry.valid", "entry valid (Exec, icon, StartupWMClass)"),
    ("window.notepadpp", "Notepad++ window after launching it from the launcher"),
    ("window.not-administrator", "Notepad++ not elevated: no \"[Administrator]\" in its title"),
    ("launch.from-entry", "process runs in its launcher entry's unit"),
    ("prefix.appearance", "Windows environment in the desktop's look (Pebble Drift colours, Inter)"),
    ("prefix.dxvk", "Direct3D through lucent-bridge's DXVK"),
    ("selinux.enforcing", "SELinux enforcing"),
    ("selinux.no-avc-flow", "no AVC denials during the flow"),
    ("wine-systemd.absent", "wine-systemd not installed"),
]
METRICS = [
    ("systemd_analyze", "systemd-analyze"),
    ("graphical_target", "graphical.target"),
    ("ram_used_idle_mib", "RAM used, idle 2 min after login (MiB)"),
    ("ram_total_mib", "RAM of the VM (MiB)"),
    ("services_running_system", "running system services"),
    ("services_running_user", "running user services"),
    ("disk_used_gb", "installed disk usage (GB)"),
    ("flatpak_apps_gb", "of which /var/lib/flatpak (GB)"),
    ("filesystem", "root file system"),
    ("template_finished_s", "prefix template ready (s after kernel start)"),
    ("template_size", "prefix template size"),
    ("installer_window_after_s", "double-click to installer window (s)"),
    ("lucent_bridge", "lucent-bridge"),
    ("wine", "Wine"),
    ("os", "OS"),
    ("kernel", "kernel"),
]


def read_tsv(path, cols):
    rows = []
    if path.exists():
        for line in path.read_text(errors="replace").splitlines():
            if line.strip():
                parts = line.split("\t", cols - 1)
                rows.append(parts + [""] * (cols - len(parts)))
    return rows


def evaluate(results, harness):
    """results: [(id, status, detail)] -> (ok, checks, failures)."""
    by_id = {}
    for cid, status, detail in results:
        by_id.setdefault(cid, []).append((status, detail))
    failures = []
    checks = []
    for cid, title in REQUIRED:
        got = by_id.get(cid)
        if not got:
            checks.append({"id": cid, "title": title, "status": "MISSING", "detail": "never reported"})
            failures.append(cid)
            continue
        status = "FAIL" if any(s == "FAIL" for s, _ in got) else got[-1][0]
        if status != "PASS":
            failures.append(cid)
        checks.append({"id": cid, "title": title, "status": status, "detail": " | ".join(d for _, d in got)})
    required = {cid for cid, _ in REQUIRED}
    for cid, status, detail in results:
        if cid not in required:
            checks.append({"id": cid, "title": "", "status": status, "detail": detail})
            if status == "FAIL":
                failures.append(cid)
    if not harness.get("guest_done"):
        failures.append("harness: the guest never finished")
    if harness.get("timed_out"):
        failures.append("harness: timeout")
    return not failures, checks, failures


def main():
    out = Path(sys.argv[1])
    res = out / "results"
    results = [tuple(r) for r in read_tsv(res / "results.tsv", 3)]
    metrics = dict((k, v) for k, v in read_tsv(res / "metrics.tsv", 2))
    harness = json.loads((out / "harness.json").read_text()) if (out / "harness.json").exists() else {}
    ok, checks, failures = evaluate(results, harness)
    shots = sorted(p.name for p in (out / "screens").glob("*.png")) if (out / "screens").exists() else []
    summary = {"passed": ok, "failures": failures, "checks": checks, "metrics": metrics,
               "harness": harness, "screenshots": shots}
    (out / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n")
    icon = {"PASS": "✅", "FAIL": "❌", "MISSING": "❌", "INFO": "ℹ️"}
    md = [f"## Lucent OS acceptance (x86_64, KVM): {'PASSED' if ok else 'FAILED'}", "",
          "| | check | detail |", "|---|---|---|"]
    for c in checks:
        title = c["title"] or c["id"]
        detail = c["detail"].replace("|", "\\|")
        md.append(f"| {icon.get(c['status'], c['status'])} | {title} (`{c['id']}`) | {detail} |")
    md += ["", "| number | value |", "|---|---|"]
    for key, title in METRICS:
        if key in metrics:
            md.append(f"| {title} | {metrics[key].replace('|', '/')} |")
    md += ["", "Screenshots: " + ", ".join(f"`{s}`" for s in shots), ""]
    if failures:
        md += ["**Failed:** " + ", ".join(f"`{f}`" for f in failures), ""]
    (out / "summary.md").write_text("\n".join(md))
    print("\n".join(md))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
