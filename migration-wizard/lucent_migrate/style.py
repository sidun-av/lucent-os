"""Pebble Drift look for the wizard (docs/mockups/concepts-2026/pebble-drift/).

Kept apart from the page logic: `apply(wizard)` adds the step sidebar (a
sunken well, the current step on a raised "pillow", as in the Settings
mockups), turns page titles into large headings, styles lists as raised
cards, and marks Next/Finish as the one accent-coloured primary action.

Every colour and size comes from the design tokens (tokens.py, a copy of
pebble-drift.css part 1), light or dark following the system palette. The
wizard follows a live light/dark switch and Settings' "Text size" (the
system font's point size, 11 pt by default) without a restart.
"""

from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import QEvent, QObject, QSize, Qt
from PySide6.QtGui import QFont, QFontDatabase, QIcon, QPalette
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QHeaderView, QLabel, QTreeWidget, QVBoxLayout, QWidget,
    QWizard,
)

from . import tokens
from .i18n import N_, _

HERE = Path(__file__).parent

# One entry per wizard page, in order.
STEPS = [N_("Welcome"), N_("Windows account"), N_("Folders"), N_("Browsers and Wi-Fi"),
         N_("Copying"), N_("Done")]

# Figtree (--font-sans) ships with Lucent Settings (SIL OFL 1.1); the wizard
# uses that copy when it is there and falls back to the system's Inter.
FONT_DIRS = [
    HERE.parent / "lucent_settings" / "fonts",                                  # /usr/lib/lucent
    HERE.parents[1] / "apps" / "lucent-settings" / "lucent_settings" / "fonts",          # checkout
]
BASE_POINTS = 11.0   # Lucent's UI font size (kdeglobals); the tokens' px are for it


def is_dark(palette: QPalette) -> bool:
    return palette.color(QPalette.ColorRole.Window).lightness() < 128


def text_scale(font: QFont) -> float:
    """How much larger the system text is than Lucent's default 11 pt."""
    points = font.pointSizeF()
    return 1.0 if points <= 0 else max(0.8, min(2.0, points / BASE_POINTS))


def check_icon(dark: bool) -> Path:
    """The check mark inside a ticked box, in --text-on-accent."""
    return HERE / ("check-dark.svg" if dark else "check.svg")


def _colours(shadow: str) -> list[str]:
    return re.findall(r"rgba?\([^)]*\)|#[0-9a-fA-F]{3,8}", shadow)


def _rgba(colour: str) -> tuple[float, float, float, float]:
    if colour.startswith("#"):
        h = colour[1:]
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 1.0
    r, g, b, *a = (float(v) for v in colour[colour.index("(") + 1:-1].split(","))
    return r, g, b, a[0] if a else 1.0


def _over(top: str, bottom: str) -> str:
    """`top` composited over `bottom`: one hairline for a ring plus a drop shadow."""
    r1, g1, b1, a1 = _rgba(top)
    r2, g2, b2, a2 = _rgba(bottom)
    a = a1 + a2 * (1 - a1)
    mix = [round((c1 * a1 + c2 * a2 * (1 - a1)) / a) for c1, c2 in ((r1, r2), (g1, g2), (b1, b2))]
    return f"rgba({mix[0]}, {mix[1]}, {mix[2]}, {a:.3f})"


