"""A whole fake laptop for the UI tests: every backend command answered
from tests/fixtures (Wi-Fi, Bluetooth devices, a staged update, a Windows
program), so each page renders with real-looking content offscreen."""

from __future__ import annotations

import json

from conftest import FakeRunner, fixture


def laptop_runner() -> FakeRunner:
    r = FakeRunner()
    r.on("nmcli", "-t", "-f", "WIFI-HW,WIFI,NETWORKING", "general", out=fixture("nmcli-general-wifi.txt"))
    r.on("nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "device", out=fixture("nmcli-device-wifi.txt"))
    r.on("nmcli", "-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY,BSSID", out=fixture("nmcli-wifi-list.txt"))
    r.on("nmcli", "-t", "-f", "NAME,TYPE,DEVICE", "connection", "show", out=fixture("nmcli-connections.txt"))
    r.on("busctl", "--system", "--json=short", "call", "org.bluez", "/", out=fixture("bluez-objects.json"))
    r.on("kscreen-doctor", "-j", out=fixture("kscreen.json"))
    r.on("busctl", "--user", "--json=short", "get-property", "org.kde.KWin",
         out='{"type":"b","data":false}\n{"type":"b","data":true}\n')
    r.on("pactl", "-f", "json", "list", "sinks", out=fixture("pactl-sinks-laptop.json"))
    r.on("pactl", "-f", "json", "list", "sources", out="[]")
    r.on("pactl", "get-default-sink", out="alsa_output.pci-0000_00_1f.3.analog-stereo\n")
    r.on("busctl", "--system", "--json=short", "call", "org.freedesktop.Accounts", "/org/freedesktop/Accounts",
         out='{"type":"o","data":["/org/freedesktop/Accounts/User1000"]}\n')
    r.on("busctl", "--system", "--json=short", "get-property", "org.freedesktop.Accounts",
         out='{"type":"s","data":"anna"}\n{"type":"s","data":"Anna Smirnova"}\n{"type":"s","data":""}\n{"type":"i","data":1}\n')
    r.on("rpm-ostree", "status", "--json", out=fixture("rpm-ostree-staged.json"))
    r.on("flatpak", "remote-ls", out="org.mozilla.firefox\tFirefox\t146.0\n")
    r.on("lucent-bridge", "list", "--json", out=fixture("bridge-list.json"))
    r.on("lucent-bridge", "plan", "--json", out=fixture("bridge-plan.json"))
    r.on("lscpu", "--json", out=fixture("lscpu.json"))
    return r


__all__ = ["laptop_runner", "json"]
