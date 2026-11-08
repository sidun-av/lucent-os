"""Read Wi-Fi network names from Windows WLAN profiles.

Windows stores Wi-Fi passwords DPAPI-encrypted with a key bound to the
Windows installation (LocalSystem). They cannot be decrypted from Linux,
so only the network names and security type are imported; Plasma asks for
the password the first time the user connects.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from .windows import child_ci

WLAN_PATH = ("ProgramData", "Microsoft", "Wlansvc", "Profiles", "Interfaces")

AUTH_MAP = {
    "open": "open",
    "wpapsk": "wpa-psk",
    "wpa2psk": "wpa-psk",
    "wpa3sae": "sae",
    "wpa": "wpa-eap",
    "wpa2": "wpa-eap",
    "wpa3": "wpa-eap",
    "wpa3ent": "wpa-eap",
    "wpa3ent192": "wpa-eap",
    "shared": "wep",
}


@dataclass(frozen=True)
class WifiProfile:
    ssid: str
    security: str  # open | wpa-psk | sae | wpa-eap | wep
    had_password: bool


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_profile(text: str) -> WifiProfile | None:
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return None
    ssid = auth = None
    had_key = False
    for el in root.iter():
        name = _local(el.tag)
        if name == "SSID":
            for sub in el:
                if _local(sub.tag) == "name" and sub.text:
                    ssid = sub.text
        elif name == "authentication" and el.text:
            auth = el.text.strip().lower()
        elif name == "keyMaterial":
            had_key = True
    if not ssid:
        return None
    return WifiProfile(ssid, AUTH_MAP.get(auth or "open", "open"), had_key)


def find_profiles(windows_root: Path) -> list[WifiProfile]:
    cur: Path | None = windows_root
    for part in WLAN_PATH:
        cur = child_ci(cur, part) if cur else None
    if not cur or not cur.is_dir():
        return []
    seen: dict[str, WifiProfile] = {}
    for xml in sorted(cur.glob("*/*.xml")):
        try:
            prof = parse_profile(xml.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
        if prof and prof.ssid not in seen:
            seen[prof.ssid] = prof
    return sorted(seen.values(), key=lambda p: p.ssid)


def nmcli_add_args(p: WifiProfile) -> list[str] | None:
    """NetworkManager command that adds the network without a stored secret.
    Enterprise (802.1X) and WEP networks need manual setup -> None."""
    if p.security in ("wpa-eap", "wep"):
        return None
    args = ["nmcli", "connection", "add", "type", "wifi", "con-name", p.ssid,
            "ssid", p.ssid, "connection.autoconnect", "yes"]
    if p.security != "open":
        # psk-flags 1 = agent-owned: the desktop asks for the password on
        # first connect and keeps it in KWallet, not in a root-readable file.
        args += ["wifi-sec.key-mgmt", p.security, "wifi-sec.psk-flags", "1"]
    return args
