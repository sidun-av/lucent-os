#!/usr/bin/env python3
"""Hardware-live test of Lucent OS (CI, x86_64, QEMU/KVM, Secure Boot on).

  hwlive.py --disk QCOW2 --key SSH_KEY --tools DIR --sticks DIR --out DIR
            [--spool DIR] [--repo-rule FILE] [--timeout S]

Boots the installed system (a qcow2 of the published image plus the
test-only overlay in tests/hardware/image) with OVMF's Secure Boot firmware
and Microsoft's keys enrolled, as a Windows PC ships, and plugs in emulated
hardware the way a user would: a sound card and USB headphones, USB sticks
(FAT32, exFAT, NTFS), Wi-Fi, Bluetooth, three Ethernet cards (PCIe and a
USB dock NIC) and a network printer. For each it checks the system side
(drivers, services, mounts, internet) over SSH and the user side through
the screen: real key presses and clicks through QEMU's input devices
(QMP), and screenshots of what the virtual screen shows.

Results: OUT/results.tsv (id, PASS|FAIL|INFO, detail), OUT/summary.md,
OUT/screens/*.png, OUT/logs/. Exit status 1 on any FAIL.

Emulated hardware is not real hardware: this proves Lucent's drivers,
services and UI for these device models (and that nothing breaks under
Secure Boot), not that any particular laptop works.
"""
import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0] / "acceptance"))
sys.path.insert(0, str(HERE))
from harness import Screen, click, connect_qmp, key_event, press, type_text  # noqa: E402
import hwlib  # noqa: E402

OVMF_CODE = "/usr/share/OVMF/OVMF_CODE_4M.secboot.fd"
OVMF_VARS_MS = "/usr/share/OVMF/OVMF_VARS_4M.ms.fd"
SSH_PORT = 2222
GUEST_T = "/var/tmp/hwtest"
WIFI_SSID = "Lucent Test"
WIFI_PSK = "lucent-wifi-2026"
TONE_HZ = 1000
W, H = 1920, 1080
# The system tray: right end of the 68 px taskbar, left of the clock.
TRAY = dict(x0=1300, x1=1812, y0=1012, y1=1060)


