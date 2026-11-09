#!/usr/bin/python3
"""Lucent OS hardware audit: does the image carry what common PC hardware needs?

Runs as root INSIDE a Lucent OS image (CI: .github/workflows/hardware-audit.yml):

    python3 tests/hardware/hw_audit.py --repo /src --out /out [--offline]

1. Firmware cross-check. For every kernel module of the audited device
   classes (see CLASSES), `modinfo -F firmware` lists the files the driver
   may request; each must exist under /usr/lib/firmware (plain, .xz or
   .zst). Missing files are looked up in the Fedora repositories (unless
   --offline) and classified: shipped by a Fedora package (must add) or in
   no Fedora package (documented in firmware-allowlist.txt with a reason).
2. Packages. Everything in build_files/hardware-packages.txt must be
   installed, and the Fedora comps groups in GROUPS are compared with the
   image (report only).

Exit status 1 = the gate failed: a core-class (Wi-Fi, Ethernet, Bluetooth,
audio, GPU) firmware file is missing and either Fedora ships it or it is not
on the allowlist, or a required hardware package is not installed.
Reports: <out>/hardware-audit.md and <out>/hardware-audit.json.
"""
import argparse
import concurrent.futures
import dataclasses
import fnmatch
import glob
import json
import os
import platform
import re
import subprocess
import sys

FW_ROOT = "/usr/lib/firmware"
COMPRESSED = ("", ".xz", ".zst")

# (path prefix under /usr/lib/modules/<kver>/kernel/, class, core?)
# "core" classes gate the build: without them a PC has no network, no sound
# or no picture after installation.
CLASSES = [
    ("drivers/net/wireless/", "wifi", True),
    ("drivers/net/ethernet/", "ethernet", True),
    ("drivers/net/usb/", "ethernet", True),
    ("drivers/bluetooth/", "bluetooth", True),
    ("sound/", "audio", True),
    ("drivers/gpu/drm/i915/", "gpu", True),
    ("drivers/gpu/drm/xe/", "gpu", True),
    ("drivers/gpu/drm/amd/", "gpu", True),
    ("drivers/gpu/drm/radeon/", "gpu", True),
    ("drivers/gpu/drm/nouveau/", "gpu", True),
    ("drivers/media/usb/", "webcam", False),
    ("drivers/media/pci/intel/", "webcam", False),
    ("drivers/staging/media/ipu7/", "webcam", False),
    ("drivers/usb/", "usb", False),
    ("drivers/thunderbolt/", "usb", False),
    ("drivers/hid/", "input", False),
    ("drivers/input/", "input", False),
    ("drivers/mmc/", "cardreader", False),
    ("drivers/platform/x86/", "laptop", False),
    ("drivers/misc/mei/", "laptop", False),
]

# Drivers that try several firmware API versions, newest first, and work
# with any one of them: a module lists every version it can use, the
# firmware package ships one or two. (regex on the file name, glob for "any
# version of the same file").
ALTERNATIVES = [
    (re.compile(r"^(iwlwifi-.+)-\d+\.ucode$"), r"\1-*.ucode"),
]

# Fedora comps groups compared with the image (report only).
GROUPS = ["hardware-support", "printing", "networkmanager-submodules", "multimedia"]


# --- pure logic (unit-tested in test_hw_audit.py) ----------------------------

def classify(rel):
    """Module path relative to kernel/ -> (class, core) or None if not audited."""
    for prefix, cls, core in CLASSES:
        if rel.startswith(prefix):
            return cls, core
    return None


def _strip_compression(name):
    for ext in (".xz", ".zst"):
        if name.endswith(ext):
            return name[: -len(ext)]
    return name


def _is_glob(name):
    return any(c in name for c in "*?[")


def _found(root, pattern):
    """Existing firmware files (relative, as on disk) matching pattern + any compression."""
    hits = []
    for ext in COMPRESSED:
        for p in glob.glob(os.path.join(root, glob.escape(pattern) if not _is_glob(pattern) else pattern) + ext):
            if os.path.exists(p):  # follows symlinks: a dangling link is missing
                hits.append(os.path.relpath(p, root))
    return sorted(hits)


def present(root, fw):
    return bool(_found(root, fw))


def alternative_glob(fw):
    for rx, repl in ALTERNATIVES:
        if rx.match(fw):
            return rx.sub(repl, fw)
    return None


def satisfied(root, fw):
    """fw itself if present, else an on-disk alternative the driver also loads, else None."""
    if present(root, fw):
        return fw
    alt = alternative_glob(fw)
    if alt:
        hits = _found(root, alt)
        if hits:
            return hits[-1]
    return None


