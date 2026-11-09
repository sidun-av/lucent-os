"""Every user-facing string of This PC has a Russian translation
(po/lucent-thispc.ru.po): the worker's (core/text.cpp), the Eject action's
and the service menu's."""

import re
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
PO = HERE / "po/lucent-thispc.ru.po"


def po_entries():
    """(msgctxt, msgid) -> list of msgstr (one, or the plural forms)."""
    entries, cur, key = {}, {}, None
    for line in PO.read_text(encoding="utf-8").splitlines() + [""]:
        line = line.strip()
        if not line or line.startswith("#"):
            if "msgid" in cur:
                strs = [v for k, v in sorted(cur.items()) if k.startswith("msgstr")]
                entries[(cur.get("msgctxt"), cur["msgid"])] = strs
            cur, key = {}, None
            continue
        m = re.match(r'(msgctxt|msgid_plural|msgid|msgstr(?:\[\d\])?) "(.*)"$', line)
        if m:
            key = m[1]
            cur[key] = m[2]
        elif line.startswith('"') and key:
            cur[key] += line[1:-1]
    return entries


def code_strings():
    text = (HERE / "core/text.cpp").read_text(encoding="utf-8")
    found = []
    for m in re.finditer(r'\bTR[12]?\("([^"]*)",\s*"([^"]*)"', text):
        found.append((m[1], m[2]))
    for m in re.finditer(r'\bTRP\("([^"]*)",\s*"([^"]*)",\s*"([^"]*)"', text):
        found.append((m[1], m[2]))
    script = (ROOT / "system_files/usr/libexec/lucent/thispc-eject").read_text(encoding="utf-8")
    for m in re.finditer(r'\b_\("([^"]+)"\)', script):
        found.append((None, m[1]))
    return found


def test_every_string_is_translated():
    entries = po_entries()
    strings = code_strings()
    assert len(strings) >= 14
    missing = [s for s in strings if not any(entries.get(s, []))]
    assert not missing, missing


def test_plurals_have_three_russian_forms():
    plural = [v for (ctx, msgid), v in po_entries().items() if msgid == "%1 item"]
    assert plural and len(plural[0]) == 3 and all(plural[0])


def test_placeholders_survive_translation():
    for (ctx, msgid), strs in po_entries().items():
        for s in strs:
            for ph in re.findall(r"%\d", msgid):
                assert ph in s, (msgid, s)


def test_service_menu_is_translated():
    desktop = (ROOT / "system_files/usr/share/kio/servicemenus/lucent-thispc-eject.desktop").read_text()
    assert re.search(r"^Name\[ru\]=\S", desktop, re.M)