QSS = """
QWizard, QWizardPage {{ background: {bg}; }}
QWidget {{ color: {text}; font-size: {body}; font-weight: 500; }}
QLabel {{ background: transparent; }}
QLabel#lucentHeading {{ font-size: {display}; font-weight: {display_weight}; padding-bottom: {s4}; }}
QLabel#lucentSection {{ font-size: {subhead}; font-weight: 700; padding-top: {s2}; }}
QLabel:disabled {{ color: {text_disabled}; }}

QFrame#lucentSide {{ background: {sunken}; border: 1px solid {sunken_ring};
    border-top-color: {sunken_top}; border-radius: {r_card}; }}
QFrame#lucentSideRule {{ background: {line}; border: none; min-height: 1px; max-height: 1px; }}
QLabel#lucentBrand {{ font-size: {subhead}; font-weight: 700; }}
QFrame#lucentStepRow {{ border-radius: {r_control}; border: 1px solid transparent; }}
QFrame#lucentStepRow[state="current"] {{ background: {raised}; border-color: {raised_ring};
    border-bottom-color: {raised_bottom}; }}
QLabel#lucentStep {{ color: {text2}; }}
QLabel#lucentStep[state="done"] {{ color: {text}; }}
QLabel#lucentStep[state="current"] {{ color: {accent_text}; font-weight: {strong}; }}
QLabel#lucentDot {{ font-size: {caption}; font-weight: 700; border-radius: {dot_radius};
    min-width: {dot}; max-width: {dot}; min-height: {dot}; max-height: {dot};
    color: {text3}; border: 1px solid {line_control}; background: transparent; }}
QLabel#lucentDot[state="current"] {{ color: {on_accent}; background: {accent}; border-color: {accent}; }}
QLabel#lucentDot[state="done"] {{ color: {accent_text}; background: {accent_soft_strong};
    border-color: transparent; }}
QFrame#lucentNote {{ background: {raised}; border: 1px solid {raised_ring};
    border-bottom-color: {raised_bottom}; border-radius: {r_card}; }}
QLabel#lucentNoteTitle {{ font-weight: 700; }}
QLabel#lucentNoteText {{ font-size: {caption}; color: {text2}; }}

QListWidget, QTreeWidget {{ background: {raised}; border: 1px solid {raised_ring};
    border-bottom-color: {raised_bottom}; border-radius: {r_card}; padding: {s2}; outline: 0; }}
QListWidget::item, QTreeWidget::item {{ min-height: {row}; padding: 0 {s2}; border: none;
    border-radius: {r_control}; color: {text}; }}
QListWidget::item:hover, QTreeWidget::item:hover {{ background: {hover}; }}
QListWidget::item:selected, QTreeWidget::item:selected {{ background: {accent_soft}; color: {text}; }}
QListWidget::item:disabled {{ color: {text3}; }}
QHeaderView {{ background: transparent; border: none; }}
QHeaderView::section {{ background: transparent; border: none; border-bottom: 1px solid {line};
    padding: {s2} {s3}; font-size: {caption}; font-weight: {caption_weight}; color: {text2}; }}

QCheckBox, QRadioButton {{ spacing: {s3}; background: transparent; }}
QCheckBox::indicator, QListView::indicator, QTreeView::indicator {{ width: 18px; height: 18px;
    border-radius: {r_chip}; border: 1px solid {line_control}; background: {raised_flat}; }}
QCheckBox::indicator:hover, QListView::indicator:hover, QTreeView::indicator:hover {{
    border-color: {accent}; }}
QCheckBox::indicator:checked, QListView::indicator:checked, QTreeView::indicator:checked {{
    background: {accent}; border-color: {accent}; image: url({check}); }}
QCheckBox::indicator:disabled, QListView::indicator:disabled, QTreeView::indicator:disabled {{
    background: {sunken}; border-color: {line}; }}
QRadioButton::indicator {{ width: 20px; height: 20px; border-radius: 11px;
    border: 1px solid {line_control}; background: {raised_flat}; }}
QRadioButton::indicator:hover {{ border-color: {accent}; }}
QRadioButton::indicator:checked {{ width: 8px; height: 8px; border: 7px solid {accent};
    background: {on_accent}; }}

QPushButton {{ min-height: {button}; padding: 0 {s5}; border-radius: {r_button}; font-weight: {strong};
    color: {text}; background: {raised}; border: 1px solid {raised_ring};
    border-bottom-color: {raised_bottom}; }}
QPushButton:hover {{ border-color: {line_strong}; }}
QPushButton:pressed {{ background: {pressed}; }}
QPushButton:focus {{ border-color: {accent_ring}; }}
QPushButton:disabled {{ color: {text_disabled}; background: {sunken}; border-color: transparent; }}
QPushButton[lucentRole="primary"] {{ color: {on_accent}; background: {accent}; border: 1px solid {accent};
    border-bottom-color: {accent_pressed}; padding: 0 {s6}; }}
QPushButton[lucentRole="primary"]:hover {{ background: {accent_hover}; border-color: {accent_hover}; }}
QPushButton[lucentRole="primary"]:pressed {{ background: {accent_pressed}; border-color: {accent_pressed}; }}
QPushButton[lucentRole="primary"]:disabled {{ color: {text_disabled}; background: {accent_soft_strong};
    border-color: transparent; }}
QPushButton[lucentRole="ghost"] {{ color: {text2}; background: transparent; border-color: transparent; }}
QPushButton[lucentRole="ghost"]:hover {{ color: {text}; background: {hover}; }}
QPushButton[lucentRole="ghost"]:pressed {{ background: {pressed}; }}
QPushButton[lucentRole="ghost"]:focus {{ border-color: {accent_ring}; }}

QProgressBar {{ border: 1px solid {sunken_ring}; border-top-color: {sunken_top}; border-radius: 6px;
    background: {sunken_strong}; min-height: 10px; max-height: 10px; text-align: center;
    color: transparent; }}
QProgressBar::chunk {{ border-radius: 5px; background: {accent}; }}

QScrollBar:vertical {{ background: transparent; width: 12px; margin: {s1} 2px; }}
QScrollBar:horizontal {{ background: transparent; height: 12px; margin: 2px {s1}; }}
QScrollBar::handle {{ background: {line_strong}; border-radius: 4px; min-height: 40px; min-width: 40px; }}
QScrollBar::handle:hover {{ background: {line_control}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
QToolTip {{ color: {text}; background: {popover}; border: 1px solid {line_strong};
    border-radius: {r_chip}; padding: {s1} {s2}; }}
QWidget#lucentRuler {{ background: {line}; border: none; min-height: 1px; max-height: 1px; }}
"""