class Allowlist:
    def __init__(self, entries):
        self.entries = entries  # [(pattern, reason)]
        self.used = set()

    def match(self, fw):
        for pat, reason in self.entries:
            if fnmatch.fnmatchcase(fw, pat):
                self.used.add(pat)
                return reason
        return None

    def unused(self):
        return [p for p, _ in self.entries if p not in self.used]


def parse_allowlist(text):
    entries = []
    for n, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) < 2 or not parts[1].strip():
            raise ValueError(f"allowlist line {n}: '{line}' has no reason")
        entries.append((parts[0], parts[1].strip()))
    return Allowlist(entries)


def parse_fedora_files(out):
    """'@@PKG name' header lines followed by file paths -> {firmware name: package}."""
    idx = {}
    pkg = None
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("@@PKG "):
            pkg = line[6:].strip()
            continue
        for prefix in ("/usr/lib/firmware/", "/lib/firmware/"):
            if pkg and line.startswith(prefix):
                idx.setdefault(_strip_compression(line[len(prefix):]), pkg)
    return idx


def fedora_provider(idx, fw):
    if fw in idx:
        return idx[fw]
    pats = [fw] if _is_glob(fw) else []
    alt = alternative_glob(fw)
    if alt:
        pats.append(alt)
    for pat in pats:
        for name in sorted(idx):
            if fnmatch.fnmatchcase(name, pat):
                return idx[name]
    return None


@dataclasses.dataclass
class Missing:
    fw: str
    modules: list
    cls: str
    core: bool
    provider: str = None       # Fedora package that ships it (None: none does / not checked)
    allow_reason: str = None   # why it is acceptable (firmware-allowlist.txt)


def gate(missing, online):
    """Core-class files that make the audit fail."""
    fails = []
    for m in missing:
        if not m.core:
            continue
        if online and m.provider:
            fails.append(m)          # Fedora ships it: it belongs in the image
        elif not m.allow_reason:
            fails.append(m)          # nobody has looked at it yet
    return fails


_GROUP_KEYS = {"mandatory packages": "mandatory", "default packages": "default",
               "optional packages": "optional", "conditional packages": "conditional"}


def parse_group_info(out):
    g = {v: [] for v in _GROUP_KEYS.values()}
    cur = None
    for line in out.splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key, val = key.strip().lower(), val.strip()
        if key:
            cur = _GROUP_KEYS.get(key)
        if cur and val:
            # dnf5 lists conditional packages as "name (if other)"; keep the name
            g[cur].append(val.split()[0])
    return g


@dataclasses.dataclass
class Pkg:
    name: str
    arch: str
    reason: str


def parse_package_list(text):
    pkgs = []
    for n, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 2)
        if len(parts) < 3 or parts[1] not in ("any", "x86_64", "aarch64"):
            raise ValueError(f"package list line {n}: want '<name> any|x86_64|aarch64 <reason>': {line}")
        pkgs.append(Pkg(*parts))
    return pkgs


def for_arch(pkgs, arch):
    return [p for p in pkgs if p.arch in ("any", arch)]


# --- system access -------------------------------------------------------------

def run(cmd, check=True):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd[:4])}... failed ({r.returncode}): {r.stderr[-2000:]}")
    return r.stdout


def kernel_dir():
    cands = sorted(d for d in glob.glob("/usr/lib/modules/*") if os.path.isdir(os.path.join(d, "kernel")))
    if not cands:
        sys.exit("no kernel modules under /usr/lib/modules")
    return cands[-1]


def scan_modules(kdir):
    """{module rel path: [firmware names]} for audited classes."""
    base = os.path.join(kdir, "kernel")
    mods = []
    for dirpath, _, files in os.walk(base):
        for f in files:
            if re.search(r"\.ko(\.xz|\.zst|\.gz)?$", f):
                rel = os.path.relpath(os.path.join(dirpath, f), base)
                if classify(rel):
                    mods.append(rel)

    def fw_of(rel):
        out = run(["modinfo", "-F", "firmware", os.path.join(base, rel)], check=False)
        return rel, [l.strip() for l in out.splitlines() if l.strip()]

    with concurrent.futures.ThreadPoolExecutor(16) as ex:
        return dict(ex.map(fw_of, sorted(mods)))


DNF = ["dnf5", "-q", "--setopt=optional_metadata_types=filelists"]


