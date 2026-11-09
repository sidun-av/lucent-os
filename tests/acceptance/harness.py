#!/usr/bin/env python3
"""Host side of the Lucent OS acceptance test (CI, x86_64, QEMU/KVM).

  harness.py install --iso ISO --disk DISK --vars VARS --log LOG [--timeout S]
      Unattended Anaconda install of the (test copy of the) ISO, no network.
  harness.py run --disk DISK --vars VARS --payload IMG --out DIR [--timeout S]
      Boot the installed disk, no network, and serve the guest's requests.

The guest side (guest/acceptance.sh) drives the test from inside the
installed system and talks to this harness over a virtio-serial port, one
request per line, one reply line each:

  SHOT name            QMP screendump -> DIR/screens/name.png
  KEYS combo...        key chords through QEMU's keyboard (e.g. meta, ret, alt-f4)
  TYPE text            type text through QEMU's keyboard
  CLICK x y [button]   absolute pointer (usb-tablet) click at screen pixel x,y
  RESULT/METRIC/LOG …  progress lines, echoed to the CI log
  DONE rc              the guest is finished (it then powers off)

So everything "the user does" arrives as real input through KWin, and every
screenshot is what the virtual screen shows.
"""
import argparse
import json
import os
import select
import socket
import struct
import subprocess
import sys
import tempfile
import time
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "vm"))
from qmp import PLAIN, QMP, SHIFTED, combo  # noqa: E402  (tools/vm/qmp.py)

OVMF_CODE = "/usr/share/OVMF/OVMF_CODE_4M.fd"


def qemu_base(vars_fd, disk, mem=8192):
    return [
        "qemu-system-x86_64", "-enable-kvm", "-cpu", "host", "-machine", "q35",
        "-smp", "4", "-m", str(mem),
        "-drive", f"if=pflash,format=raw,readonly=on,file={OVMF_CODE}",
        "-drive", f"if=pflash,format=raw,file={vars_fd}",
        "-drive", f"file={disk},format=raw,if=virtio",
        "-nic", "none",
    ]


# ---------------------------------------------------------------- images
def ppm_to_png(src, dst):
    """Convert a binary PPM (P6, maxval 255) to PNG with the standard library."""
    data = Path(src).read_bytes()
    tokens, i = [], 2
    while len(tokens) < 3:
        while data[i:i + 1].isspace():
            i += 1
        if data[i:i + 1] == b"#":
            i = data.index(b"\n", i) + 1
            continue
        j = i
        while not data[j:j + 1].isspace():
            j += 1
        tokens.append(int(data[i:j]))
        i = j
    w, h, _ = tokens
    pix = data[i + 1:]
    raw = b"".join(b"\x00" + pix[y * w * 3:(y + 1) * w * 3] for y in range(h))

    def chunk(kind, body):
        c = kind + body
        return struct.pack(">I", len(body)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    Path(dst).write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 6))
        + chunk(b"IEND", b"")
    )
    return w, h


def png_size(path):
    head = Path(path).read_bytes()[:24]
    return struct.unpack(">II", head[16:24])


class Screen:
    def __init__(self, q):
        self.q = q
        self.png = None  # does this QEMU write PNG itself?

    def dump(self, path):
        path = Path(path)
        if self.png is not False:
            try:
                self.q.cmd("screendump", filename=str(path), format="png")
                self.png = True
                return png_size(path)
            except SystemExit:
                self.png = False
        with tempfile.NamedTemporaryFile(suffix=".ppm", dir=path.parent, delete=False) as t:
            ppm = t.name
        try:
            self.q.cmd("screendump", filename=ppm)
            return ppm_to_png(ppm, path)
        finally:
            os.unlink(ppm)

    def size(self, scratch):
        return self.dump(Path(scratch) / ".size.png")


# ---------------------------------------------------------------- input
def key_event(q, key, down):
    q.cmd("input-send-event", events=[{"type": "key", "data": {"down": down, "key": key}}])


