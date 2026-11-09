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
    # iwlwifi: iwlwifi-<chip>-<API>.ucode, API "89" or "c106" (iwlmld)
    (re.compile(r"^(iwlwifi-.+)-c?\d+\.ucode$"), r"\1-*.ucode"),
    # ath10k: firmware-<API>.bin, newest first
    (re.compile(r"^(ath10k/.+/)firmware-\d+\.bin$"), r"\1firmware-*.bin"),
    # ath10k/ath11k: board-2.bin (many boards in one file), else board.bin
    (re.compile(r"^(ath1[01]k/.+/)board-2\.bin$"), r"\1board*.bin"),
]

# Files that must exist for a device class to work: drivers, firmware and
# user-space pieces that a package rename or a base-image change could drop
# without any firmware reference noticing. (name, arch, [globs]; any match).
M = "/usr/lib/modules/*/kernel/"


@dataclasses.dataclass
class Capability:
    name: str
    arch: str      # any | x86_64 | aarch64
    globs: list


CAPABILITIES = [Capability(*c) for c in [
    # Wi-Fi drivers for the common laptop and desktop chips
    ("Wi-Fi: Intel (iwlwifi)", "any", [M + "drivers/net/wireless/intel/iwlwifi/iwlwifi.ko*"]),
    ("Wi-Fi: Realtek (rtw88/rtw89)", "any", [M + "drivers/net/wireless/realtek/rtw89/rtw89_8852be.ko*"]),
    ("Wi-Fi: MediaTek (mt7921/mt7925)", "any", [M + "drivers/net/wireless/mediatek/mt76/mt7921/mt7921e.ko*"]),
    ("Wi-Fi: Qualcomm (ath11k/ath12k)", "any", [M + "drivers/net/wireless/ath/ath12k/ath12k*.ko*"]),
    ("Wi-Fi: Broadcom (brcmfmac)", "any", [M + "drivers/net/wireless/broadcom/brcm80211/brcmfmac/brcmfmac.ko*"]),
    ("Wi-Fi regulatory database", "any", ["/usr/lib/firmware/regulatory.db*"]),
    ("Wi-Fi in NetworkManager", "any", ["/usr/lib64/NetworkManager/*/libnm-device-plugin-wifi.so"]),
    # Ethernet: onboard, USB and USB-C docks
    ("Ethernet: Realtek onboard (r8169)", "any", [M + "drivers/net/ethernet/realtek/r8169.ko*"]),
    ("Ethernet: Intel onboard (e1000e/igc)", "any", [M + "drivers/net/ethernet/intel/igc/igc.ko*"]),
    ("Ethernet: Realtek USB/dock (r8152)", "any", [M + "drivers/net/usb/r8152.ko*"]),
    ("Ethernet: ASIX/AX88179 USB/dock", "any", [M + "drivers/net/usb/ax88179_178a.ko*"]),
    ("Ethernet: USB CDC (phones, docks)", "any", [M + "drivers/net/usb/cdc_ncm.ko*"]),
    ("Mobile broadband: MBIM/QMI modems", "any", [M + "drivers/net/usb/cdc_mbim.ko*"]),
    ("Mobile broadband: PCIe 5G modems (MHI)", "any", [M + "drivers/net/wwan/mhi_wwan_mbim.ko*"]),
    # Bluetooth
    ("Bluetooth: USB adapters (btusb)", "any", [M + "drivers/bluetooth/btusb.ko*"]),
    ("Bluetooth: Intel firmware", "any", ["/usr/lib/firmware/intel/ibt-*"]),
    ("Bluetooth: Realtek firmware", "any", ["/usr/lib/firmware/rtl_bt/*"]),
    ("Bluetooth: MediaTek firmware", "any", ["/usr/lib/firmware/mediatek/BT_RAM_CODE_*"]),
    # Sound
    ("Sound: HD Audio (snd-hda-intel)", "any", [M + "sound/hda/controllers/snd-hda-intel.ko*",
                                                M + "sound/pci/hda/snd-hda-intel.ko*"]),
    ("Sound: Intel SOF laptops", "x86_64", [M + "sound/soc/sof/intel/snd-sof-pci-intel-tgl.ko*"]),
    ("Sound: Intel SOF firmware", "any", ["/usr/lib/firmware/intel/sof*/*"]),
    ("Sound: AMD ACP (SOF firmware)", "any", ["/usr/lib/firmware/amd/sof/*"]),
    ("Sound: Cirrus smart amplifiers", "any", ["/usr/lib/firmware/cirrus/*"]),
    ("Sound: TI smart amplifiers (tas2781)", "any", [M + "sound/hda/codecs/side-codecs/snd-hda-scodec-tas2781*.ko*",
                                                     M + "sound/pci/hda/snd-hda-scodec-tas2781*.ko*"]),
    ("Sound: USB headsets and interfaces", "any", [M + "sound/usb/snd-usb-audio.ko*"]),
    ("Sound: UCM profiles (speaker/headset/HDMI routing)", "any", ["/usr/share/alsa/ucm2/ucm.conf"]),
    ("Sound: PipeWire with PulseAudio compatibility", "any", ["/usr/bin/pipewire-pulse"]),
    # Graphics and hardware video decode
    ("GPU: Intel kernel drivers (i915/xe)", "x86_64", [M + "drivers/gpu/drm/xe/xe.ko*"]),
    ("GPU: AMD kernel driver (amdgpu)", "any", [M + "drivers/gpu/drm/amd/amdgpu/amdgpu.ko*"]),
    ("GPU: NVIDIA kernel driver (nouveau)", "any", [M + "drivers/gpu/drm/nouveau/nouveau.ko*"]),
    ("GPU: NVIDIA GSP firmware (Turing and newer)", "any", ["/usr/lib/firmware/nvidia/*/gsp/*"]),
    ("OpenGL: Intel (iris)", "x86_64", ["/usr/lib64/dri/iris_dri.so"]),
    ("OpenGL: AMD (radeonsi)", "any", ["/usr/lib64/dri/radeonsi_dri.so"]),
    ("OpenGL: NVIDIA (nouveau)", "any", ["/usr/lib64/dri/nouveau_dri.so"]),
    ("Vulkan: Intel (ANV)", "x86_64", ["/usr/share/vulkan/icd.d/intel_icd.*.json"]),
    ("Vulkan: AMD (RADV)", "any", ["/usr/share/vulkan/icd.d/radeon_icd.*.json"]),
    ("Vulkan: NVIDIA (NVK)", "any", ["/usr/share/vulkan/icd.d/nouveau_icd.*.json"]),
    ("Vulkan: Qualcomm Adreno (Turnip)", "aarch64", ["/usr/share/vulkan/icd.d/freedreno_icd.*.json"]),
    ("Video decode: Intel (VA-API iHD)", "x86_64", ["/usr/lib64/dri/iHD_drv_video.so"]),
    ("Video decode: AMD (VA-API radeonsi)", "any", ["/usr/lib64/dri/radeonsi_drv_video.so"]),
    ("Video decode: NVIDIA (VA-API nouveau)", "any", ["/usr/lib64/dri/nouveau_drv_video.so"]),
    # Webcams
    ("Webcam: USB (UVC)", "any", [M + "drivers/media/usb/uvc/uvcvideo.ko*"]),
    ("Webcam: Intel IPU6 driver", "x86_64", [M + "drivers/media/pci/intel/ipu6/intel-ipu6.ko*"]),
    ("Webcam: Intel IPU6 firmware", "x86_64", ["/usr/lib/firmware/intel/ipu/ipu6*_fw.bin*"]),
    ("Webcam: Intel IPU7 firmware", "x86_64", ["/usr/lib/firmware/intel/ipu/ipu7*_fw.bin*"]),
    ("Webcam: Intel VSC firmware", "x86_64", ["/usr/lib/firmware/intel/vsc/ivsc_fw.bin*"]),
    ("Webcam: libcamera software ISP", "any", ["/usr/lib64/libcamera/ipa/ipa_soft_simple.so"]),
    ("Webcam: libcamera in PipeWire", "any", ["/usr/lib64/spa-0.2/libcamera/libspa-libcamera.so"]),
    # USB, Thunderbolt, card readers
    ("USB storage (UAS)", "any", [M + "drivers/usb/storage/uas.ko*"]),
    ("Thunderbolt/USB4", "any", [M + "drivers/thunderbolt/thunderbolt.ko*"]),
    ("Thunderbolt device authorisation (boltd)", "any", ["/usr/libexec/boltd"]),
    ("Card reader: Realtek PCIe (rtsx)", "any", [M + "drivers/mmc/host/rtsx_pci_sdmmc.ko*"]),
    ("Card reader: Realtek USB (rtsx_usb)", "any", [M + "drivers/mmc/host/rtsx_usb_sdmmc.ko*"]),
    # Input, sensors, fingerprint, laptop controls
    ("Touchpads and touchscreens (I2C HID)", "any", [M + "drivers/hid/i2c-hid/i2c-hid*.ko*"]),
    ("Touchscreens and pens (hid-multitouch)", "any", [M + "drivers/hid/hid-multitouch.ko*"]),
    ("Pens and tablets (libwacom data)", "any", ["/usr/share/libwacom/*.tablet"]),
    ("Sensors: Intel ISH (auto-rotate, lid)", "x86_64", [M + "drivers/hid/intel-ish-hid/intel-ish-ipc.ko*"]),
    ("Sensors: iio-sensor-proxy", "any", ["/usr/libexec/iio-sensor-proxy"]),
    ("Fingerprint readers (fprintd)", "any", ["/usr/libexec/fprintd"]),
    ("Laptop keys/brightness: ThinkPad", "x86_64", [M + "drivers/platform/x86/lenovo/thinkpad_acpi.ko*",
                                                    M + "drivers/platform/x86/thinkpad_acpi.ko*"]),
    ("Laptop keys/brightness: ASUS", "x86_64", [M + "drivers/platform/x86/asus-wmi.ko*",
                                                M + "drivers/platform/x86/asus/asus-wmi.ko*"]),
    ("Laptop keys/brightness: Dell", "x86_64", [M + "drivers/platform/x86/dell/dell-wmi.ko*"]),
    ("Laptop keys/brightness: HP", "x86_64", [M + "drivers/platform/x86/hp/hp-wmi.ko*"]),
    ("Laptop keys/brightness: Acer", "x86_64", [M + "drivers/platform/x86/acer-wmi.ko*"]),
    ("Laptop: Intel ME (needed by some sensors and webcams)", "x86_64", [M + "drivers/misc/mei/mei-me.ko*"]),
    ("Battery and keyboard backlight (UPower)", "any", ["/usr/libexec/upowerd"]),
    ("Hybrid graphics (switcheroo-control)", "any", ["/usr/libexec/switcheroo-control"]),
    ("Game controllers: Xbox wired (xpad)", "any", [M + "drivers/input/joystick/xpad.ko*"]),
    ("Game controllers: PlayStation (hid-playstation)", "any", [M + "drivers/hid/hid-playstation.ko*"]),
    ("Game controllers: udev access (steam-devices)", "any", ["/usr/lib/udev/rules.d/*steam*"]),
    # Printers and scanners
    ("Printing: CUPS driverless (ipp backend)", "any", ["/usr/lib/cups/backend/ipp"]),
    ("Printing: USB driverless (ipp-usb)", "any", ["/usr/sbin/ipp-usb"]),
    ("Scanning: driverless (sane-airscan)", "any", ["/usr/lib64/sane/libsane-airscan.so*"]),
]]