def fedora_index(missing_names):
    """{firmware name: Fedora package} for firmware packages, plus whatever ships missing_names."""
    out = run(DNF + ["repoquery", "--available", "--queryformat", "@@PKG %{name}\n%{files}\n",
                     "*firmware*", "*-fw", "*-fw-*", "*ucode*", "*openfwwf*"])
    idx = parse_fedora_files(out)
    rest = [n for n in missing_names if not _is_glob(n) and fedora_provider(idx, n) is None]
    if rest:
        caps = [f"{FW_ROOT}/{n}{ext}" for n in rest for ext in COMPRESSED]
        names = set()
        for i in range(0, len(caps), 300):
            o = run(DNF + ["repoquery", "--available", "--queryformat", "%{name}\n",
                           "--whatprovides", ",".join(caps[i:i + 300])], check=False)
            names.update(l.strip() for l in o.splitlines() if l.strip())
        if names:
            out = run(DNF + ["repoquery", "--available", "--queryformat", "@@PKG %{name}\n%{files}\n",
                             *sorted(names)])
            for k, v in parse_fedora_files(out).items():
                idx.setdefault(k, v)
    return idx


def installed_names():
    return set(run(["rpm", "-qa", "--qf", "%{NAME}\n"]).split())


def available_sizes(names):
    """{name: install size in bytes} of available Fedora packages (this arch or noarch)."""
    if not names:
        return {}
    out = run(DNF + ["repoquery", "--available", "--latest-limit=1", "--queryformat",
                     "%{name} %{arch} %{installsize}\n", *sorted(names)], check=False)
    arch = platform.machine()
    sizes = {}
    for line in out.splitlines():
        p = line.split()
        if len(p) == 3 and p[1] in (arch, "noarch") and p[2].isdigit():
            sizes[p[0]] = max(sizes.get(p[0], 0), int(p[2]))
    return sizes


def group_info(gid):
    out = run(DNF + ["group", "info", gid], check=False)
    return parse_group_info(out)


# --- audit --------------------------------------------------------------------

def audit(args):
    arch = platform.machine()
    kdir = kernel_dir()
    here = os.path.dirname(os.path.abspath(__file__))
    allow = parse_allowlist(open(os.path.join(here, "firmware-allowlist.txt")).read())
    pkgs = for_arch(parse_package_list(open(os.path.join(args.repo, "build_files/hardware-packages.txt")).read()), arch)

    mods = scan_modules(kdir)
    stats = {}
    want = {}   # fw -> (cls, core, [modules])
    alt_used = {}
    for rel, fws in mods.items():
        cls, core = classify(rel)
        s = stats.setdefault(cls, {"core": core, "modules": 0, "modules_with_fw": 0,
                                   "files": set(), "present": 0, "via_alternative": 0, "missing": 0})
        s["modules"] += 1
        if fws:
            s["modules_with_fw"] += 1
        for fw in fws:
            s["files"].add(fw)
            c = want.setdefault(fw, [cls, core, []])
            c[2].append(rel)
            if core and not c[1]:     # a file wanted by a core and a non-core module is core
                c[0], c[1] = cls, core

    missing = []
    for fw, (cls, core, rels) in sorted(want.items()):
        got = satisfied(FW_ROOT, fw)
        s = stats[cls]
        if got == fw:
            s["present"] += 1
        elif got:
            s["via_alternative"] += 1
            alt_used[fw] = got
        else:
            s["missing"] += 1
            missing.append(Missing(fw=fw, modules=sorted(rels), cls=cls, core=core,
                                   allow_reason=allow.match(fw)))

    online = not args.offline
    if online:
        idx = fedora_index([m.fw for m in missing])
        for m in missing:
            m.provider = fedora_provider(idx, m.fw)
    fails = gate(missing, online)

    inst = installed_names()
    pkg_rows = [{"name": p.name, "reason": p.reason, "installed": p.name in inst} for p in pkgs]
    pkg_fails = [r for r in pkg_rows if not r["installed"]]

    groups = {}
    if online:
        all_names = set()
        for gid in GROUPS:
            g = group_info(gid)
            groups[gid] = g
            for kind in ("mandatory", "default", "optional", "conditional"):
                all_names.update(g[kind])
        all_names.update(m.provider for m in missing if m.provider)
        all_names.update(r["name"] for r in pkg_fails)
        sizes = available_sizes(all_names - inst)
    else:
        sizes = {}

    report = {
        "arch": arch, "kernel": os.path.basename(kdir), "online": online,
        "classes": {k: {**v, "files": len(v["files"])} for k, v in stats.items()},
        "missing": [dataclasses.asdict(m) for m in missing],
        "alternatives_used": alt_used,
        "gate_failures": [m.fw for m in fails],
        "packages": pkg_rows,
        "package_failures": [r["name"] for r in pkg_fails],
        "groups": {gid: {kind: [{"name": n, "installed": n in inst, "available": n in sizes or n in inst,
                                 "mb": round(sizes.get(n, 0) / 1e6, 1)} for n in names]
                         for kind, names in g.items()} for gid, g in groups.items()},
        "allowlist_unused": allow.unused(),
        "sizes_mb": {n: round(b / 1e6, 1) for n, b in sorted(sizes.items())},
    }
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "hardware-audit.json"), "w") as f:
        json.dump(report, f, indent=1)
    md = render(report)
    with open(os.path.join(args.out, "hardware-audit.md"), "w") as f:
        f.write(md)
    print(md)
    return 1 if (fails or pkg_fails) else 0


