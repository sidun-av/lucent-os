"""Turn udev records and kernel-log events into a device list.

A *device* is what a person would point at: a PCI function, a USB device,
an SDIO card, or (only when it carries something recognisable, such as a
keyboard, a disk or a screen) a Hyper-V, serio, i2c or platform device.
Bridges, root hubs and purely virtual devices are never listed.

Each device gets a group (Wi-Fi, Ethernet, Bluetooth, Sound, Display,
Camera, Input, Storage, Other) and a status:

  working       a driver is bound and nothing went wrong
  needs_driver  no driver claimed it
  problem       firmware failed to load, the driver failed to start, or the
                radio is switched off by a hardware switch
  unused        no driver, and none is expected: chipset parts Linux leaves
                alone, or USB gadgets that programs talk to directly
                (fingerprint readers, phones, smart cards)

"system" marks chipset parts (SMBus, I2C controllers, signal processing...)
that a person never needs to see unless something is wrong with them.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

GROUPS = ["wifi", "ethernet", "bluetooth", "sound", "display", "camera", "input", "storage", "other"]
SCHEMA = 1

# Broadcom Wi-Fi chips that only the proprietary "wl" driver supports
# (neither brcmfmac, brcmsmac, b43 nor b43legacy claims them). docs/drivers.md.
# 14e4:4365 is BCM43142 in laptops; brcmfmac only claims 4365 with Broadcom's
# own subsystem ID (the BCM4365 router chip), so a bound driver rules it out.
BROADCOM_WL_ONLY = {"4360", "43a0", "43b1", "4365"}

_ITEM_BUSES = {"pci", "sdio", "vmbus"}
_LEAF_BUSES = {"serio", "i2c", "spi", "platform", "acpi", "pnp", "mmc", "hid", "virtio", "scsi", "usb"}
_FIRMWARE_DIRS = ("/usr/lib/firmware/updates", "/usr/lib/firmware", "/lib/firmware")

# PCI base classes / class codes that are chipset plumbing.
_PCI_SYSTEM_PREFIXES = ("05", "08", "0b", "10", "11", "ff", "0c05", "0c80", "0c07", "0c09", "0780", "0880")
_USB_USERSPACE_CLASSES = {"ff", "06", "0b", "fe", "dc", "0d", "ef"}


def _pci_class(rec) -> str:
    c = rec.props.get("PCI_CLASS", "")
    return c.lower().rjust(6, "0") if c else ""


def _pci_group(cls: str) -> str | None:
    if not cls:
        return None
    base, sub = cls[:2], cls[:4]
    if sub == "0200":
        return "ethernet"
    if sub == "0280" or sub in ("0d20", "0d21"):
        return "wifi"
    if sub == "0d11":
        return "bluetooth"
    if base == "03":
        return "display"
    if sub in ("0401", "0403"):
        return "sound"
    if sub == "0400":
        return "camera"
    if base == "01" or sub == "0805":
        return "storage"
    if sub == "0900" or sub == "0902":
        return "input"
    return None


def _usb_iface_classes(rec) -> list[str]:
    s = rec.props.get("ID_USB_INTERFACES", "")
    return [x for x in s.split(":") if len(x) == 6]


def _usb_group(classes: list[str]) -> str | None:
    if any(c.startswith("e00101") for c in classes):
        return "bluetooth"
    if any(c.startswith("0e") for c in classes):
        return "camera"
    if any(c.startswith("01") for c in classes):
        return "sound"
    if any(c.startswith("08") for c in classes):
        return "storage"
    if any(c[:4] in ("0206", "020d", "0a00") or c.startswith("e00103") for c in classes):
        return "ethernet"
    if any(c.startswith("03") for c in classes):
        return "input"
    return None


def _decode(enc: str) -> str:
    return re.sub(r"\\x([0-9a-fA-F]{2})", lambda m: chr(int(m.group(1), 16)), enc)


def _clean(name: str | None) -> str | None:
    if not name:
        return None
    name = name.strip().strip('"').strip()
    return name or None


class _Item:
    def __init__(self, rec, bus):
        self.rec = rec
        self.bus = bus
        self.desc = []          # descendant records
        self.kinds = []         # (group, record) from class nodes below it


def _is_class_node(rec):
    """(group, name) for a node that tells what a device *is*, else None."""
    s, name = rec.subsystem, rec.sysname
    if s == "net":
        if rec.devtype == "wlan":
            return "wifi"
        if rec.devtype in (None, "", "ethernet"):
            return "ethernet"
        return None
    if s == "bluetooth" and name.startswith("hci"):
        return "bluetooth"
    if s == "sound" and re.fullmatch(r"card\d+", name):
        return "sound"
    if s == "drm" and re.fullmatch(r"card\d+", name):
        return "display"
    if s == "video4linux" and ":capture:" in rec.props.get("ID_V4L_CAPABILITIES", ""):
        return "camera"
    if s == "input" and re.fullmatch(r"input\d+", name):
        p = rec.props
        if any(p.get(k) == "1" for k in ("ID_INPUT_KEYBOARD", "ID_INPUT_MOUSE", "ID_INPUT_TOUCHPAD",
                                         "ID_INPUT_TOUCHSCREEN", "ID_INPUT_TABLET", "ID_INPUT_JOYSTICK")):
            return "input"
        return None
    if s == "block" and rec.devtype == "disk" and not re.match(r"(loop|ram|zram|dm-|md|nbd)", name):
        return "storage"
    return None


_PRIORITY = ["wifi", "bluetooth", "camera", "display", "ethernet", "sound", "storage", "input"]


def _firmware_present(name: str, dirs) -> bool:
    for d in dirs:
        base = Path(d) / name
        if any(Path(str(base) + ext).exists() for ext in ("", ".xz", ".zst")):
            return True
    return False


def build(records, events, *, kernel_log_source, firmware_dirs=None, hwdb=None) -> dict:
    firmware_dirs = _FIRMWARE_DIRS if firmware_dirs is None else firmware_dirs
    by_path = {r.path: r for r in records}

    # 1. Candidate items: PCI (not bridges), USB devices (not root hubs), SDIO, vmbus.
    items: dict[str, _Item] = {}
    for r in records:
        if "/virtual/" in r.path:
            continue
        if r.subsystem == "pci":
            if _pci_class(r).startswith("06"):
                continue
            items[r.path] = _Item(r, "pci")
        elif r.subsystem == "usb" and r.devtype == "usb_device":
            if r.props.get("ID_VENDOR_ID", "").lower() == "1d6b" or re.fullmatch(r"usb\d+", r.sysname):
                continue
            items[r.path] = _Item(r, "usb")
        elif r.subsystem in _ITEM_BUSES:
            items[r.path] = _Item(r, r.subsystem)

    def owner(path):
        """Nearest ancestor item; a serio/i2c/spi/platform device in between
        becomes an item of its own (a touchpad is not its I2C controller)."""
        parts = path.split("/")
        for i in range(len(parts) - 1, 1, -1):
            p = "/".join(parts[:i])
            if p in items:
                return items[p]
            rec = by_path.get(p)
            if rec and rec.subsystem in ("serio", "i2c", "spi", "platform", "acpi", "pnp") \
                    and (rec.subsystem != "i2c" or rec.devtype != "i2c_adapter") \
                    and not re.fullmatch(r"i2c-\d+", rec.sysname):
                items[p] = _Item(rec, rec.subsystem)
                return items[p]
        # Top-level HID (e.g. the Hyper-V mouse) owns itself.
        for i in range(2, len(parts)):
            p = "/".join(parts[:i + 1])
            rec = by_path.get(p)
            if rec and rec.subsystem == "hid":
                items.setdefault(p, _Item(rec, "hid"))
                return items[p]
        return None

    # 2. Attach class nodes and descendants.
    for r in records:
        if "/virtual/" in r.path:
            continue
        g = _is_class_node(r)
        if g:
            it = owner(r.path)
            if it:
                it.kinds.append((g, r))
    for r in records:
        # descendants: attach to the nearest item only
        parts = r.path.split("/")
        for i in range(len(parts) - 1, 1, -1):
            p = "/".join(parts[:i])
            if p in items:
                items[p].desc.append(r)
                break

    # Leaf items (serio/i2c/platform/hid/vmbus) only count if they carry a class node.
    for p in list(items):
        it = items[p]
        if it.bus not in ("pci", "usb", "sdio") and not it.kinds:
            del items[p]

    # 3. Index kernel names -> item, and drivers -> items.
    name_index: dict[str, _Item] = {}
    driver_index: dict[str, list[_Item]] = {}
    for it in items.values():
        name_index[it.rec.sysname] = it
        for d in it.desc:
            name_index.setdefault(d.sysname, it)
    for it in items.values():
        for drv in _drivers(it):
            driver_index.setdefault(drv, []).append(it)

    per_item_events: dict[int, list] = {}
    for ev in events or []:
        it = name_index.get(ev.device) if ev.device else None
        if it is None and ev.device is None and ev.driver:
            cands = driver_index.get(ev.driver.replace("-", "_"), []) or driver_index.get(ev.driver, [])
            if len(cands) == 1:
                it = cands[0]
        if it is not None:
            per_item_events.setdefault(id(it), []).append(ev)

    # 4. rfkill: per device and machine-wide hardware switches.
    hard_blocked = set()
    for r in records:
        if r.subsystem == "rfkill" and r.props.get("RFKILL_STATE") == "2":
            hard_blocked.add(r.props.get("RFKILL_TYPE"))

    devices = []
    for it in items.values():
        devices.append(_describe(it, per_item_events.get(id(it), []), hard_blocked,
                                 firmware_dirs, hwdb, events is not None))

    order = {"problem": 0, "needs_driver": 1, "working": 2, "unused": 3}
    devices.sort(key=lambda d: (order[d["status"]], d["system"], GROUPS.index(d["group"]),
                                d["name"].lower()))

    visible = [d for d in devices if not d["system"] and d["status"] != "unused"
               or d["status"] in ("problem", "needs_driver")]
    summary = {
        "total": len(visible),
        "working": sum(d["status"] == "working" for d in visible),
        "needs_driver": sum(d["status"] == "needs_driver" for d in devices),
        "problem": sum(d["status"] == "problem" for d in devices),
        "unused": sum(d["status"] == "unused" for d in devices),
        "system": sum(d["system"] for d in devices),
    }
    return {
        "schema": SCHEMA,
        "summary": summary,
        "kernel_log": {"readable": events is not None, "source": kernel_log_source if events is not None else None},
        "devices": devices,
    }


def _drivers(it) -> list[str]:
    out = []
    if it.rec.driver and it.rec.driver not in ("usb", "pcieport"):
        out.append(it.rec.driver)
    for d in it.desc:
        if d.driver and (d.devtype == "usb_interface" or d.subsystem in ("virtio", "sdio")):
            if d.driver not in out:
                out.append(d.driver)
    return out


def _ids(it):
    p = it.rec.props
    if it.bus == "pci" and "PCI_ID" in p:
        v, _, d = p["PCI_ID"].lower().partition(":")
        return {"vendor": v, "device": d}
    if it.bus == "usb":
        v, d = p.get("ID_VENDOR_ID"), p.get("ID_MODEL_ID")
        if not (v and d) and "PRODUCT" in p:
            pv, pd, _ = (p["PRODUCT"].split("/") + ["", ""])[:3]
            v, d = pv.rjust(4, "0"), pd.rjust(4, "0")
        return {"vendor": (v or "").lower(), "device": (d or "").lower()}
    return {"vendor": None, "device": None}


def _describe(it, events, hard_blocked, firmware_dirs, hwdb, log_known):
    rec, p = it.rec, it.rec.props
    if hwdb and "ID_MODEL_FROM_DATABASE" not in p and p.get("MODALIAS"):
        p = {**hwdb(p["MODALIAS"]), **p}

    # Group: what hangs below it first, then its own class codes.
    kinds = [g for g, _ in it.kinds]
    group = next((g for g in _PRIORITY if g in kinds), None)
    classes = _usb_iface_classes(rec) if it.bus == "usb" else []
    if group is None and it.bus == "pci":
        group = _pci_group(_pci_class(rec))
    if group is None and it.bus == "usb":
        group = _usb_group(classes)
    group = group or "other"

    # Name: hwdb, then the device's own strings, then what the class node says.
    name = _clean(p.get("ID_MODEL_FROM_DATABASE"))
    if not name and p.get("ID_MODEL_ENC"):
        name = _clean(_decode(p["ID_MODEL_ENC"]))
    if not name and p.get("ID_MODEL"):
        name = _clean(p["ID_MODEL"].replace("_", " "))
    if not name:
        for _, node in it.kinds:
            name = _clean(node.props.get("NAME")) or _clean(node.props.get("ID_MODEL_FROM_DATABASE"))
            if name:
                break
    if not name:
        name = _clean(p.get("HID_NAME"))
    vendor = _clean(p.get("ID_VENDOR_FROM_DATABASE"))
    if not vendor and p.get("ID_VENDOR"):
        vendor = _clean(p["ID_VENDOR"].replace("_", " "))
    ids = _ids(it)
    if not name:
        kind = (_clean(p.get("ID_PCI_SUBCLASS_FROM_DATABASE")) or _clean(p.get("ID_PCI_CLASS_FROM_DATABASE"))
                or {"usb": "USB device", "pci": "PCI device"}.get(it.bus, "Device"))
        name = f"{kind} {ids['vendor']}:{ids['device']}" if ids["vendor"] else kind

    drivers = _drivers(it)
    if it.bus not in ("pci", "usb", "sdio") and not drivers:
        # serio/i2c/hid items: the driver of the device itself or of what sits on it
        drivers = [d.driver for d in [rec] + it.desc if d.driver][:1]

    pci_cls = _pci_class(rec) if it.bus == "pci" else ""
    system = bool(pci_cls) and pci_cls.startswith(_PCI_SYSTEM_PREFIXES) and group == "other"

    # Firmware and probe failures.
    firmware, problems = [], []
    soft_files = []
    for ev in events:
        if ev.kind == "firmware":
            entry = {"file": ev.file, "error": ev.error, "fatal": ev.fatal,
                     "present": _firmware_present(ev.file, firmware_dirs) if ev.file else None}
            if entry not in firmware:
                firmware.append(entry)
            if not ev.fatal and ev.file:
                soft_files.append(ev)
    fatal_fw = [f for f in firmware if f["fatal"]]
    if fatal_fw or (not drivers and firmware):
        f = (fatal_fw or firmware)[0]
        file, err = f["file"], f["error"]
        if not file and soft_files:       # "failed to request firmware" names no file
            file, err = soft_files[-1].file, err if err is not None else soft_files[-1].error
        present = _firmware_present(file, firmware_dirs) if file else None
        code = "firmware_missing" if (err == -2 or present is False) else "firmware_failed"
        problems.append({"code": code, "file": file, "error": err, "present": present})
    for ev in events:
        if ev.kind == "probe":
            prob = {"code": "probe_failed", "driver": ev.driver, "error": ev.error}
            if prob not in problems:
                problems.append(prob)

    notes = []
    radio = {"wifi": "wlan", "bluetooth": "bluetooth"}.get(group)
    for d in it.desc:
        if d.subsystem == "rfkill" and d.props.get("RFKILL_STATE") == "0":
            notes.append("turned_off")
    if radio and radio in hard_blocked:
        problems.append({"code": "switched_off"})

    if it.bus == "usb" and not drivers:
        userspace = bool(classes) and all(c[:2] in _USB_USERSPACE_CLASSES for c in classes)
    else:
        userspace = False

    if problems:
        status = "problem"
    elif drivers:
        status = "working"
    elif system or userspace:
        status = "unused"
    else:
        status = "needs_driver"
        problems.append({"code": "no_driver"})

    hint = None
    if not drivers and ids["vendor"] == "14e4" and ids["device"] in BROADCOM_WL_ONLY and group == "wifi":
        hint = "broadcom-wl"

    bus_id = rec.sysname
    return {
        "id": f"{it.bus}:{bus_id}",
        "syspath": "/sys" + rec.path,
        "bus": it.bus,
        "group": group,
        "name": name,
        "vendor": vendor,
        "ids": ids,
        "driver": drivers[0] if drivers else None,
        "drivers": drivers,
        "status": status,
        "problems": problems,
        "firmware": firmware,
        "notes": sorted(set(notes)),
        "system": system,
        "hint": hint,
    }