def stylesheet(dark: bool, scale: float = 1.0) -> str:
    t = tokens.load(dark)
    c = {k: tokens.qss(t[k]) for k in t}

    def size(px: float) -> str:
        return f"{px * scale:.2f}px"

    raised_ring, raised_drop = _colours(t["shadow-raised"])[:2]
    sunken_shade, sunken_ring = _colours(t["shadow-sunken"])[:2]
    return QSS.format(
        bg=c["surface-window-solid"], text=c["text-primary"], text2=c["text-secondary"],
        text3=c["text-tertiary"], text_disabled=c["text-disabled"],
        accent=c["accent"], accent_hover=c["accent-hover"], accent_pressed=c["accent-pressed"],
        accent_text=c["accent-text"], accent_soft=c["accent-soft"],
        accent_soft_strong=c["accent-soft-strong"], accent_ring=c["accent-ring"],
        on_accent=c["text-on-accent"],
        raised=tokens.qss(f"linear-gradient({t['surface-raised']}, {t['surface-raised-2']})"),
        raised_flat=c["surface-raised"], raised_ring=tokens.qss(raised_ring),
        raised_bottom=tokens.qss(_over(raised_ring, raised_drop)),
        sunken=c["surface-sunken"], sunken_strong=c["surface-sunken-strong"],
        sunken_ring=tokens.qss(sunken_ring), sunken_top=tokens.qss(_over(sunken_shade, sunken_ring)),
        popover=c["surface-popover"], hover=c["state-hover"], pressed=c["state-pressed"],
        line=c["line"], line_strong=c["line-strong"], line_control=c["line-control"],
        r_card=t["radius-card"], r_control=t["radius-control"], r_chip=t["radius-chip"],
        r_button="11px",                                   # .btn in pebble-drift.css
        display=size(tokens.px(t["type-display"])), display_weight=t["type-display-weight"],
        subhead=size(tokens.px(t["type-subhead"])), body=size(tokens.px(t["type-body"])),
        caption=size(tokens.px(t["type-caption"])), caption_weight=t["type-caption-weight"],
        strong=t["type-body-strong"],
        s1=size(tokens.px(t["space-1"])), s2=size(tokens.px(t["space-2"])),
        s3=size(tokens.px(t["space-3"])), s4=size(tokens.px(t["space-4"])),
        s5=size(tokens.px(t["space-5"])), s6=size(tokens.px(t["space-6"])),
        row=size(40), button=size(40), dot=size(24), dot_radius=size(12),
        check=check_icon(dark).as_posix(),
    )


