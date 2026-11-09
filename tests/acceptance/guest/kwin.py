#!/usr/bin/python3
"""The windows of the running Plasma session, for the acceptance test.

  kwin.py list             every window, one TSV line each:
                           caption, class, pid, x, y, width, height, active (0/1), normal (0/1)
  kwin.py activate REGEX   make the first normal window whose caption matches the active one
  kwin.py close REGEX      close every normal window whose caption matches (like its X button)

Runs inside the session (systemd-run --user). A KWin script reads the window
list and calls back over D-Bus, as kdotool does: a KWin script's print() goes
to a debug log category that is off by default. PySide6 is in the image for
the migration wizard. All output lines are printed after the action.
"""
import json
import os
import sys
import tempfile

from PySide6.QtCore import QCoreApplication, QObject, QTimer, Slot
from PySide6.QtDBus import QDBusConnection, QDBusInterface, QDBusMessage

IFACE = "org.lucent.AcceptanceKWin"

SCRIPT = r"""
(function () {
    const mode = %MODE%, pattern = new RegExp(%REGEX%);
    const rows = [];
    let acted = false;
    for (const w of workspace.windowList()) {
        const usable = w.normalWindow || w.dialog;
        const hit = usable && pattern.test(w.caption || "");
        if (hit && mode === "activate" && !acted) { workspace.activeWindow = w; acted = true; }
        if (hit && mode === "close") { w.closeWindow(); }
        const g = w.frameGeometry;
        rows.push([String(w.caption || "").replace(/[\t\n]/g, " "), w.resourceClass, w.pid,
                   Math.round(g.x), Math.round(g.y), Math.round(g.width), Math.round(g.height),
                   workspace.activeWindow === w ? 1 : 0, usable ? 1 : 0].join("\t"));
    }
    callDBus(%SERVICE%, "/", "%IFACE%", "report", rows.join("\n"));
})();
"""


class Receiver(QObject):
    text = None

    @Slot(str)
    def report(self, text):
        Receiver.text = text
        QCoreApplication.quit()


def die(msg):
    print(f"kwin.py: {msg}", file=sys.stderr)
    sys.exit(2)


def option(name):
    opts = QDBusConnection.RegisterOption
    return getattr(opts, name, None) or getattr(QDBusConnection, name)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "list"
    regex = sys.argv[2] if len(sys.argv) > 2 else "^$"
    if mode not in ("list", "activate", "close"):
        die(f"unknown mode {mode}")
    app = QCoreApplication(sys.argv[:1])
    bus = QDBusConnection.sessionBus()
    if not bus.isConnected():
        die("no session bus")
    service = f"{IFACE}.p{os.getpid()}"
    if not bus.registerService(service):
        die(f"cannot register {service}")
    receiver = Receiver()
    if not bus.registerObject("/", IFACE, receiver, option("ExportAllSlots")):
        die("cannot export the receiver")
    js = (SCRIPT.replace("%MODE%", json.dumps(mode)).replace("%REGEX%", json.dumps(regex))
          .replace("%SERVICE%", json.dumps(service)).replace("%IFACE%", IFACE))
    fd, path = tempfile.mkstemp(suffix=".js", dir=os.environ.get("XDG_RUNTIME_DIR"))
    with os.fdopen(fd, "w") as f:
        f.write(js)
    plugin = f"lucent-acceptance-{os.getpid()}"
    scripting = QDBusInterface("org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting", bus)
    try:
        reply = scripting.call("loadScript", path, plugin)
        if reply.type() == QDBusMessage.MessageType.ErrorMessage:
            die(f"loadScript: {reply.errorMessage()}")
        sid = reply.arguments()[0]
        script = QDBusInterface("org.kde.KWin", f"/Scripting/Script{sid}", "org.kde.kwin.Script", bus)
        reply = script.call("run")
        if reply.type() == QDBusMessage.MessageType.ErrorMessage:
            die(f"run: {reply.errorMessage()}")
        QTimer.singleShot(15000, app.quit)
        app.exec()
        script.call("stop")
    finally:
        scripting.call("unloadScript", plugin)
        os.unlink(path)
    if Receiver.text is None:
        die("no answer from the KWin script")
    if Receiver.text:
        print(Receiver.text)


if __name__ == "__main__":
    main()