def press(q, spec):
    """One chord: modifiers first, hold, release in reverse (tools/vm/qmp.py)."""
    spec, _, hold = spec.partition(":")
    keys = combo(spec)
    for k in keys:
        key_event(q, k, True)
        time.sleep(0.08)
    time.sleep(int(hold or 120) / 1000)
    for k in reversed(keys):
        key_event(q, k, False)
        time.sleep(0.03)
    time.sleep(0.4)


def type_text(q, text):
    for ch in text:
        if ch.isupper():
            names = ["shift", ch.lower()]
        elif ch in SHIFTED:
            names = ["shift", SHIFTED[ch]]
        else:
            names = [PLAIN.get(ch, ch)]
        keys = [{"type": "qcode", "data": n} for n in names]
        for k in keys:
            key_event(q, k, True)
            time.sleep(0.03)
        time.sleep(0.05)
        for k in reversed(keys):
            key_event(q, k, False)
        time.sleep(0.08)


def click(q, x, y, w, h, button="left"):
    q.cmd("input-send-event", events=[
        {"type": "abs", "data": {"axis": "x", "value": x * 32767 // (w - 1)}},
        {"type": "abs", "data": {"axis": "y", "value": y * 32767 // (h - 1)}},
    ])
    time.sleep(0.2)
    for down in (True, False):
        q.cmd("input-send-event", events=[{"type": "btn", "data": {"down": down, "button": button}}])
        time.sleep(0.08)


# ---------------------------------------------------------------- commands
def connect_unix(path, timeout=60):
    deadline = time.time() + timeout
    while True:
        try:
            s = socket.socket(socket.AF_UNIX)
            s.connect(str(path))
            return s
        except OSError:
            if time.time() > deadline:
                raise
            time.sleep(0.2)


def connect_qmp(path, timeout=60):
    deadline = time.time() + timeout
    while True:
        try:
            return QMP(str(path))
        except OSError:
            if time.time() > deadline:
                raise
            time.sleep(0.2)


def install(a):
    cmd = qemu_base(a.vars, a.disk) + [
        "-drive", f"file={a.iso},media=cdrom,readonly=on",
        "-boot", "order=d", "-display", "none", "-no-reboot",
        "-serial", f"file:{a.log}",
    ]
    print("$", " ".join(cmd), flush=True)
    start = time.time()
    try:
        rc = subprocess.run(cmd, timeout=a.timeout).returncode
    except subprocess.TimeoutExpired:
        print(f"install did not finish in {a.timeout} s", flush=True)
        return 1
    print(f"install took {time.time() - start:.0f} s (qemu exit {rc})", flush=True)
    log = Path(a.log).read_text(errors="replace")
    ok = "default apps installed from the install media" in log
    print("offline apps unpacked by the installer:", "yes" if ok else "NO", flush=True)
    return 0 if rc == 0 and ok else 1


def run(a):
    out = Path(a.out)
    shots, timeline = out / "screens", out / "timeline"
    for d in (shots, timeline):
        d.mkdir(parents=True, exist_ok=True)
    ctl_path, qmp_path = out / "ctl.sock", out / "qmp.sock"
    for p in (ctl_path, qmp_path):
        p.unlink(missing_ok=True)
    cmd = qemu_base(a.vars, a.disk) + [
        "-drive", f"file={a.payload},format=raw,if=virtio",
        "-vga", "none", "-device", f"virtio-vga,xres={a.width},yres={a.height}",
        "-device", "qemu-xhci", "-device", "usb-tablet",
        "-device", "virtio-serial-pci",
        "-chardev", f"socket,id=ctl,path={ctl_path},server=on,wait=off",
        "-device", "virtserialport,chardev=ctl,name=org.lucent.acceptance",
        "-qmp", f"unix:{qmp_path},server=on,wait=off",
        "-display", "none", "-serial", f"file:{out / 'serial-boot.log'}",
    ]
    print("$", " ".join(cmd), flush=True)
    log = open(out / "harness.log", "a", buffering=1)

    def say(msg):
        line = f"[{time.time() - t0:7.1f}] {msg}"
        print(line, flush=True)
        log.write(line + "\n")

    t0 = time.time()
    proc = subprocess.Popen(cmd)
    q = connect_qmp(qmp_path)
    screen = Screen(q)
    ctl = connect_unix(ctl_path)
    say("QEMU started, control channel connected")
    buf, done, timed_out, last_tl = b"", None, False, 0.0

    def handle(line):
        nonlocal done
        verb, _, rest = line.partition(" ")
        if verb == "SHOT":
            name = "".join(c for c in rest if c.isalnum() or c in "-_.") or "shot"
            w, h = screen.dump(shots / f"{name}.png")
            say(f"screenshot {name}.png ({w}x{h})")
            return "OK"
        if verb == "KEYS":
            for spec in rest.split():
                press(q, spec)
            return "OK"
        if verb == "TYPE":
            type_text(q, rest)
            return "OK"
        if verb == "CLICK":
            parts = rest.split()
            w, h = screen.size(out)
            click(q, int(parts[0]), int(parts[1]), w, h, parts[2] if len(parts) > 2 else "left")
            return f"OK {w}x{h}"
        if verb in ("RESULT", "METRIC", "LOG"):
            say(f"{verb.lower()}: {rest}")
            return "OK"
        if verb == "DONE":
            done = int(rest or 1)
            say(f"guest finished (rc {done})")
            return "OK"
        return "ERR unknown request"

    done_at = None
    while proc.poll() is None:
        now = time.time()
        if now - t0 > a.timeout:
            timed_out = True
            say(f"TIMEOUT after {a.timeout} s")
            try:
                screen.dump(timeline / "timeout.png")
            except Exception as e:  # noqa: BLE001
                say(f"timeout screenshot failed: {e}")
            break
        if now - last_tl >= 60:
            last_tl = now
            try:
                screen.dump(timeline / f"t{int(now - t0):05d}.png")
            except Exception as e:  # noqa: BLE001
                say(f"timeline screenshot failed: {e}")
        if done is not None:
            done_at = done_at or now
            if now - done_at > 180:
                say("guest did not power off; quitting QEMU")
                break
        r, _, _ = select.select([ctl], [], [], 1.0)
        if not r:
            continue
        data = ctl.recv(65536)
        if not data:
            say("control channel closed")
            break
        buf += data
        while b"\n" in buf:
            raw, buf = buf.split(b"\n", 1)
            line = raw.decode("utf-8", "replace").strip()
            if not line:
                continue
            try:
                reply = handle(line)
            except (Exception, SystemExit) as e:  # noqa: BLE001
                reply = f"ERR {e}"
                say(f"request '{line}' failed: {e}")
            ctl.sendall((reply + "\n").encode())
    if proc.poll() is None:
        try:
            q.cmd("quit")
        except (Exception, SystemExit):  # noqa: BLE001
            pass
        try:
            proc.wait(timeout=60)
        except subprocess.TimeoutExpired:
            proc.kill()
    state = {"guest_done": done is not None, "guest_rc": done, "timed_out": timed_out,
             "seconds": round(time.time() - t0)}
    (out / "harness.json").write_text(json.dumps(state, indent=1) + "\n")
    say(f"harness: {state}")
    return 0 if done == 0 and not timed_out else 1


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("install")
    i.add_argument("--iso", required=True)
    i.add_argument("--disk", required=True)
    i.add_argument("--vars", required=True)
    i.add_argument("--log", required=True)
    i.add_argument("--timeout", type=int, default=75 * 60)
    r = sub.add_parser("run")
    r.add_argument("--disk", required=True)
    r.add_argument("--vars", required=True)
    r.add_argument("--payload", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--timeout", type=int, default=60 * 60)
    r.add_argument("--width", type=int, default=1920)
    r.add_argument("--height", type=int, default=1080)
    a = ap.parse_args()
    sys.exit(install(a) if a.cmd == "install" else run(a))


if __name__ == "__main__":
    main()