def render(r):
    L = [f"# Hardware audit: {r['arch']}, kernel {r['kernel']}",
         "", f"Fedora repositories checked: {'yes' if r['online'] else 'no (--offline)'}", "",
         "## Firmware referenced by drivers", "",
         "| Class | Core | Modules | With firmware | Files | Present | Older/newer version present | Missing |",
         "|---|---|---|---|---|---|---|---|"]
    for cls, s in sorted(r["classes"].items(), key=lambda kv: (not kv[1]["core"], kv[0])):
        L.append(f"| {cls} | {'yes' if s['core'] else 'no'} | {s['modules']} | {s['modules_with_fw']} | "
                 f"{s['files']} | {s['present']} | {s['via_alternative']} | {s['missing']} |")
    miss = r["missing"]
    add = [m for m in miss if m["provider"]]
    L += ["", f"Missing files: {len(miss)}; shipped by a Fedora package: {len(add)}; "
          f"core-class gate failures: {len(r['gate_failures'])}.", ""]
    if r["gate_failures"]:
        L += ["## GATE FAILED: core firmware missing", ""]
        for m in miss:
            if m["fw"] in r["gate_failures"]:
                why = f"Fedora package `{m['provider']}` ships it" if m["provider"] else "not on the allowlist"
                L.append(f"- `{m['fw']}` ({m['cls']}; {', '.join(x.rsplit('/', 1)[-1] for x in m['modules'])}): {why}")
        L.append("")
    if add:
        L += ["## Missing, but a Fedora package ships it", "", "| File | Class | Package | MB |", "|---|---|---|---|"]
        for m in add:
            L.append(f"| `{m['fw']}` | {m['cls']} | {m['provider']} | {r['sizes_mb'].get(m['provider'], '')} |")
        L.append("")
    L += ["## All missing files", "", "<details><summary>expand</summary>", "",
          "| File | Class | Modules | Fedora package | Allowlist reason |", "|---|---|---|---|---|"]
    for m in miss:
        mods = ", ".join(x.rsplit("/", 1)[-1] for x in m["modules"][:4]) + (" ..." if len(m["modules"]) > 4 else "")
        L.append(f"| `{m['fw']}` | {m['cls']}{'' if m['core'] else ' (non-core)'} | {mods} | "
                 f"{m['provider'] or '-'} | {m['allow_reason'] or '-'} |")
    L += ["", "</details>", "", "## Required hardware packages (build_files/hardware-packages.txt)", ""]
    for p in r["packages"]:
        if p["installed"]:
            state = "x"
        else:
            mb = r["sizes_mb"].get(p["name"])
            state = " "
            p = {**p, "reason": p["reason"] + (f" (MISSING; {mb} MB in Fedora)" if mb is not None
                                               else " (MISSING; not found in the Fedora repositories)")}
        L.append(f"- [{state}] `{p['name']}`: {p['reason']}")
    for gid, g in r["groups"].items():
        L += ["", f"## Fedora comps group `{gid}`: not in the image", ""]
        any_row = False
        for kind in ("mandatory", "default", "optional", "conditional"):
            rows = [x for x in g[kind] if not x["installed"]]
            if rows:
                any_row = True
                L.append(f"- {kind}: " + ", ".join(
                    f"`{x['name']}`" + (f" ({x['mb']} MB)" if x["available"] else " (not available on this arch)")
                    for x in rows))
        if not any_row:
            L.append("- everything is installed")
    if r["allowlist_unused"]:
        L += ["", "## Allowlist entries that matched nothing (stale?)", ""]
        L += [f"- `{p}`" for p in r["allowlist_unused"]]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))
    ap.add_argument("--out", default="/tmp/hardware-audit")
    ap.add_argument("--offline", action="store_true", help="don't query the Fedora repositories")
    sys.exit(audit(ap.parse_args()))


if __name__ == "__main__":
    main()