class Test:
    def __init__(self, a):
        self.a = a
        self.out = Path(a.out)
        self.shots = self.out / "screens"
        self.logs = self.out / "logs"
        for d in (self.shots, self.logs):
            d.mkdir(parents=True, exist_ok=True)
        self.results = []
        self.t0 = time.time()
        self.proc = self.q = self.screen = None
        self.log = open(self.out / "hwlive.log", "a", buffering=1)

    # ------------------------------------------------------------ bookkeeping
    def say(self, msg):
        line = f"[{time.time() - self.t0:7.1f}] {msg}"
        print(line, flush=True)
        self.log.write(line + "\n")

    def record(self, cid, status, detail):
        detail = " ".join(str(detail).split())[:900]
        self.results.append((cid, status, detail))
        self.say(f"{status} {cid}: {detail}")
        with open(self.out / "results.tsv", "a") as f:
            f.write(f"{cid}\t{status}\t{detail}\n")

    def check(self, cid, ok, detail):
        self.record(cid, "PASS" if ok else "FAIL", detail)
        return ok

    def shot(self, name):
        try:
            self.screen.dump(self.shots / f"{name}.png")
            self.say(f"screenshot {name}.png")
        except Exception as e:  # noqa: BLE001
            self.say(f"screenshot {name} failed: {e}")

    def save(self, name, text):
        (self.logs / name).write_text(text if isinstance(text, str) else str(text))

    # ------------------------------------------------------------ guest access
    def ssh(self, script, root=False, sess=False, timeout=300, check=False):
        """Run a bash script in the guest: as lucent, as root, or inside the
        Plasma session (guest/sess.sh). Returns (rc, output)."""
        if sess:
            remote = f"SESS_MAX={timeout} bash {GUEST_T}/sess.sh"
        elif root:
            remote = "sudo bash -s"
        else:
            remote = "bash -s"
        cmd = ["ssh", *self.ssh_opts(), "lucent@127.0.0.1", remote]
        try:
            p = subprocess.run(cmd, input=script, capture_output=True, text=True, timeout=timeout + 30)
            out = (p.stdout + p.stderr).strip()
            rc = p.returncode
        except subprocess.TimeoutExpired:
            rc, out = 124, f"(timed out after {timeout} s)"
        if check and rc != 0:
            raise RuntimeError(f"guest command failed ({rc}): {script[:120]!r}: {out[-400:]}")
        return rc, out

    def ssh_opts(self):
        return ["-i", self.a.key, "-p", str(SSH_PORT), "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null", "-o", "LogLevel=ERROR", "-o", "ConnectTimeout=10",
                "-o", "BatchMode=yes", "-o", "ServerAliveInterval=15"]

    def scp(self, *src, dest):
        subprocess.run(["scp", "-q", "-r", *self.ssh_opts()[:2], "-P", str(SSH_PORT), *self.ssh_opts()[4:],
                        *map(str, src), f"lucent@127.0.0.1:{dest}"], check=True, timeout=600)

    def wait(self, seconds, script, **kw):
        """Poll a guest script until it exits 0."""
        deadline = time.time() + seconds
        rc, out = 1, ""
        while time.time() < deadline:
            rc, out = self.ssh(script, timeout=60, **kw)
            if rc == 0:
                return True, out
            time.sleep(2)
        return False, out

    # ------------------------------------------------------------ input
    def keys(self, *specs):
        for s in specs:
            press(self.q, s)

    def type(self, text):
        type_text(self.q, text)

    def click(self, x, y, button="left"):
        click(self.q, int(x), int(y), W, H, button)

    def tray_icons(self):
        f = self.screen.grab(self.out / ".tray.ppm")
        (self.out / ".tray.ppm").unlink(missing_ok=True)
        return hwlib.tray_icons(f, **TRAY)

    def windows(self):
        rc, out = self.ssh(f"/usr/bin/python3 -I {GUEST_T}/kwin.py list", sess=True, timeout=60)
        rows = [r.split("\t") for r in out.splitlines() if r.count("\t") >= 8]
        return rows

    def qmp(self, cmd, **args):
        return self.qmp_args(cmd, args)

    def qmp_args(self, cmd, args):
        """QMP command with an argument dict (set_link takes "name", which
        the client's cmd(name, **args) cannot pass)."""
        q = self.q
        q.f.write(json.dumps({"execute": cmd, "arguments": args}) + "\n")
        q.f.flush()
        r = q._read()
        if "error" in r:
            raise RuntimeError(f"QMP {cmd}: {r['error']}")
        return r.get("return")

    # ------------------------------------------------------------ the machine
    def boot(self):
        a = self.a
        vars_fd = self.out / "OVMF_VARS.fd"
        vars_fd.write_bytes(Path(OVMF_VARS_MS).read_bytes())
        self.qmp_path = self.out / "qmp.sock"
        self.qmp_path.unlink(missing_ok=True)
        cmd = [
            "qemu-system-x86_64", "-enable-kvm", "-cpu", "host", "-machine", "q35,smm=on",
            "-smp", "4", "-m", "6144",
            "-global", "driver=cfi.pflash01,property=secure,value=on",
            "-drive", f"if=pflash,format=raw,unit=0,readonly=on,file={OVMF_CODE}",
            "-drive", f"if=pflash,format=raw,unit=1,file={vars_fd}",
            "-drive", f"file={a.disk},format=qcow2,if=virtio,discard=unmap",
            "-vga", "none", "-device", f"virtio-vga,xres={W},yres={H}",
            "-device", "qemu-xhci,id=xhci", "-device", "usb-tablet,bus=xhci.0",
            # Sound: Intel HD Audio (ICH9) with a duplex codec, and USB
            # headphones; whatever the guest plays lands in these files.
            "-audiodev", f"wav,id=hda,path={self.out / 'hda.wav'}",
            "-device", "ich9-intel-hda,id=hda0", "-device", "hda-duplex,bus=hda0.0,audiodev=hda",
            "-audiodev", f"wav,id=usbsnd,path={self.out / 'usb-audio.wav'}",
            "-device", "usb-audio,bus=xhci.0,audiodev=usbsnd",
            # The rig's own links (unmanaged in the guest): SSH, and the
            # uplink of the virtual Wi-Fi access point.
            "-netdev", f"user,id=ctl,restrict=on,hostfwd=tcp:127.0.0.1:{SSH_PORT}-10.0.2.15:22",
            "-device", "virtio-net-pci,netdev=ctl,mac=52:54:00:4c:00:01",
            "-netdev", "user,id=apwan",
            "-device", "virtio-net-pci,netdev=apwan,mac=52:54:00:4c:00:02",
            # Empty PCIe slots for hot-plugged network cards and a disk.
            "-device", "pcie-root-port,id=rp1,chassis=1,slot=1,bus=pcie.0",
            "-device", "pcie-root-port,id=rp2,chassis=2,slot=2,bus=pcie.0",
            "-device", "pcie-root-port,id=rp3,chassis=3,slot=3,bus=pcie.0",
            "-device", "virtio-rng-pci",
            "-qmp", f"unix:{self.qmp_path},server=on,wait=off",
            "-display", "none", "-serial", f"file:{self.out / 'serial.log'}",
        ]
        self.say("$ " + " ".join(shlex.quote(c) for c in cmd))
        self.proc = subprocess.Popen(cmd)
        self.q = connect_qmp(self.qmp_path)
        self.screen = Screen(self.q)
        ok, out = self.wait(900, "true")
        self.check("boot.ssh", ok, f"SSH up {time.time() - self.t0:.0f} s after power-on" if ok else f"no SSH: {out}")
        if not ok:
            return False
        rc, out = self.ssh(f"mkdir -p {GUEST_T}")
        self.scp(*(HERE / "guest").glob("*.sh"), HERE.parents[0] / "acceptance" / "guest" / "kwin.py", dest=GUEST_T)
        ok, out = self.wait(600, "pgrep -u lucent -x plasmashell >/dev/null && "
                            "systemctl --user show-environment | grep -q ^WAYLAND_DISPLAY=")
        self.check("boot.desktop", ok, "Plasma session of lucent running (autologin)" if ok else "no Plasma session")
        # Keep the screen on and unlocked while the test works (as a user at the machine).
        self.ssh("systemd-run --user --quiet --collect --unit=hwtest-inhibit -- "
                 "kde-inhibit --power --screenSaver sleep infinity", root=False)
        time.sleep(20)
        return ok

    def stop(self):
        if self.proc and self.proc.poll() is None:
            try:
                self.ssh("systemctl poweroff --no-block", root=True, timeout=20)
                self.proc.wait(timeout=120)
            except Exception:  # noqa: BLE001
                try:
                    self.qmp("quit")
                except (Exception, SystemExit):  # noqa: BLE001
                    pass
                self.proc.wait(timeout=60)

    # ------------------------------------------------------------ sections
    def secure_boot(self):
        _, sb = self.ssh("mokutil --sb-state 2>&1; cat /sys/kernel/security/lockdown 2>&1")
        self.save("secureboot.txt", sb)
        self.check("secureboot.enabled", "SecureBoot enabled" in sb,
                   f"mokutil --sb-state: {sb.splitlines()[0] if sb else '?'}; lockdown: {sb.splitlines()[-1] if sb else '?'}")
        _, kern = self.ssh("journalctl -k -b --no-pager -o short-monotonic | grep -iE "
                           "'secure ?boot|lockdown|integrity: Loaded X.509|Loaded X.509 cert' | head -n 20")
        self.save("secureboot-kernel.txt", kern)
        self.record("secureboot.kernel", "INFO", kern)
        self.signature_failures("boot")
        _, ok = self.ssh("pgrep -u lucent -x plasmashell >/dev/null && echo up")
        self.shot("01-desktop-secure-boot")
        self.check("secureboot.desktop", ok.strip() == "up", "Plasma desktop running with Secure Boot on")

    def signature_failures(self, tag):
        """Modules or firmware that failed to load because of a signature
        (or lockdown), and firmware that failed to load at all."""
        pat = ("module verification failed|Key was rejected|PKCS#7 signature not signed|"
               "Loading of unsigned module|Lockdown: .*(unsigned|module)|"
               "required key not available|firmware: failed to load|Direct firmware load .* failed|"
               "bad shim signature|Invalid signature")
        _, out = self.ssh(f"journalctl -b --no-pager -o short-monotonic | grep -iE '{pat}' | grep -v 'hwtest-grep' ; true",
                          root=True)
        self.save(f"signature-grep-{tag}.txt", f"$ journalctl -b | grep -iE '{pat}'\n{out}\n")
        _, mods = self.ssh("lsmod | sort", root=True)
        self.save(f"lsmod-{tag}.txt", mods)
        self.check(f"secureboot.no-signature-failures-{tag}", not out.strip(),
                   f"journal grep for signature/lockdown/firmware load failures: {out.strip() or 'no matches'}"
                   f" ({len(mods.splitlines()) - 1} modules loaded)")

    def audio(self):
        # PipeWire's view: sinks (outputs) and sources (inputs).
        rc, dump = self.ssh("pw-dump", sess=True, timeout=60)
        nodes = []
        try:
            for o in json.loads(dump[dump.index("["):]):
                p = (o.get("info") or {}).get("props") or {}
                if p.get("media.class") in ("Audio/Sink", "Audio/Source"):
                    nodes.append((p.get("media.class"), p.get("node.name"), p.get("node.description"),
                                  p.get("device.api") or p.get("api.alsa.card.name", "")))
        except (ValueError, json.JSONDecodeError):
            pass
        self.save("pw-dump.json", dump)
        _, st = self.ssh("wpctl status", sess=True, timeout=60)
        self.save("wpctl-status.txt", st)
        sinks = [n for n in nodes if n[0] == "Audio/Sink"]
        sources = [n for n in nodes if n[0] == "Audio/Source" and not (n[1] or "").endswith(".monitor")]
        hda = [n for n in sinks if "usb" not in (n[1] or "").lower()]
        usb = [n for n in sinks if "usb" in (n[1] or "").lower()]
        self.check("audio.sinks", bool(hda) and bool(usb),
                   f"PipeWire sinks: {[n[2] for n in sinks]}")
        self.check("audio.source", bool(sources), f"PipeWire sources: {[n[2] for n in sources]}")
        _, cards = self.ssh("cat /proc/asound/cards; lspci -k -s $(lspci | awk '/Audio/ {print $1; exit}') 2>/dev/null")
        self.record("audio.alsa", "INFO", cards)
        # A tone through each output; the sound card writes what it gets to a WAV on the runner.
        tone = self.out / "tone.wav"
        make_tone(tone, TONE_HZ, 2.0)
        self.scp(tone, dest=GUEST_T)
        for label, group, wav in (("hda", hda, "hda.wav"), ("usb", usb, "usb-audio.wav")):
            if not group:
                self.record(f"audio.tone-{label}", "FAIL", "no such sink")
                continue
            path = self.out / wav
            start = path.stat().st_size if path.exists() else 0
            node = shlex.quote(group[0][1])
            rc, out = self.ssh(f"if command -v pw-play >/dev/null; then pw-play --target {node} {GUEST_T}/tone.wav; "
                               f"else paplay --device={node} {GUEST_T}/tone.wav; fi", sess=True, timeout=60)
            time.sleep(2)
            end = path.stat().st_size if path.exists() else 0
            st = hwlib.wav_stats(path, TONE_HZ, start=start, end=end)
            ok = rc == 0 and not st["silent"] and st["tone_share"] > 0.5 and st["loud_seconds"] >= 1.0
            self.check(f"audio.tone-{label}", ok,
                       f"pw-play 2 s of {TONE_HZ} Hz to '{group[0][2]}' (rc {rc} {out[-120:]}); runner's {wav} "
                       f"grew {end - start} bytes: loud {st['loud_seconds']} s, peak {st['peak_dbfs']} dBFS, "
                       f"{st['tone_share'] * 100:.0f}% of the energy at {TONE_HZ} Hz")
        # The volume keys, as on a laptop keyboard: the OSD and the new volume.
        _, before = self.ssh("wpctl set-volume @DEFAULT_AUDIO_SINK@ 0.5; wpctl get-volume @DEFAULT_AUDIO_SINK@", sess=True)
        self.keys("volumeup")
        time.sleep(0.3)
        self.shot("10-volume-key-osd")
        self.keys("volumeup")
        time.sleep(1)
        _, after = self.ssh("wpctl get-volume @DEFAULT_AUDIO_SINK@", sess=True)
        self.check("audio.volume-key", before.strip() != after.strip() and "Volume" in after,
                   f"default output volume: {before.strip()} -> {after.strip()} after two Volume Up key presses")
        time.sleep(3)

    def tray_probe(self, tag):
        """Click every tray icon in turn and screenshot what opens."""
        icons = self.tray_icons()
        self.record(f"tray.icons-{tag}", "INFO", f"{len(icons)} icons at x={[round(x) for x, _ in icons]}")
        for i, (x, y) in enumerate(icons):
            self.click(x, y)
            time.sleep(1.5)
            self.shot(f"probe-{tag}-{i}")
            wins = [w for w in self.windows() if "plasmashell" in w[1].lower()]
            self.record(f"tray.probe-{tag}-{i}", "INFO", f"x={round(x)}: " + "; ".join(
                f"'{w[0]}' {w[3]},{w[4]} {w[5]}x{w[6]}" for w in wins))
            self.keys("esc")
            time.sleep(1)
        return icons

    def open_tray(self, which):
        """Open a tray applet's popup by clicking its icon. `which` is the
        icon's position from the right of the tray, not counting the
        expander arrow (1 = the rightmost icon)."""
        icons = self.tray_icons()
        if len(icons) < which + 1:
            return None
        x, y = icons[-1 - which]
        self.click(x, y)
        time.sleep(2)
        return x, y

    def usb_sticks(self):
        # The computer's own internal Windows disk (an extra NVMe/SATA-like
        # disk on PCIe): must stay read-only. Plugged in now so the "Move
        # from Windows" assistant does not open at the first login.
        win = self.a.windows_disk
        if win:
            self.qmp("blockdev-add", **{"node-name": "windisk", "driver": "qcow2",
                                        "file": {"driver": "file", "filename": str(win)}})
            self.qmp("device_add", driver="virtio-blk-pci", drive="windisk", id="windisk0", bus="rp3")
            ok, _ = self.wait(30, "test -e /dev/disk/by-label/Windows")
            time.sleep(3)
            rc, out = self.ssh("udisksctl mount -b /dev/disk/by-label/Windows; m=$(findmnt -n -o TARGET -S LABEL=Windows); "
                               "echo OPTIONS: $(findmnt -n -o OPTIONS -S LABEL=Windows); touch \"$m/x\"; "
                               "udevadm info -q property /dev/disk/by-label/Windows | grep ^UDISKS", sess=True)
            self.save("ntfs-internal.txt", out)
            opts = re.search(r"OPTIONS: (\S*)", out)
            ro = bool(opts) and "ro" in opts[1].split(",")
            self.check("ntfs.internal-windows-disk-read-only", ok and ro and "Read-only file system" in out,
                       f"internal NTFS 'Windows' (virtio-blk on PCIe), mounted by the user's session: {out}")
            self.ssh("udisksctl unmount -b /dev/disk/by-label/Windows", sess=True)
        sticks = [("fat32", "LUCENTFAT32"), ("exfat", "LucentExFAT"), ("ntfs", "LucentNTFS")]
        for n, (fs, label) in enumerate(sticks):
            img = Path(self.a.sticks) / f"stick-{fs}.img"
            self.qmp("blockdev-add", **{"node-name": f"stick{n}", "driver": "raw",
                                        "file": {"driver": "file", "filename": str(img)}})
            self.qmp("device_add", driver="usb-storage", drive=f"stick{n}", id=f"stick{n}", bus="xhci.0",
                     removable=True, serial=f"LUCENT{n:04d}")
            ok, _ = self.wait(30, f"test -e /dev/disk/by-label/{label}")
            time.sleep(1.5)
            self.shot(f"20-usb-{fs}-plugged")
            self.check(f"usb.{fs}.detected", ok, f"/dev/disk/by-label/{label} appeared after plugging the {fs} stick")
            if not ok:
                continue
            _, info = self.ssh(f"dev=$(readlink -f /dev/disk/by-label/{label}); echo $dev; "
                               f"udevadm info -q property $dev | grep -E '^(ID_BUS|ID_FS_TYPE|ID_FS_LABEL|UDISKS)='; "
                               f"lsblk -no TRAN,RM,HOTPLUG /dev/$(lsblk -no PKNAME $dev)")
            self.save(f"usb-{fs}-udev.txt", info)
            self.check(f"usb.{fs}.not-read-only-rule", "UDISKS_MOUNT_OPTIONS_DEFAULTS=ro" not in info,
                       f"udev: {info}")
            _, auto = self.ssh(f"findmnt -n -o TARGET,OPTIONS -S LABEL={label}; true")
            self.record(f"usb.{fs}.automount", "INFO",
                        f"mounted on plug-in: {auto.strip() or 'no (mounted when opened)'}")
            # It shows up in Files' This PC with its label.
            rc, ls = self.ssh("for e in $(kioclient ls thispc:/ | grep '^drive-'); do "
                              "echo \"$e: $(kioclient stat thispc:/$e 2>&1 | grep -iE 'name' | head -n 3 | tr '\\n' ' ')\"; done",
                              sess=True, timeout=60)
            self.save(f"usb-{fs}-thispc.txt", ls)
            self.check(f"usb.{fs}.this-pc", label in ls, f"thispc:/ lists: {ls}")
            if n == 0:
                self.keys("meta-e")
                time.sleep(5)
                self.shot(f"21-usb-{fs}-this-pc")
                self.keys("alt-f4")
                time.sleep(1)
            # Mount as the user's session does (Dolphin -> udisks), read, write.
            rc, out = self.ssh(
                f"set -e; dev=$(readlink -f /dev/disk/by-label/{label}); "
                f"findmnt -S $dev >/dev/null || udisksctl mount -b $dev; "
                f"m=$(findmnt -n -o TARGET -S $dev); findmnt -n -o SOURCE,FSTYPE,OPTIONS -S $dev; "
                f"echo READ: $(cat \"$m/hello.txt\"); "
                f"printf 'Lucent wrote this on the {fs} stick\\n' > \"$m/written-by-lucent.txt\"; "
                f"head -c 4194304 /dev/urandom > \"$m/random-4M.bin\"; sha256sum \"$m/random-4M.bin\" | cut -c1-16; "
                f"sync; echo BACK: $(cat \"$m/written-by-lucent.txt\")", sess=True, timeout=120)
            self.save(f"usb-{fs}-mount.txt", out)
            self.check(f"usb.{fs}.read", f"Hello from a {fs} stick" in out, out)
            self.check(f"usb.{fs}.write", rc == 0 and f"BACK: Lucent wrote this on the {fs} stick" in out,
                       f"rc {rc}: {out}")
            if fs == "ntfs":
                self.ntfs_enclosure_check(label)
            # Safely remove: what the Eject action on This PC runs.
            rc, out = self.ssh(f"m=$(findmnt -n -o TARGET -S LABEL={label}); /usr/libexec/lucent/thispc-eject \"$m\"; "
                               f"echo rc=$?; sleep 1; lsblk -no NAME,MOUNTPOINTS 2>/dev/null | grep -c . ", sess=True)
            time.sleep(1)
            self.shot(f"22-usb-{fs}-ejected")
            _, gone = self.ssh(f"test -e /dev/disk/by-label/{label} && echo still-there || echo gone")
            self.check(f"usb.{fs}.eject", "rc=0" in out and "gone" in gone,
                       f"thispc-eject: {out.splitlines()[0] if out else '?'}; device {gone.strip()}")
            self.qmp("device_del", id=f"stick{n}")
            time.sleep(3)
            try:
                self.qmp("blockdev-del", **{"node-name": f"stick{n}"})
            except (Exception, SystemExit) as e:  # noqa: BLE001
                self.say(f"blockdev-del stick{n}: {e}")

    def ntfs_enclosure_check(self, label):
        """A USB hard disk in a SATA enclosure gets ID_BUS=ata from ata_id
        (QEMU's USB stick can't answer ata_id, so it is simulated with a
        runtime rule). Is it still writable under the shipped rule, and
        under the repo's rule?"""
        fake = (f'SUBSYSTEM=="block", ENV{{ID_FS_LABEL}}=="{label}", ENV{{ID_BUS}}="ata"\n')
        script = (f"set -u; echo '{fake.strip()}' > /run/udev/rules.d/61-hwtest-fake-ata.rules; "
                  f"udevadm control --reload; dev=$(readlink -f /dev/disk/by-label/{label}); "
                  f"udevadm test --action=add $dev 2>&1 | grep -oE '(ID_BUS|UDISKS_MOUNT_OPTIONS_DEFAULTS)=[a-z]+' | sort -u; true")
        _, shipped = self.ssh(script, root=True)
        repo = ""
        if self.a.repo_rule:
            self.scp(self.a.repo_rule, dest=f"{GUEST_T}/99-lucent-windows-readonly.rules")
            _, repo = self.ssh(f"cp {GUEST_T}/99-lucent-windows-readonly.rules /run/udev/rules.d/; " + script, root=True)
        self.ssh("rm -f /run/udev/rules.d/61-hwtest-fake-ata.rules /run/udev/rules.d/99-lucent-windows-readonly.rules; "
                 "udevadm control --reload", root=True)
        self.save("ntfs-usb-enclosure.txt", f"shipped rule:\n{shipped}\n\nrepo rule:\n{repo}\n")
        self.record("ntfs.usb-sata-enclosure-shipped-rule",
                    "INFO" if "UDISKS_MOUNT_OPTIONS_DEFAULTS=ro" not in shipped else "FAIL" if not repo else "INFO",
                    f"USB NTFS disk with ID_BUS=ata (as ata_id reports a SATA enclosure), image's rule: "
                    f"{'read-only' if 'UDISKS_MOUNT_OPTIONS_DEFAULTS=ro' in shipped else 'writable'} ({shipped})")
        if repo:
            self.check("ntfs.usb-sata-enclosure-repo-rule", "ID_BUS=ata" in repo and "UDISKS_MOUNT_OPTIONS_DEFAULTS=ro" not in repo,
                       f"same disk, this commit's rule: "
                       f"{'read-only' if 'UDISKS_MOUNT_OPTIONS_DEFAULTS=ro' in repo else 'writable'} ({repo})")

    def bluetooth(self):
        tools = Path(self.a.tools)
        self.scp(tools / "bin" / "btvirt", dest=f"{GUEST_T}/btvirt")
        before = [round(x) for x, _ in self.tray_icons()]
        rc, out = self.ssh(f"modprobe hci_vhci && modinfo -F signer hci_vhci; chmod +x {GUEST_T}/btvirt; "
                           f"setsid -f {GUEST_T}/btvirt -l2 > {GUEST_T}/btvirt.log 2>&1 < /dev/null; sleep 5; "
                           f"systemctl is-active bluetooth.service; bluetoothctl list", root=True)
        ctrls = re.findall(r"Controller ((?:[0-9A-F]{2}:){5}[0-9A-F]{2})", out)
        self.check("bluetooth.adapter", len(ctrls) >= 1, f"hci_vhci + btvirt -l2: {out}")
        if not ctrls:
            return
        time.sleep(4)
        self.shot("30-bluetooth-adapter-in-tray")
        after = self.tray_icons()
        _, show = self.ssh("bluetoothctl show | head -n 12", root=True)
        self.save("bluetooth-show.txt", show)
        # The new tray icon is Bluetooth's (icons right of it shift left).
        bt = after[-len(before) - 1] if len(after) == len(before) + 1 else None
        self.check("bluetooth.tray-icon", bt is not None,
                   f"tray icons x={before} before the adapter, x={[round(x) for x, _ in after]} after")
        if bt:
            self.click(*bt)
            time.sleep(2)
            self.shot("31-bluetooth-popup")
            # The popup's on/off switch: its toolbar's first control, where
            # the network popup has its Wi-Fi switch.
            pops = [w for w in self.windows() if "plasmashell" in w[1].lower() and int(w[5]) > 300 and int(w[6]) > 300]
            if pops:
                x, y = int(pops[0][3]), int(pops[0][4])
                states = []
                for i in (1, 2):
                    self.click(x + 32, y + 65)
                    time.sleep(3)
                    _, st = self.ssh(f"bluetoothctl show {ctrls[0]} | grep -m1 'Powered:'", root=True)
                    states.append(st.strip())
                    self.shot(f"32-bluetooth-switch-{i}")
                self.check("bluetooth.power-switch", states == ["Powered: no", "Powered: yes"],
                           f"clicked the popup's switch twice: {states}")
            self.keys("esc")
            time.sleep(1)
        # Pair the computer's adapter with the second controller as a nearby device.
        if len(ctrls) >= 2:
            rc, out = self.ssh(f"bash {GUEST_T}/bt-pair.sh {ctrls[0]} {ctrls[1]}", root=True, timeout=120)
            self.save("bluetooth-pair.txt", out)
            clean = re.sub(r"\x1b\[[0-9;]*m", "", out)
            paired = re.search(r"Paired: yes", clean) is not None
            self.check("bluetooth.pair", paired, f"bluetoothctl pair {ctrls[1]} from {ctrls[0]}: " + "; ".join(
                ln.strip() for ln in clean.splitlines()
                if re.search(r"Pair|pair|Fail|Bonded|Confirm|auth", ln) and "bluetoothctl]>" not in ln)[:700])
            if bt:
                self.click(*bt)
                time.sleep(2)
                self.shot("33-bluetooth-paired-device")
                self.keys("esc")
                time.sleep(1)

    def wifi(self):
        tools = Path(self.a.tools)
        self.ssh(f"mkdir -p {GUEST_T}/rpms {GUEST_T}/bin")
        self.scp(*(tools / "rpms").glob("*.rpm"), dest=f"{GUEST_T}/rpms/")
        self.scp(tools / "bin" / "hostapd", tools / "bin" / "dnsmasq", dest=f"{GUEST_T}/bin/")
        rc, out = self.ssh(f"chmod +x {GUEST_T}/bin/*; bash {GUEST_T}/install-test-rpms.sh {GUEST_T}/rpms 2>&1 | tail -n 12",
                           root=True, timeout=600)
        self.save("wifi-install-test-rpms.txt", out)
        self.record("wifi.hwsim-installed", "INFO", f"test VM only, transient /usr overlay: {out[-500:]}")
        rc, out = self.ssh(f"bash {GUEST_T}/wifi-ap.sh {shlex.quote(WIFI_SSID)} {WIFI_PSK} 2>&1", root=True, timeout=120)
        self.save("wifi-ap.txt", out)
        if not self.check("wifi.access-point", rc == 0, out[-600:]):
            return
        ok, out = self.wait(60, f"nmcli -t -f SSID dev wifi list --rescan yes | grep -qx {shlex.quote(WIFI_SSID)}")
        _, lst = self.ssh("nmcli -f IN-USE,SSID,SECURITY,SIGNAL,DEVICE dev wifi list")
        self.check("wifi.scan", ok, f"NetworkManager sees: {lst}")
        _, dev = self.ssh("nmcli -t -f DEVICE,TYPE,STATE dev | awk -F: '$2==\"wifi\"{print $1; exit}'")
        wdev = dev.strip()
        _, drv = self.ssh(f"basename $(readlink -f /sys/class/net/{wdev}/device/driver)")
        self.record("wifi.device", "INFO", f"{wdev}, driver {drv.strip()}")
        # The user: tray -> network list -> the network -> password -> Enter.
        self.shot("40-wifi-before")
        xy = self.open_tray(1)
        self.shot("41-wifi-network-list")
        wins = [w for w in self.windows() if "plasmashell" in w[1].lower()]
        self.record("wifi.popup", "INFO", f"clicked tray icon at {xy}; plasmashell windows: " +
                    "; ".join(f"'{w[0]}' {w[3]},{w[4]} {w[5]}x{w[6]}" for w in wins))
        gui = self.wifi_gui_connect(wins)
        ok, _ = self.wait(60, f"nmcli -t -f GENERAL.STATE dev show {wdev} | grep -q '100 '")
        self.shot("43-wifi-connected-popup")
        self.keys("esc")
        time.sleep(1)
        self.shot("44-wifi-connected-tray")
        _, con = self.ssh(f"nmcli -f GENERAL.CONNECTION,GENERAL.STATE,IP4.ADDRESS,IP4.GATEWAY dev show {wdev}; "
                          f"nmcli -f connection.id,802-11-wireless-security.psk-flags con show {shlex.quote(WIFI_SSID)} 2>&1")
        self.check("wifi.connect-from-tray", ok and gui, f"{'GUI flow done' if gui else 'GUI flow did not finish'}; {con}")
        if not ok:
            rc, out = self.ssh(f"nmcli dev wifi connect {shlex.quote(WIFI_SSID)} password {WIFI_PSK} ifname {wdev}",
                               sess=True, timeout=90)
            self.record("wifi.connect-cli-fallback", "INFO", f"nmcli fallback (not what the user does): rc {rc} {out}")
        _, net = self.ssh(f"nmcli networking connectivity check; curl -sS -o /dev/null -w '%{{http_code}} via %{{local_ip}}' "
                          f"--interface {wdev} --max-time 20 https://fedoraproject.org/", root=True)
        self.check("wifi.internet", re.search(r"\b(200|30\d) via 192\.168\.77\.", net) is not None,
                   f"connectivity, curl over {wdev}: {net}")
        _, kw = self.ssh("pgrep -a -u lucent -f 'kwalletd|ksecretd' ; true")
        self.record("wifi.secret-store", "INFO", f"wallet processes: {kw.strip() or 'none'}")

    def wifi_gui_connect(self, wins):
        """Find 'Lucent Test' in the open popup and connect: click its row,
        type the password, Enter. Returns True when the steps ran."""
        pops = [w for w in wins if int(w[5]) > 300 and int(w[6]) > 300]
        if not pops:
            self.record("wifi.gui", "INFO", "no tray popup window found")
            return False
        x, y, w, h = (int(v) for v in pops[0][3:7])
        # Plasma's network popup (452 px wide at 1080p): title, a toolbar
        # with the Wi-Fi switch and the search field, "Available", then the
        # first network's row 140 px below the popup's top, with its
        # "Connect" button 100 px from the right edge (41-wifi-network-list).
        self.click(x + w - 102, y + 140)
        time.sleep(2.5)
        self.shot("42b-wifi-password-field")
        self.type(WIFI_PSK)
        time.sleep(0.5)
        self.shot("42c-wifi-password-typed")
        self.keys("ret")
        time.sleep(6)
        return True

    def ethernet(self):
        nics = [("e1000e", "pcie", "user", "rp1", "52:54:00:4c:01:01"),
                ("usb-net", "usb", "user", None, "52:54:00:4c:01:03"),
                ("igb", "pcie", "tap", "rp2", "52:54:00:4c:01:02")]
        self.ssh("nmcli radio wifi off", root=True)
        time.sleep(3)
        for model, kind, net, bus, mac in nics:
            nid = f"net-{model}"
            if net == "tap":
                self.qmp("netdev_add", type="tap", id=nid, ifname="lucenttap0", script="no", downscript="no")
            else:
                self.qmp("netdev_add", type="user", id=nid)
            args = dict(driver=model, netdev=nid, id=f"nic-{model}", mac=mac)
            if bus:
                args["bus"] = bus
            else:
                args["bus"] = "xhci.0"
            self.qmp("device_add", **args)
            find = (f"for i in /sys/class/net/*; do [ \"$(cat $i/address)\" = {mac} ] && echo ${{i##*/}}; done")
            ok, ifname = self.wait(30, f"i=$({find}); test -n \"$i\" && echo $i")
            ifname = ifname.strip()
            ok2, _ = self.wait(60, f"nmcli -t -f GENERAL.STATE dev show {ifname} | grep -q '100 '")
            _, info = self.ssh(f"basename $(readlink -f /sys/class/net/{ifname}/device/driver); "
                               f"nmcli -f GENERAL.CONNECTION,IP4.ADDRESS,IP4.GATEWAY dev show {ifname}; "
                               f"curl -sS -o /dev/null -w 'curl: %{{http_code}} via %{{local_ip}}' --interface {ifname} "
                               f"--max-time 20 https://fedoraproject.org/")
            self.save(f"eth-{model}.txt", info)
            self.check(f"ethernet.{model}", ok and ok2 and re.search(r"curl: (200|30\d)", info) is not None,
                       f"{ifname}: {info}")
            time.sleep(2)
            self.open_tray(1)
            self.shot(f"50-ethernet-{model}-tray")
            self.keys("esc")
            time.sleep(1)
            if model == "igb":
                self.printing(ifname)
            self.qmp("set_link", name=f"nic-{model}", up=False)
            time.sleep(3)

    def printing(self, ifname):
        ok, out = self.wait(120, "lpstat -e | grep -i lucent", sess=True)
        _, all_ = self.ssh("lpstat -e; avahi-browse -rtp _ipp._tcp 2>/dev/null | head -n 5", sess=True)
        self.save("printing-discovery.txt", all_)
        self.check("printing.discovered", ok, f"lpstat -e (CUPS, DNS-SD): {all_}")
        if not ok:
            return
        dest = out.strip().splitlines()[0]
        spool = Path(self.a.spool)
        before = set(spool.rglob("*"))
        self.ssh(f"printf 'Lucent OS hardware test page\\n\\nPrinted over {ifname}.\\n' > {GUEST_T}/page.txt")
        rc, out = self.ssh(f"lp -d {shlex.quote(dest)} -t 'Lucent test page' {GUEST_T}/page.txt", sess=True)
        got = []
        for _ in range(60):
            got = [p for p in set(spool.rglob("*")) - before if p.is_file()]
            if got:
                break
            time.sleep(2)
        self.check("printing.cli-job", bool(got), f"lp -d {dest}: {out}; printer received: "
                   f"{[(p.name, p.stat().st_size) for p in got]}")
        # A KDE app's print dialog, if KWrite is in the image.
        rc, kw = self.ssh("command -v kwrite")
        if rc != 0:
            self.record("printing.kde-app", "INFO", "no KWrite in the image; printed from the command line only")
            return
        self.ssh(f"setsid -f kwrite {GUEST_T}/page.txt", sess=True)
        time.sleep(6)
        self.keys("ctrl-p")
        time.sleep(4)
        self.shot("60-print-dialog")
        before = set(spool.rglob("*"))
        self.keys("ret")
        got = []
        for _ in range(45):
            got = [p for p in set(spool.rglob("*")) - before if p.is_file()]
            if got:
                break
            time.sleep(2)
        self.shot("61-after-print")
        self.check("printing.kde-app", bool(got), f"KWrite > Ctrl+P > Enter: printer received "
                   f"{[(p.name, p.stat().st_size) for p in got]}")
        self.keys("ctrl-q")
        time.sleep(2)

    def inventory(self):
        _, out = self.ssh("rpm -qa --qf '%{NAME}\\n' | grep -E 'firmware|^kernel|bluez|pipewire|wpa_supplicant|"
                          "NetworkManager|cups|sane|fwupd|exfat|ntfs|alsa' | sort", root=True)
        self.save("packages-hardware.txt", out)
        for cmd, name in (("lspci -k", "lspci.txt"), ("lsusb -t; lsusb", "lsusb.txt"),
                          ("journalctl -b --no-pager -o short-monotonic", "journal.txt"),
                          ("dmesg", "dmesg.txt"), ("systemctl list-units --failed --no-pager", "failed-units.txt"),
                          ("ausearch -m AVC,USER_AVC --start boot 2>&1 | tail -n 200", "avc.txt")):
            _, o = self.ssh(cmd, root=True, timeout=120)
            self.save(name, o)

    # ------------------------------------------------------------ main
    def run(self):
        try:
            if not self.boot():
                return 1
            for name, fn in (("secureboot", self.secure_boot), ("audio", self.audio),
                             ("tray", lambda: self.tray_probe("start")), ("usb", self.usb_sticks),
                             ("bluetooth", self.bluetooth), ("wifi", self.wifi), ("ethernet", self.ethernet),
                             ("final", lambda: self.signature_failures("end")), ("inventory", self.inventory)):
                self.say(f"=== {name}")
                try:
                    fn()
                except Exception as e:  # noqa: BLE001
                    self.record(f"{name}.error", "FAIL", f"{type(e).__name__}: {e}")
                    self.shot(f"error-{name}")
        finally:
            self.stop()
            self.summary()
        return 1 if any(s == "FAIL" for _, s, _ in self.results) else 0

    def summary(self):
        icon = {"PASS": "✅", "FAIL": "❌", "INFO": "ℹ️"}
        lines = ["# Hardware-live test (x86_64, QEMU/KVM, Secure Boot)", "",
                 "| | check | detail |", "| --- | --- | --- |"]
        for cid, st, d in self.results:
            lines.append(f"| {icon.get(st, st)} | {cid} | {d.replace('|', '/')[:500]} |")
        (self.out / "summary.md").write_text("\n".join(lines) + "\n")