def check_capabilities(caps, arch, root="/"):
    """[(capability, ok, first matching path or None)] for caps that apply to arch."""
    res = []
    for c in caps:
        if c.arch not in ("any", arch):
            continue
        hit = None
        for g in c.globs:
            ms = sorted(m for m in glob.glob(os.path.join(root, g.lstrip("/"))) if os.path.exists(m))
            if ms:
                hit = "/" + os.path.relpath(ms[0], root)
                break
        res.append((c, hit is not None, hit))
    return res


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
        self.entries = entries  # [(pattern, kind, reason)]
        self.used = set()

    def lookup(self, fw):
        """(kind, reason) of the first matching entry, or (None, None)."""
        for pat, kind, reason in self.entries:
            if fnmatch.fnmatchcase(fw, pat):
                self.used.add(pat)
                return kind, reason
        return None, None

    def match(self, fw):
        return self.lookup(fw)[1]

    def unused(self):
        return [p for p, _, _ in self.entries if p not in self.used]


ALLOW_KINDS = ("absent", "excluded")


def parse_allowlist(text):
    """Lines '<glob> absent|excluded <reason>'.

    absent:   no Fedora package ships the file (if one starts to, the gate fails);
    excluded: Fedora ships it but Lucent deliberately leaves it out (server hardware).
    """
    entries = []
    for n, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 2)
        if len(parts) < 3 or parts[1] not in ALLOW_KINDS or not parts[2].strip():
            raise ValueError(f"allowlist line {n}: want '<glob> absent|excluded <reason>': {line}")
        entries.append((parts[0], parts[1], parts[2].strip()))
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
    allow_kind: str = None     # "absent" or "excluded"