def load_fonts() -> list[str]:
    """Families from the bundled Figtree files that could be registered."""
    families: list[str] = []
    for folder in FONT_DIRS:
        for ttf in sorted(folder.glob("*.ttf")):
            font_id = QFontDatabase.addApplicationFont(str(ttf))
            families += [f for f in QFontDatabase.applicationFontFamilies(font_id) if f not in families]
        if families:
            break
    return families


def ui_font(base: QFont) -> QFont:
    """The system font, in --font-sans' families (Figtree, then Inter)."""
    font = QFont(base)
    wanted = [f.strip().strip('"') for f in tokens.load(False)["font-sans"].split(",")]
    font.setFamilies([f for f in wanted if f not in ("system-ui", "sans-serif")] + base.families())
    return font


class StepSidebar(QWidget):
    """Left column: a sunken well with the brand, the wizard's steps and the
    'nothing changes' note, inset from the window edges like Settings' sidebar."""

    def __init__(self):
        super().__init__()
        self.setObjectName("lucentSideHost")
        self.setFixedWidth(302)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 0, 12)
        well = QFrame()
        well.setObjectName("lucentSide")
        outer.addWidget(well)
        lay = QVBoxLayout(well)
        lay.setContentsMargins(12, 18, 12, 12)
        lay.setSpacing(2)

        brand = QHBoxLayout()
        brand.setContentsMargins(10, 0, 0, 0)
        brand.setSpacing(12)
        logo = QLabel()
        logo.setPixmap(QIcon.fromTheme("lucent-start").pixmap(QSize(30, 30)))
        brand.addWidget(logo)
        name = QLabel("Lucent")
        name.setObjectName("lucentBrand")
        brand.addWidget(name)
        brand.addStretch()
        lay.addLayout(brand)
        lay.addSpacing(16)
        rule = QFrame()
        rule.setObjectName("lucentSideRule")
        lay.addWidget(rule)
        lay.addSpacing(12)

        self.rows: list[tuple[QLabel, QLabel]] = []
        self.frames: list[QFrame] = []
        for i, title in enumerate(STEPS):
            frame = QFrame()
            frame.setObjectName("lucentStepRow")
            frame.setMinimumHeight(42)
            row = QHBoxLayout(frame)
            row.setContentsMargins(10, 6, 10, 6)
            row.setSpacing(12)
            dot = QLabel(str(i + 1))
            dot.setObjectName("lucentDot")
            dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label = QLabel(_(title))
            label.setObjectName("lucentStep")
            row.addWidget(dot)
            row.addWidget(label, 1)
            lay.addWidget(frame)
            self.rows.append((dot, label))
            self.frames.append(frame)
        lay.addStretch()

        note = QFrame()
        note.setObjectName("lucentNote")
        nl = QVBoxLayout(note)
        nl.setContentsMargins(16, 14, 16, 16)
        nl.setSpacing(6)
        head = QLabel(_("Windows stays as it is"))
        head.setObjectName("lucentNoteTitle")
        head.setWordWrap(True)
        body = QLabel(_("We only copy. Nothing on the Windows disk is deleted or changed."))
        body.setObjectName("lucentNoteText")
        body.setWordWrap(True)
        nl.addWidget(head)
        nl.addWidget(body)
        lay.addWidget(note)

    def set_current(self, index: int) -> None:
        for i, ((dot, label), frame) in enumerate(zip(self.rows, self.frames)):
            state = "done" if i < index else "current" if i == index else "todo"
            dot.setText("✓" if state == "done" else str(i + 1))
            for w in (frame, dot, label):
                w.setProperty("state", state)
                w.style().unpolish(w)
                w.style().polish(w)


