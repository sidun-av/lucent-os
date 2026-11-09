import gzip
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
THEMES = ROOT / "system_files/usr/share/plasma/desktoptheme"

pytest.importorskip("numpy")
import gen_plasma_theme as g  # noqa: E402
import tokens  # noqa: E402


def svg_text(doc):
    return doc.svg()


@pytest.mark.parametrize("dark", [False, True])
def test_accent_parts_are_vector_and_recolourable(dark):
    t = g.theme(tokens.load().mode(dark), dark)
    tasks = svg_text(g.tasks(t))
    focus_bottom = re.search(r'<g id="focus-bottom".*?</g></g>', tasks).group(0)
    assert 'class="ColorScheme-Highlight"' in focus_bottom
    assert 'id="current-color-scheme"' in tasks
    for doc in (g.viewitem(t), g.lineedit(t), g.tabbar(t)):
        assert "ColorScheme-Highlight" in svg_text(doc)


def test_pieces_are_sized_by_their_image():
    """KSvg sizes an element by its content: an overlay must stay inside its piece."""
    QtSvg = pytest.importorskip("PySide6.QtSvg")
    from PySide6.QtCore import QByteArray
    t = g.theme(tokens.load().light, False)
    for doc in (g.tasks(t), g.viewitem(t), g.lineedit(t), g.tabbar(t)):
        text = svg_text(doc)
        r = QtSvg.QSvgRenderer(QByteArray(text.encode()))
        assert r.isValid()
        for m in re.finditer(r'<g id="([^"]+)" transform="translate\(([-\d.]+),([-\d.]+)\)"><image x="0" y="0" '
                             r'width="([\d.]+)" height="([\d.]+)"', text):
            eid, x, y, w, h = m.group(1), *map(float, m.groups()[1:])
            b = r.boundsOnElement(eid)
            assert (round(b.x(), 2), round(b.y(), 2), round(b.width(), 2), round(b.height(), 2)) == (x, y, w, h), eid


def test_taskbar_is_a_flush_slab():
    t = g.theme(tokens.load().light, False)
    text = svg_text(g.panel_background(t, False))
    assert 'id="hint-top-margin"' in text
    assert g.PANEL_H == 68 and g.TASK_H == g.PANEL_H


def test_committed_theme_metadata():
    for tid in ("lucent", "lucent-dark"):
        assert (THEMES / tid / "metadata.json").is_file()
        for f in ("widgets/panel-background.svgz", "dialogs/background.svgz", "widgets/tasks.svgz",
                  "widgets/viewitem.svgz", "widgets/lineedit.svgz", "widgets/tabbar.svgz"):
            with gzip.open(THEMES / tid / f) as fh:
                assert fh.read(5) == b"<?xml"
