#!/usr/bin/env python3
"""Summarise an acceptance run: summarize.py OUT_DIR

Reads OUT_DIR/results/{results.tsv,metrics.tsv} (written by the guest),
its logs (the second boot's memory table and boot chain), OUT_DIR/harness.json
and OUT_DIR/screens/, writes OUT_DIR/summary.json and OUT_DIR/summary.md, and
exits 1 unless every required check passed and no check failed. A check that
never reported counts as failed, so a guest that dies half-way can't pass.
"""
import json
import re
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
    ("session_up_s", "desktop session running (s after kernel start)"),
    ("ram_used_idle_mib", "RAM used, idle 2 min after login (MiB)"),
    ("pss_total_mib", "PSS of all processes, idle (MiB)"),
    ("ram_total_mib", "RAM of the VM (MiB)"),
    ("services_running_system", "running system services"),
    ("services_running_user", "running user services"),
    ("failed_units", "failed units, 2 min after login"),
    ("avc_at_boot", "SELinux denial records, power-on to 2 min after login"),
    ("boot2_systemd_analyze", "systemd-analyze, second boot"),
    ("boot2_graphical_target", "graphical.target, second boot"),
    ("boot2_session_up_s", "desktop session running, second boot (s after kernel start)"),
    ("boot2_ram_used_idle_mib", "RAM used, idle 2 min after login, second boot (MiB)"),
    ("boot2_pss_total_mib", "PSS of all processes, idle, second boot (MiB)"),
    ("boot2_services_running_system", "running system services, second boot"),
    ("boot2_services_running_user", "running user services, second boot"),
    ("boot2_failed_units", "failed units, second boot"),
    ("boot2_avc_at_boot", "SELinux denial records, second boot"),
    ("reboot_to_session_s", "reboot, wall clock: reboot command to desktop session (s)"),
    ("reboot_before_kernel_s", "of which shutdown, firmware and GRUB loading kernel + initramfs (s)"),
    ("shutdown_s", "of which the first boot's shutdown (s)"),
    ("firmware_grub_s", "of which firmware and GRUB, kernel and initramfs loaded (s)"),
    ("launcher_cold_first_ms", "launcher opens, first time: first change (ms)"),
    ("launcher_cold_settled_ms", "launcher opens, first time: animation done (ms)"),
    ("launcher_warm_first_ms", "launcher opens, warm: first change (ms)"),
    ("launcher_warm_settled_ms", "launcher opens, warm: animation done (ms)"),
    ("app_files_ms", "Dolphin: Enter to window (ms)"),
    ("app_settings_ms", "Settings: Enter to window (ms)"),
    ("app_store_ms", "Store: Enter to window (ms)"),
    ("app_firefox_ms", "Firefox (Flatpak, first start): Enter to window (ms)"),
    ("app_notepadpp_ms", "Notepad++ (Windows app): Enter to window (ms)"),
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


def machine(harness):
    if "smp" not in harness:
        return ""
    return f", {harness['smp']} vCPU, {harness.get('mem_mib', 0) / 1024:g} GB"


def reboot_times(harness_log):
    """From harness.log: (seconds from the first boot's reboot command to the
    second boot's desktop session, of which before the kernel started:
    shutdown, firmware and GRUB loading kernel and initramfs), or Nones."""
    t_reboot = t_session = up = None
    for line in harness_log.splitlines():
        stamp, _, rest = line.partition("] ")
        try:
            t = float(stamp.lstrip("[ "))
        except ValueError:
            continue
        if rest.startswith("log: first boot done") and "rebooting" in rest:
            t_reboot = t
        elif rest.startswith("metric: boot2_session_up_s "):
            t_session, up = t, float(rest.split()[-1])
    if t_reboot is None or t_session is None:
        return None, None
    return t_session - t_reboot, t_session - t_reboot - up


def shutdown_time(guest_log, serial_log):
    """Seconds the first boot took to shut down: from the reboot command
    (guest's acceptance.log, uptime) to the kernel's "reboot: Restarting
    system" on the serial console (uptime), or None."""
    t_cmd = t_restart = None
    for line in guest_log.splitlines():
        if "ctl: LOG first boot done" in line and "rebooting" in line:
            t_cmd = float(line.split("]", 1)[0].lstrip("[ "))
    for line in serial_log.splitlines():
        m = re.search(r"\[\s*(\d+\.\d+)\] reboot: Restarting system", line)
        if m:
            t_restart = float(m.group(1))
    if t_cmd is None or t_restart is None:
        return None
    return t_restart - t_cmd