def _heading(page) -> None:
    """Replace QWizard's small page title with a large heading in the page."""
    title = page.title()
    if not title or page.layout() is None:
        return
    page.setTitle("")
    label = QLabel(title)
    label.setObjectName("lucentHeading")
    label.setIndent(0)  # align with the page text (a styled label indents by half an x)
    label.setWordWrap(True)
    page.layout().insertWidget(0, label)
    page.layout().setContentsMargins(40, 30, 40, 12)
    page.layout().setSpacing(14)
    for tree in page.findChildren(QTreeWidget):
        # Sizes arrive after the first layout: let the name column take the
        # rest of the width instead of truncating "1.2 GB" to "1...".
        tree.setRootIsDecorated(False)  # a flat list: no tree-branch stubs
        tree.setIconSize(QSize(24, 24))  # folder icons at list-row size, as in Files
        header = tree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in range(1, tree.columnCount()):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)


def refresh(wizard: QWizard) -> None:
    """(Re)apply the style for the system's current light/dark and text size."""
    app = QApplication.instance()
    palette, font = (app.palette(), app.font()) if app else (wizard.palette(), wizard.font())
    look = (is_dark(palette), round(text_scale(font), 3))
    if wizard.property("lucentLook") == list(look):
        return
    wizard.setProperty("lucentLook", list(look))
    wizard.setFont(ui_font(font))
    wizard.setStyleSheet(stylesheet(*look))


class _FollowSystem(QObject):
    """Restyles the wizard when the system palette or font changes (Plasma
    switching to dark at sunset, Settings → Text size)."""

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.Type.ApplicationPaletteChange, QEvent.Type.ApplicationFontChange):
            refresh(self.parent())
        return False


def apply(wizard: QWizard) -> StepSidebar:
    load_fonts()
    wizard.setWizardStyle(QWizard.WizardStyle.ClassicStyle)
    wizard.setOption(QWizard.WizardOption.NoBackButtonOnStartPage, True)
    # The last page reports what was copied: only Finish is left to press.
    wizard.setOption(QWizard.WizardOption.NoBackButtonOnLastPage, True)
    wizard.setOption(QWizard.WizardOption.NoCancelButtonOnLastPage, True)
    for which in (QWizard.WizardButton.NextButton, QWizard.WizardButton.FinishButton):
        wizard.button(which).setProperty("lucentRole", "primary")
    wizard.button(QWizard.WizardButton.CancelButton).setProperty("lucentRole", "ghost")
    # QWizard's ruler above the buttons (a private 2 px widget) is painted in
    # the palette's dark line colour; draw it as a --line hairline instead.
    for child in wizard.findChildren(QWidget):
        if child.metaObject().className() == "QWidget" and child.maximumHeight() == 2:
            child.setObjectName("lucentRuler")
            child.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    # Properties first, then the stylesheet, so the role selectors match.
    refresh(wizard)
    wizard.installEventFilter(_FollowSystem(wizard))
    if wizard.layout() is not None:      # the sidebar well sets its own inset
        wizard.layout().setContentsMargins(0, 0, 0, 0)
    sidebar = StepSidebar()
    wizard.setSideWidget(sidebar)
    for page_id in wizard.pageIds():
        _heading(wizard.page(page_id))
    ids = wizard.pageIds()
    wizard.currentIdChanged.connect(lambda pid: sidebar.set_current(ids.index(pid) if pid in ids else 0))
    sidebar.set_current(0)
    wizard.resize(1180, 780)
    return sidebar
