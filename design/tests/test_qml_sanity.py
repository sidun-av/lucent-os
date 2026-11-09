"""Cheap checks on Lucent's hand-written shell QML that would otherwise only
show up as a broken applet at runtime."""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
QML = sorted(
    list((ROOT / "system_files/usr/share/plasma/plasmoids").glob("org.lucent.*/contents/ui/*.qml"))
    + list((ROOT / "system_files/usr/share/kwin/tabbox").glob("org.lucent.*/contents/ui/*.qml"))
    + [ROOT / "system_files/usr/share/sddm/themes/lucent/Main.qml",
       ROOT / "system_files/usr/share/lucent/design/lockscreen/LockScreenUi.qml"])


@pytest.mark.parametrize("path", QML, ids=lambda p: p.relative_to(ROOT).as_posix())
def test_pixel_sizes_are_whole_numbers(path):
    # font.pixelSize is an int: "15.5" fails to load the whole component
    bad = [line.strip() for line in path.read_text().splitlines()
           if re.search(r"pixelSize:\s*-?\d+\.\d", line)]
    assert not bad, bad


@pytest.mark.parametrize("path", QML, ids=lambda p: p.relative_to(ROOT).as_posix())
def test_no_property_looks_like_a_signal_handler(path):
    # "property color onAccent" is read as a handler: "Cannot assign a value to a signal"
    bad = re.findall(r"property\s+\w+\s+(on[A-Z]\w*)", path.read_text())
    assert not bad, bad
