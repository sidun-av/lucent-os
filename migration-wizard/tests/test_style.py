"""The wizard's Pebble Drift style: built from the tokens, light and dark,
and it follows the system when the colour scheme or the text size changes."""

import os
import re
from pathlib import Path

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QColor, QFont, QPalette  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from lucent_migrate import app, style, tokens  # noqa: E402
from lucent_migrate.volumes import Volume  # noqa: E402

OLD_LUCENT_COLOURS = ["#3b6ef5", "#5b8bff", "#1f2229", "#191b21", "#f4f5f8"]


@pytest.fixture
def qapp():
    qapp = QApplication.instance() or QApplication([])
    palette, font = qapp.palette(), qapp.font()
    yield qapp
    qapp.setPalette(palette)
    qapp.setFont(font)


def palette(window: str, text: str) -> QPalette:
    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window, QColor(window))
    pal.setColor(QPalette.ColorRole.WindowText, QColor(text))
    return pal


@pytest.mark.parametrize("dark", [False, True])
def test_stylesheet_is_built_from_the_tokens(dark):
    t = tokens.load(dark)
    qss = style.stylesheet(dark)
    for name in ("surface-window-solid", "accent", "accent-hover", "text-primary", "text-secondary",
                 "surface-sunken", "line", "text-on-accent"):
        assert tokens.qss(t[name]) in qss, name
    for old in OLD_LUCENT_COLOURS:
        assert old not in qss.lower()
    assert not re.search(r"\{\w+\}", qss)       # no unfilled placeholders
    assert style.check_icon(dark).name in qss


@pytest.mark.parametrize("dark", [False, True])
def test_check_glyph_is_drawn_in_text_on_accent(dark):
    svg = style.check_icon(dark).read_text()
    assert f'stroke="{tokens.load(dark)["text-on-accent"]}"' in svg


def test_text_follows_the_system_font_size():
    assert style.text_scale(QFont("Inter", 11)) == 1.0
    assert style.text_scale(QFont("Inter", 13)) == pytest.approx(13 / 11)
    pixel_sized = QFont("Inter")
    pixel_sized.setPixelSize(15)
    assert style.text_scale(pixel_sized) == 1.0
    body = tokens.px(tokens.load(False)["type-body"])
    assert f"font-size: {body * 2:.2f}px" in style.stylesheet(False, scale=2.0)


def test_wizard_follows_a_live_switch_to_dark_and_a_new_text_size(qapp, monkeypatch, windows_root):
    from lucent_migrate import volumes
    monkeypatch.setattr(volumes, "mount_readonly", lambda v: str(windows_root))
    qapp.setPalette(palette("#eff0f1", "#232629"))
    qapp.setFont(QFont("Inter", 11))
    wiz = app.MigrationWizard([Volume(path="/dev/sda3", fstype="ntfs", size=10**11, uuid="U", label="OS")])
    light_bg = tokens.qss(tokens.load(False)["surface-window-solid"])
    dark_bg = tokens.qss(tokens.load(True)["surface-window-solid"])
    assert light_bg in wiz.styleSheet() and dark_bg not in wiz.styleSheet()

    qapp.setPalette(palette("#202326", "#fcfcfc"))     # e.g. Plasma switched to Lucent Dark
    qapp.processEvents()
    assert dark_bg in wiz.styleSheet() and light_bg not in wiz.styleSheet()

    qapp.setFont(QFont("Inter", 13))                     # Settings → Text size
    qapp.processEvents()
    body = tokens.px(tokens.load(True)["type-body"])
    assert f"font-size: {body * 13 / 11:.2f}px" in wiz.styleSheet()
    wiz.close()
    wiz.deleteLater()
    qapp.processEvents()


def test_figtree_is_found_in_the_system_fonts(qapp):
    # Figtree is installed system-wide (/usr/share/fonts/figtree); a checkout
    # has it under system_files/
    checkout_fonts = Path(__file__).resolve().parents[2] / "system_files/usr/share/fonts/figtree"
    if not checkout_fonts.is_dir():
        pytest.skip("not a repository checkout")
    assert checkout_fonts in [d.resolve() for d in style.FONT_DIRS]
    assert "Figtree" in style.load_fonts()
    assert style.ui_font(QFont("Figtree", 11)).families()[:2] == ["Figtree", "Inter"]
    # a session in a language Figtree has no letters for runs on Inter
    # (lucent-theme font): the wizard follows it instead of mixing the two
    assert style.ui_font(QFont("Inter", 11)).families()[:2] == ["Inter", "Figtree"]
    assert style.ui_font(QFont("DejaVu Sans", 11)).families()[:2] == ["Figtree", "Inter"]
