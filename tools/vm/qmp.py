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
        for spec in rest:
            q.cmd("send-key", keys=combo(spec), **{"hold-time": 120})
            time.sleep(0.4)
    elif what == "type":
        for ch in " ".join(rest):
            if ch.isupper():
                keys = ["shift", ch.lower()]
            elif ch in SHIFTED:
                keys = ["shift", SHIFTED[ch]]
            else:
                keys = [PLAIN.get(ch, ch)]
            q.cmd("send-key", keys=[{"type": "qcode", "data": k} for k in keys], **{"hold-time": 40})
            time.sleep(0.05)
    else:
        args = json.loads(rest[0]) if rest else {}
        print(json.dumps(q.cmd(what, **args), indent=1))


if __name__ == "__main__":
    main()
