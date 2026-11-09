"""Minimal QMP client: qmp.py SOCKET COMMAND [JSON-ARGS]  |  SOCKET keys COMBO...  |  SOCKET type TEXT"""
import json
import socket
import sys
import time

ALIASES = {"meta": "meta_l", "win": "meta_l", "super": "meta_l", "enter": "ret",
           "space": "spc", "escape": "esc", "pgup": "pgup", "pgdn": "pgdn",
           "backspace": "backspace", "del": "delete"}
SHIFTED = {"!": "1", "@": "2", "#": "3", "$": "4", "%": "5", "^": "6", "&": "7",
           "*": "8", "(": "9", ")": "0", "_": "minus", "+": "equal", ":": "semicolon",
           "?": "slash", ">": "dot", "<": "comma", '"': "apostrophe"}
PLAIN = {" ": "spc", "-": "minus", "=": "equal", ".": "dot", ",": "comma", "/": "slash",
         ";": "semicolon", "'": "apostrophe", "\n": "ret"}


class QMP:
    def __init__(self, path):
        self.s = socket.socket(socket.AF_UNIX)
        self.s.connect(path)
        self.f = self.s.makefile("rw")
        self._read()  # greeting
        self.cmd("qmp_capabilities")

    def _read(self):
        while True:
            msg = json.loads(self.f.readline())
            if "event" not in msg:
                return msg

    def cmd(self, name, **args):
        self.f.write(json.dumps({"execute": name, "arguments": args}) + "\n")
        self.f.flush()
        r = self._read()
        if "error" in r:
            raise SystemExit(f"QMP {name}: {r['error']}")
        return r.get("return")


def combo(spec):
    keys = []
    for k in spec.lower().split("-") if spec != "-" else ["minus"]:
        keys.append({"type": "qcode", "data": ALIASES.get(k, k)})
    return keys


def main():
    sock, what, *rest = sys.argv[1:]
    q = QMP(sock)
    if what == "keys":
        # Press the chord's keys one after another (modifiers first), hold,
        # release in reverse: KWin's Alt+Tab ignores a simultaneous press,
        # which is what QMP send-key does.
        for spec in rest:
            spec, _, hold = spec.partition(":")  # e.g. alt-tab:2500 holds the chord 2.5 s
            keys = combo(spec)
            for k in keys:
                q.cmd("input-send-event", events=[{"type": "key", "data": {"down": True, "key": k}}])
                time.sleep(0.08)
            time.sleep(int(hold or 120) / 1000)
            for k in reversed(keys):
                q.cmd("input-send-event", events=[{"type": "key", "data": {"down": False, "key": k}}])
                time.sleep(0.03)
            time.sleep(0.4)
    elif what == "type":
        for ch in " ".join(rest):
            if ch.isupper():
                keys = ["shift", ch.lower()]
            elif ch in SHIFTED:
                keys = ["shift", SHIFTED[ch]]
            else:
                keys = [PLAIN.get(ch, ch)]
            for k in keys:
                q.cmd("input-send-event", events=[{"type": "key", "data": {"down": True, "key": {"type": "qcode", "data": k}}}])
                time.sleep(0.03)
            time.sleep(0.05)
            for k in reversed(keys):
                q.cmd("input-send-event", events=[{"type": "key", "data": {"down": False, "key": {"type": "qcode", "data": k}}}])
            time.sleep(0.08)
    elif what == "drag":
        # drag X1 Y1 X2 Y2 WIDTH HEIGHT: press at 1, move in steps, release at 2
        x1, y1, x2, y2, w, h = (int(v) for v in rest[:6])
        absev = lambda x, y: [{"type": "abs", "data": {"axis": "x", "value": x * 32767 // (w - 1)}},
                              {"type": "abs", "data": {"axis": "y", "value": y * 32767 // (h - 1)}}]
        q.cmd("input-send-event", events=absev(x1, y1))
        time.sleep(0.2)
        q.cmd("input-send-event", events=[{"type": "btn", "data": {"down": True, "button": "left"}}])
        for i in range(1, 21):
            q.cmd("input-send-event", events=absev(x1 + (x2 - x1) * i // 20, y1 + (y2 - y1) * i // 20))
            time.sleep(0.03)
        q.cmd("input-send-event", events=[{"type": "btn", "data": {"down": False, "button": "left"}}])
    elif what in ("click", "move"):
        # click X Y WIDTH HEIGHT [left|right|middle]: absolute pointer via usb-tablet
        x, y, w, h = (int(v) for v in rest[:4])
        button = rest[4] if len(rest) > 4 else "left"
        pos = [{"type": "abs", "data": {"axis": "x", "value": x * 32767 // (w - 1)}},
               {"type": "abs", "data": {"axis": "y", "value": y * 32767 // (h - 1)}}]
        q.cmd("input-send-event", events=pos)
        time.sleep(0.15)
        if what == "click":
            for down in (True, False):
                q.cmd("input-send-event", events=[{"type": "btn", "data": {"down": down, "button": button}}])
                time.sleep(0.08)
    else:
        args = json.loads(rest[0]) if rest else {}
        print(json.dumps(q.cmd(what, **args), indent=1))


if __name__ == "__main__":
    main()