def perf_sections(logs):
    """The second boot's (else the first's) memory table and critical chain."""
    md = []
    boot = logs / "boot2" if (logs / "boot2").is_dir() else logs
    which = "second boot" if boot.name == "boot2" else "first boot"
    pss = boot / "top-pss.tsv"
    if pss.exists():
        rows = [ln.split("\t") for ln in pss.read_text(errors="replace").splitlines()]
        body = [r for r in rows[1:] if len(r) >= 8 and not r[0].startswith("#")]
        total = next((r for r in rows if r[0] == "# total"), None)
        users = next((r for r in rows if r[0] == "# user"), None)
        md += [f"### Memory by process, idle 2 min after login ({which}, PSS)", ""]
        if total and len(total) >= 4:
            md.append(f"All processes: {total[1]} MiB in {total[3].replace('processes ', '')} processes"
                      + (f" ({', '.join(users[1:])} MiB)" if users else "") + ".")
            md.append("")
        md += ["| PSS MiB | RSS MiB | user | process |", "|---:|---:|---|---|"]
        md += [f"| {r[0]} | {r[1]} | {r[5]} | {r[7]} |" for r in body]
        md.append("")
    for name, title in (("systemd-analyze-critical-chain-login.txt", "Path to the login screen"),
                        ("systemd-analyze-critical-chain.txt", "Boot critical chain")):
        chain = boot / name
        if chain.exists():
            lines = [ln for ln in chain.read_text(errors="replace").splitlines() if ln.strip()
                     and not ln.startswith("The time")]
            md += [f"### {title} ({which})", "", "```"] + lines[:25] + ["```", ""]
    return md


def main():
    out = Path(sys.argv[1])
    res = out / "results"
    results = [tuple(r) for r in read_tsv(res / "results.tsv", 3)]
    metrics = dict((k, v) for k, v in read_tsv(res / "metrics.tsv", 2))
    harness = json.loads((out / "harness.json").read_text()) if (out / "harness.json").exists() else {}
    if (out / "harness.log").exists():
        reboot, before_kernel = reboot_times((out / "harness.log").read_text(errors="replace"))
        if reboot is not None:
            metrics["reboot_to_session_s"] = f"{reboot:.1f}"
            metrics["reboot_before_kernel_s"] = f"{before_kernel:.1f}"
    guest_log, serial = res / "logs" / "acceptance.log", out / "serial-boot.log"
    if guest_log.exists() and serial.exists():
        down = shutdown_time(guest_log.read_text(errors="replace"), serial.read_text(errors="replace"))
        if down is not None:
            metrics["shutdown_s"] = f"{down:.1f}"
            if "reboot_before_kernel_s" in metrics:
                metrics["firmware_grub_s"] = f"{float(metrics['reboot_before_kernel_s']) - down:.1f}"
    ok, checks, failures = evaluate(results, harness)
    shots = sorted(p.name for p in (out / "screens").glob("*.png")) if (out / "screens").exists() else []
    summary = {"passed": ok, "failures": failures, "checks": checks, "metrics": metrics,
               "harness": harness, "screenshots": shots}
    (out / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n")
    icon = {"PASS": "✅", "FAIL": "❌", "MISSING": "❌", "INFO": "ℹ️"}
    md = [f"## Lucent OS acceptance (x86_64, KVM{machine(harness)}): {'PASSED' if ok else 'FAILED'}", "",
          "| | check | detail |", "|---|---|---|"]
    for c in checks:
        title = c["title"] or c["id"]
        detail = c["detail"].replace("|", "\\|")
        md.append(f"| {icon.get(c['status'], c['status'])} | {title} (`{c['id']}`) | {detail} |")
    md += ["", "| number | value |", "|---|---|"]
    for key, title in METRICS:
        if key in metrics:
            md.append(f"| {title} | {metrics[key].replace('|', '/')} |")
    md += [""] + perf_sections(res / "logs")
    md += ["Screenshots: " + ", ".join(f"`{s}`" for s in shots), ""]
    if failures:
        md += ["**Failed:** " + ", ".join(f"`{f}`" for f in failures), ""]
    (out / "summary.md").write_text("\n".join(md))
    print("\n".join(md))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