def gate(missing, online):
    """Core-class files that make the audit fail."""
    fails = []
    for m in missing:
        if not m.core:
            continue
        if online and m.provider and m.allow_kind != "excluded":
            fails.append(m)          # Fedora ships it: it belongs in the image
        elif not m.allow_kind:
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
            kind, reason = allow.lookup(fw)
            missing.append(Missing(fw=fw, modules=sorted(rels), cls=cls, core=core,
                                   allow_reason=reason, allow_kind=kind))

    online = not args.offline
    if online:
        idx = fedora_index([m.fw for m in missing])
        for m in missing:
            m.provider = fedora_provider(idx, m.fw)
    fails = gate(missing, online)
    caps = check_capabilities(CAPABILITIES, arch)
    cap_fails = [c.name for c, ok, _ in caps if not ok]

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
        "capabilities": [{"name": c.name, "ok": ok, "found": hit, "wanted": c.globs} for c, ok, hit in caps],
        "capability_failures": cap_fails,
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
    return 1 if (fails or pkg_fails or cap_fails) else 0


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
          f"core-class gate failures: {len(r['gate_failures'])}; "
          f"device-class files missing: {len(r['capability_failures'])}; "
          f"required packages missing: {len(r['package_failures'])}.", ""]
    if r["gate_failures"]:
        L += ["## GATE FAILED: core firmware missing", ""]
        for m in miss:
            if m["fw"] in r["gate_failures"]:
                why = (f"Fedora package `{m['provider']}` ships it" if m["provider"] else "not on the allowlist")
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
                 f"{m['provider'] or '-'} | {(m['allow_kind'] + ': ' + m['allow_reason']) if m['allow_kind'] else '-'} |")
    L += ["", "</details>", "", "## Device classes: files that must exist", ""]
    for c in r["capabilities"]:
        L.append(f"- [{'x' if c['ok'] else ' '}] {c['name']}: " +
                 (f"`{c['found']}`" if c["ok"] else f"MISSING (`{'` or `'.join(c['wanted'])}`)"))
    L += ["", "## Required hardware packages (build_files/hardware-packages.txt)", ""]
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
    ap.add_argument("--probe", nargs="+", metavar="WHAT",
                    help="investigate instead of auditing: package name globs (Fedora repos + installed) "
                         "and /path globs (in the image, with owning package)")
    args = ap.parse_args()
    if args.probe:
        sys.exit(probe(args.probe))
    sys.exit(audit(args))


def probe(items):
    pkgs = [i for i in items if not i.startswith("/")]
    for path in (i for i in items if i.startswith("/")):
        hits = sorted(glob.glob(path, recursive=True))
        print(f"== {path}: {len(hits)} match(es)")
        for h in hits[:40]:
            owner = run(["rpm", "-qf", "--qf", "%{NAME}\n", h], check=False).strip() or "(no package)"
            print(f"   {h}  [{owner}]")
    if pkgs:
        print("== Fedora repositories: name arch installsize repo")
        print(run(DNF + ["repoquery", "--available", "--latest-limit=1", "--queryformat",
                         "%{name} %{arch} %{installsize} %{repoid}\n", *pkgs], check=False))
        print("== installed in the image")
        print(run(["rpm", "-q", *[p for p in pkgs if not _is_glob(p)]], check=False))
    return 0


if __name__ == "__main__":
    main()
