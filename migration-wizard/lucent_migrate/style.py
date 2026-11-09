"""Lucent look for the wizard (docs/mockups/04-migration.png).

Kept apart from the page logic: `apply(wizard)` adds the step sidebar,
turns page titles into large headings, styles lists as cards, and marks the
Next/Finish button as the one accent-coloured primary action. Colours and
sizes are the mockups' tokens (docs/mockups/lucent.css), light or dark
following the system palette.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPalette
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QHeaderView, QLabel, QTreeWidget, QVBoxLayout, QWidget,
    QWizard,
)

from .i18n import N_, _

HERE = Path(__file__).parent

# One entry per wizard page, in order.
STEPS = [N_("Welcome"), N_("Windows account"), N_("Folders"), N_("Browsers and Wi-Fi"),
         N_("Copying"), N_("Done")]

LIGHT = dict(
    bg="#ffffff", side="#f4f5f8", card="#ffffff", field="#eceef3", text="#1b1f27",
    text2="#4c5463", text3="#6a7282", line="rgba(20,28,45,0.10)", line_strong="rgba(20,28,45,0.18)",
    hover="rgba(20,28,45,0.05)", sel="rgba(59,110,245,0.14)", accent="#3b6ef5",
    accent_hover="#2f5fe0", accent_disabled="rgba(59,110,245,0.45)", ok="#1f9d55",
)
DARK = dict(
    bg="#1f2229", side="#191b21", card="#262a32", field="#2b2f38", text="#eef0f5",
    text2="#b4bac6", text3="#959cab", line="rgba(255,255,255,0.09)", line_strong="rgba(255,255,255,0.18)",
    hover="rgba(255,255,255,0.05)", sel="rgba(91,139,255,0.22)", accent="#5b8bff",
    accent_hover="#6e98ff", accent_disabled="rgba(91,139,255,0.45)", ok="#3cc47a",
)

QSS = """
QWizard, QWizard > QWidget {{ background: {bg}; }}
QWizardPage {{ background: {bg}; }}
QLabel {{ color: {text}; font-size: 15px; }}
QLabel#lucentHeading {{ font-size: 30px; font-weight: 700; padding-bottom: 6px; }}

QFrame#lucentSide {{ background: {side}; border: none; border-right: 1px solid {line}; }}
QLabel#lucentBrand {{ font-size: 17px; font-weight: 700; }}
QLabel#lucentStep {{ font-size: 15px; color: {text2}; }}
QLabel#lucentStep[state="current"] {{ color: {text}; font-weight: 600; }}
QLabel#lucentDot {{ font-size: 12px; font-weight: 700; border-radius: 12px;
    min-width: 24px; max-width: 24px; min-height: 24px; max-height: 24px;
    color: {text2}; border: 1px solid {line_strong}; background: transparent; }}
QLabel#lucentDot[state="current"] {{ color: white; background: {accent}; border: none; }}
QLabel#lucentDot[state="done"] {{ color: white; background: {ok}; border: none; }}
QFrame#lucentNote {{ background: {card}; border: 1px solid {line}; border-radius: 12px; }}
QLabel#lucentNoteTitle {{ font-size: 14px; font-weight: 600; }}
QLabel#lucentNoteText {{ font-size: 13.5px; color: {text2}; }}

QListWidget, QTreeWidget {{ background: {card}; border: 1px solid {line}; border-radius: 14px;
    padding: 6px; font-size: 15px; color: {text}; outline: 0; }}
QListWidget::item, QTreeWidget::item {{ min-height: 42px; padding: 0 8px; border-radius: 9px; }}
QListWidget::item:hover, QTreeWidget::item:hover {{ background: {hover}; }}
QListWidget::item:selected, QTreeWidget::item:selected {{ background: {sel}; color: {text}; }}
QHeaderView {{ background: transparent; }}
QHeaderView::section {{ background: transparent; border: none; border-bottom: 1px solid {line};
    padding: 8px 10px; font-size: 13.5px; font-weight: 600; color: {text2}; }}

QCheckBox, QRadioButton {{ font-size: 15px; color: {text}; spacing: 10px; }}
QCheckBox::indicator, QListView::indicator, QTreeView::indicator {{ width: 20px; height: 20px;
    border-radius: 6px; border: 1.5px solid {line_strong}; background: {bg}; }}
QCheckBox::indicator:checked, QListView::indicator:checked, QTreeView::indicator:checked {{
    background: {accent}; border-color: {accent}; image: url({check}); }}
QRadioButton::indicator {{ width: 18px; height: 18px; border-radius: 10px;
    border: 1px solid {line_strong}; background: {bg}; }}