def make_tone(path, freq, seconds, rate=48000):
    import math
    import struct
    import wave
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(rate)
        frames = bytearray()
        for i in range(int(seconds * rate)):
            v = int(0.5 * 32767 * math.sin(2 * math.pi * freq * i / rate))
            frames += struct.pack("<hh", v, v)
        w.writeframes(bytes(frames))


def sticks_verdict(a):
    """After the run: the runner reads the ejected stick images back
    (runner/sticks.sh check) - the file the computer wrote, a clean file
    system. Adds those checks and rewrites the summary."""
    t = Test(a)
    t.log = open(os.devnull, "w")
    for line in Path(t.out / "results.tsv").read_text().splitlines() if (t.out / "results.tsv").exists() else []:
        cid, st, d = (line.split("\t") + ["", ""])[:3]
        t.results.append((cid, st, d))
    for line in Path(a.sticks_verdict).read_text().splitlines():
        fs, written, clean = (line.split("\t") + ["", ""])[:3]
        ok_w = written.startswith(f"Lucent wrote this on the {fs} stick")
        ok_c = clean.startswith("rc=0 ") and not re.search(r"dirty|corrupt", clean, re.I)
        t.check(f"usb.{fs}.file-on-stick-after-eject", ok_w, f"runner mounted the ejected image: '{written}'")
        t.check(f"usb.{fs}.clean-after-eject", ok_c, f"runner's fsck of the ejected image: {clean}")
    t.summary()
    return 1 if any(s == "FAIL" for _, s, _ in t.results) else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--sticks-verdict", help="runner/sticks.sh check output: add those checks, rewrite the summary")
    ap.add_argument("--disk")
    ap.add_argument("--key")
    ap.add_argument("--tools")
    ap.add_argument("--sticks")
    ap.add_argument("--windows-disk")
    ap.add_argument("--spool")
    ap.add_argument("--repo-rule")
    a = ap.parse_args()
    if a.sticks_verdict:
        sys.exit(sticks_verdict(a))
    sys.exit(Test(a).run())


if __name__ == "__main__":
    main()