QRadioButton::indicator:checked {{ width: 8px; height: 8px; border: 6px solid {accent}; background: white; }}
QWizardRuler, QFrame[frameShape="4"] {{ border: none; background: {line}; min-height: 1px; max-height: 1px; }}

QPushButton {{ min-height: 40px; padding: 0 18px; border-radius: 10px; font-size: 15px;
    font-weight: 600; color: {text}; background: {field}; border: 1px solid {line}; }}
QPushButton:hover {{ border-color: {line_strong}; }}
QPushButton:disabled {{ color: {text3}; }}
QPushButton[lucentRole="primary"] {{ color: white; background: {accent}; border: none; padding: 0 26px; }}
QPushButton[lucentRole="primary"]:hover {{ background: {accent_hover}; }}
QPushButton[lucentRole="primary"]:disabled {{ background: {accent_disabled}; color: white; }}
QPushButton[lucentRole="ghost"] {{ color: {accent}; background: transparent; border: none; }}
QPushButton[lucentRole="ghost"]:hover {{ background: {hover}; }}

QProgressBar {{ border: none; border-radius: 4px; background: {field}; max-height: 8px; min-height: 8px;
    text-align: center; color: transparent; }}
QProgressBar::chunk {{ border-radius: 4px; background: {accent}; }}
"""


def is_dark(palette: QPalette) -> bool:
    return palette.color(QPalette.ColorRole.Window).lightness() < 128


def stylesheet(dark: bool) -> str:
    tokens = DARK if dark else LIGHT
    return QSS.format(check=(HERE / "check.svg").as_posix(), **tokens)


class StepSidebar(QFrame):
    """Left column: brand, the wizard's steps, and the 'nothing changes' note."""

    def __init__(self):
        super().__init__()
        self.setObjectName("lucentSide")
        self.setFixedWidth(270)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 30, 20, 22)
        lay.setSpacing(0)

        brand = QHBoxLayout()
        brand.setSpacing(12)
        logo = QLabel()
        logo.setPixmap(QIcon.fromTheme("lucent-start").pixmap(QSize(30, 30)))
        brand.addWidget(logo)
        name = QLabel("Lucent")
        name.setObjectName("lucentBrand")
        brand.addWidget(name)
        brand.addStretch()
        lay.addLayout(brand)
        lay.addSpacing(34)

        self.rows: list[tuple[QLabel, QLabel]] = []
        for i, title in enumerate(STEPS):
            row = QHBoxLayout()
            row.setSpacing(12)
            dot = QLabel(str(i + 1))
            dot.setObjectName("lucentDot")
            dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label = QLabel(_(title))
            label.setObjectName("lucentStep")
            row.addWidget(dot)
            row.addWidget(label, 1)
            lay.addLayout(row)
            lay.addSpacing(15)
            self.rows.append((dot, label))
        lay.addStretch()

        note = QFrame()
        note.setObjectName("lucentNote")
        nl = QVBoxLayout(note)
        nl.setContentsMargins(14, 12, 14, 14)
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
        for i, (dot, label) in enumerate(self.rows):
            state = "done" if i < index else "current" if i == index else "todo"
            dot.setText("✓" if state == "done" else str(i + 1))
            for w in (dot, label):
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
    label.setWordWrap(True)
    page.layout().insertWidget(0, label)
    page.layout().setContentsMargins(44, 36, 44, 12)
    page.layout().setSpacing(14)
    for tree in page.findChildren(QTreeWidget):
        # Sizes arrive after the first layout: let the name column take the
        # rest of the width instead of truncating "1.2 GB" to "1...".
        tree.setRootIsDecorated(False)  # a flat list: no tree-branch stubs
        header = tree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in range(1, tree.columnCount()):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)


def apply(wizard: QWizard) -> StepSidebar:
    app = QApplication.instance()
    wizard.setWizardStyle(QWizard.WizardStyle.ClassicStyle)
    wizard.setOption(QWizard.WizardOption.NoBackButtonOnStartPage, True)
    for which in (QWizard.WizardButton.NextButton, QWizard.WizardButton.FinishButton):
        wizard.button(which).setProperty("lucentRole", "primary")
    for which in (QWizard.WizardButton.CancelButton, QWizard.WizardButton.BackButton):
        wizard.button(which).setProperty("lucentRole", "ghost")
    # Properties first, then the stylesheet, so the role selectors match.
    wizard.setStyleSheet(stylesheet(is_dark(app.palette() if app else wizard.palette())))
    if wizard.layout() is not None:      # sidebar flush with the window edges
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
