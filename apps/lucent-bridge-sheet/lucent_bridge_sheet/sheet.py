"""The sheet window: a centred Pebble Drift card (docs/mockups/05-exe-launch.png
restyled), painted from model.State. Buttons are real QPushButtons, so Tab,
Enter and Esc behave as everywhere else.
"""

from __future__ import annotations

import os

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import (
    QColor, QFont, QFontMetricsF, QImage, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap,
)
from PySide6.QtWidgets import QPushButton, QWidget

from . import look as looks
from . import model
from .i18n import _

CARD_W = 640           # as in the mockup, at 1x
MARGIN = 40            # transparent room for the soft shadow
PAD_TOP, PAD_SIDE, PAD_BOTTOM = 40, 44, 30
ICON = 96


def glyph_path(name: str, size: float) -> QPainterPath:
    """Lucent's 24-unit line glyphs (docs/mockups/lucent.js), scaled."""
    k = size / 24
    p = QPainterPath()
    if name == "winapp":
        p.addRoundedRect(QRectF(3.5 * k, 4.5 * k, 17 * k, 15 * k), 2.5 * k, 2.5 * k)
        p.moveTo(3.5 * k, 9 * k)
        p.lineTo(20.5 * k, 9 * k)
    elif name == "chip":
        p.addRoundedRect(QRectF(6 * k, 6 * k, 12 * k, 12 * k), 2 * k, 2 * k)
        for a, b, c, d in ((9.5, 3, 9.5, 6), (14.5, 3, 14.5, 6), (9.5, 18, 9.5, 21), (14.5, 18, 14.5, 21),
                           (3, 9.5, 6, 9.5), (3, 14.5, 6, 14.5), (18, 9.5, 21, 9.5), (18, 14.5, 21, 14.5)):
            p.moveTo(a * k, b * k)
            p.lineTo(c * k, d * k)
    elif name == "alert":
        p.moveTo(12 * k, 3.5 * k)
        p.lineTo(21.5 * k, 20 * k)
        p.lineTo(2.5 * k, 20 * k)
        p.closeSubpath()
        p.moveTo(12 * k, 9.5 * k)
        p.lineTo(12 * k, 14 * k)
    return p


class Sheet(QWidget):
    action = Signal(str)   # "cancel" | "close" | "run-anyway"

    def __init__(self, look: looks.Look | None = None):
        super().__init__(None, Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.look = look or looks.load()
        self.state = model.State()
        self.shown_fraction = 0.0
        self.icon: QPixmap | None = None
        self.icon_path: str | None = None
        self.buttons: list[QPushButton] = []
        self.button_spec: list[tuple[str, str, bool]] = []
        self.anim = QTimer(self, interval=16)
        self.anim.timeout.connect(self._step_progress)
        self.setWindowTitle(_("Preparing Windows program"))
        self.resize(self.sizeHint())

    # --- state -----------------------------------------------------------
    def set_state(self, state: model.State) -> None:
        self.state = state
        if state.icon != self.icon_path:
            self.icon_path = state.icon
            pm = QPixmap(state.icon) if state.icon and os.path.isfile(state.icon) else QPixmap()
            self.icon = None if pm.isNull() else pm
        self.setWindowTitle(model.title(state))
        spec = model.buttons(state)
        if spec != self.button_spec:
            self._make_buttons(spec)
        if state.fraction > self.shown_fraction and not self.anim.isActive():
            self.anim.start()
        size = self.sizeHint()
        if size != self.size():
            self.resize(size)
        self._place_buttons()
        self.update()

    def _step_progress(self) -> None:
        target = self.state.fraction
        self.shown_fraction += (target - self.shown_fraction) * 0.22
        if abs(target - self.shown_fraction) < 0.002:
            self.shown_fraction = target
            self.anim.stop()
        self.update()

    # --- buttons ------------------------------------------------------------
    def _make_buttons(self, spec: list[tuple[str, str, bool]]) -> None:
        for b in self.buttons:
            b.deleteLater()
        self.buttons = []
        self.button_spec = spec
        for action, label, primary in spec:
            b = QPushButton(label, self)
            b.setProperty("primary", primary)
            b.setStyleSheet(self._button_qss(primary))
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda _=False, a=action: self.action.emit(a))
            if primary:
                b.setDefault(True)
            b.show()
            self.buttons.append(b)
        if self.buttons:
            (next((b for b in self.buttons if b.property("primary")), self.buttons[-1])).setFocus()

    def _button_qss(self, primary: bool) -> str:
        L = self.look
        r = L.px(L.radius_control)
        font = f"font-size: {L.px(15):.1f}px; font-weight: 600;"
        if primary:
            return (f"QPushButton {{ background: {L.accent.name()}; color: {L.on_accent.name()}; border: none;"
                    f" border-radius: {r:.0f}px; padding: 0 {L.px(18):.0f}px; {font} }}"
                    f"QPushButton:hover {{ background: {L.accent.lighter(108).name()}; }}"
                    f"QPushButton:pressed {{ background: {L.accent.darker(110).name()}; }}"
                    f"QPushButton:focus {{ outline: none; border: 2px solid {L.accent.darker(125).name()}; }}")
        top, bottom = (c.name() for c in L.raised)
        return (f"QPushButton {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {top}, stop:1 {bottom});"
                f" color: {L.text.name()}; border: 1px solid {L.line_strong.name()};"
                f" border-radius: {r:.0f}px; padding: 0 {L.px(18):.0f}px; {font} }}"
                f"QPushButton:hover {{ border-color: {L.text3.name()}; }}"
                f"QPushButton:pressed {{ background: {L.track.name()}; }}"
                f"QPushButton:focus {{ outline: none; border: 2px solid {L.accent.name()}; }}")

    def _place_buttons(self) -> None:
        if not self.buttons:
            return
        L = self.look
        h = round(L.px(40))
        gap = round(L.px(12))
        right = MARGIN + L.px(CARD_W) - L.px(PAD_SIDE)
        y = MARGIN + self._content_height() - L.px(PAD_BOTTOM) - h
        x = right
        for b in reversed(self.buttons):
            w = max(round(L.px(96)), b.sizeHint().width())
            x -= w
            b.setGeometry(round(x), round(y), w, h)
            x -= gap

    # --- layout -------------------------------------------------------------
    def _fonts(self) -> dict[str, QFont]:
        L = self.look
        return {
            "title": looks.font(L.px(22), 700),
            "name": looks.font(L.px(17), 650),
            "body": looks.font(L.px(15), 500),
            "strong": looks.font(L.px(15), 600),
            "chip": looks.font(L.px(14), 650),
        }

    def _text_h(self, font: QFont, text: str, width: float) -> float:
        fm = QFontMetricsF(font)
        flags = int(Qt.AlignmentFlag.AlignHCenter | Qt.TextFlag.TextWordWrap)
        return fm.boundingRect(QRectF(0, 0, width, 10_000), flags, text).height()

    def _blocks(self) -> list[tuple[str, float]]:
        """(what, height) top to bottom, between the paddings."""
        L, s, f = self.look, self.state, self._fonts()
        inner = L.px(CARD_W - 2 * PAD_SIDE)
        out = [("icon", L.px(ICON)), ("gap", L.px(22)),
               ("title", self._text_h(f["title"], model.title(s), inner))]
        if s.started:
            out += [("gap", L.px(10)), ("name", self._text_h(f["name"], s.name, inner)),
                    ("gap", L.px(4)), ("file", self._text_h(f["body"], model.file_line(s), inner))]
        if s.phase == "error":
            msg = s.error.get("message", "")
            if msg:
                out += [("gap", L.px(16)), ("message", self._text_h(f["body"], msg, inner))]
            if s.error.get("hints"):
                out += [("gap", L.px(18)), ("hints", self._hints_h(inner))]
        else:
            out += [("gap", L.px(16)), ("chip", L.px(32)), ("gap", L.px(30)), ("track", L.px(10)),
                    ("gap", L.px(12)), ("status", QFontMetricsF(f["body"]).height())]
        if self.buttons or model.buttons(s):
            out += [("gap", L.px(30)), ("buttons", L.px(40))]
        return out

    def _hints_h(self, inner: float) -> float:
        L, f = self.look, self._fonts()
        pad = L.px(16)
        h = pad
        for hint in self.state.error.get("hints", []):
            h += self._wrap_h(f["body"], hint, inner - 2 * pad - L.px(18)) + L.px(6)
        return h - L.px(6) + pad

    def _wrap_h(self, font: QFont, text: str, width: float) -> float:
        fm = QFontMetricsF(font)
        flags = int(Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap)
        return fm.boundingRect(QRectF(0, 0, width, 10_000), flags, text).height()

    def _content_height(self) -> float:
        L = self.look
        return L.px(PAD_TOP) + sum(h for _, h in self._blocks()) + L.px(PAD_BOTTOM)

    def sizeHint(self) -> QSize:
        L = self.look
        return QSize(round(L.px(CARD_W) + 2 * MARGIN), round(self._content_height() + 2 * MARGIN + 12))

    # --- painting -------------------------------------------------------------
    def paintEvent(self, _event) -> None:
        L, s, f = self.look, self.state, self._fonts()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        card = QRectF(MARGIN, MARGIN, L.px(CARD_W), self._content_height())
        radius = L.px(L.radius_window)
        self._shadow(p, card, radius)
        p.setPen(QPen(L.line_strong, 1))
        p.setBrush(L.card)
        p.drawRoundedRect(card.adjusted(0.5, 0.5, -0.5, -0.5), radius, radius)
        # The pillow's top light.
        p.setPen(QPen(L.highlight, 1))
        p.drawLine(QPointF(card.left() + radius, card.top() + 1.5), QPointF(card.right() - radius, card.top() + 1.5))

        inner_l = card.left() + L.px(PAD_SIDE)
        inner_w = L.px(CARD_W - 2 * PAD_SIDE)
        y = card.top() + L.px(PAD_TOP)
        center = Qt.AlignmentFlag.AlignHCenter | Qt.TextFlag.TextWordWrap
        for what, h in self._blocks():
            r = QRectF(inner_l, y, inner_w, h)
            if what == "icon":
                self._icon(p, QRectF(card.center().x() - h / 2, y, h, h))
            elif what == "title":
                p.setPen(L.text)
                p.setFont(f["title"])
                p.drawText(r, int(center), model.title(s))
            elif what == "name":
                p.setPen(L.text)
                p.setFont(f["name"])
                p.drawText(r, int(center), s.name)
            elif what == "file":
                p.setPen(L.text2)
                p.setFont(f["body"])
                p.drawText(r, int(center), model.file_line(s))
            elif what == "message":
                p.setPen(L.text2)
                p.setFont(f["body"])
                p.drawText(r, int(center), s.error.get("message", ""))
            elif what == "hints":
                self._hints(p, r)
            elif what == "chip":
                self._chip(p, r)
            elif what == "track":
                self._track(p, r)
            elif what == "status":
                p.setFont(f["body"])
                p.setPen(L.text2)
                pct = model.percent(s)
                pct_w = QFontMetricsF(f["strong"]).horizontalAdvance(pct) + L.px(12)
                status = QFontMetricsF(f["body"]).elidedText(model.status_line(s), Qt.TextElideMode.ElideRight,
                                                             r.width() - pct_w)
                p.drawText(r, int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), status)
                if s.phase not in ("cancelling",):
                    p.setFont(f["strong"])
                    p.setPen(L.text)
                    p.drawText(r, int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter), pct)
            y += h
        p.end()

    def _shadow(self, p: QPainter, card: QRectF, radius: float) -> None:
        """A long, soft, cool-tinted drop (--shadow-window), drawn as layers."""
        base = QColor(self.look.shadow)
        layers = 22
        p.setPen(Qt.PenStyle.NoPen)
        for i in range(layers, 0, -1):
            c = QColor(base)
            c.setAlphaF(base.alphaF() * 0.085 * (1 - i / (layers + 1)) ** 2)
            p.setBrush(c)
            grow = i * 1.45
            drop = i * 0.75   # light from above: the shadow falls lower
            p.drawRoundedRect(card.adjusted(-grow, -grow * 0.6 + drop, grow, grow + drop), radius + grow, radius + grow)

    def _icon(self, p: QPainter, r: QRectF) -> None:
        L = self.look
        if self.icon is not None:
            pm = self.icon.scaled(round(r.width() * self.devicePixelRatioF()), round(r.height() * self.devicePixelRatioF()),
                                  Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            pm.setDevicePixelRatio(self.devicePixelRatioF())
            p.drawPixmap(r.topLeft(), pm)
        else:
            # No icon in the file: a calm tile with the Windows-program glyph.
            g = QLinearGradient(r.topLeft(), r.bottomLeft())
            g.setColorAt(0, L.accent.lighter(125))
            g.setColorAt(1, L.accent)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(g)
            p.drawRoundedRect(r.adjusted(4, 4, -4, -4), L.px(22), L.px(22))
            self._glyph(p, "winapp", QRectF(r.center().x() - r.width() * 0.27, r.center().y() - r.width() * 0.27,
                                             r.width() * 0.54, r.width() * 0.54), QColor("#ffffff"), 1.8)
        # Badge: Windows program, or a warning when explaining a problem.
        b = L.px(34)
        badge = QRectF(r.right() - b + L.px(6), r.bottom() - b + L.px(6), b, b)
        warn = self.state.phase == "error"
        p.setPen(QPen(L.card, L.px(3)))
        p.setBrush(L.warning if warn else (QColor("#3a3f58") if L.dark else QColor("#2a303c")))
        p.drawRoundedRect(badge, L.px(10), L.px(10))
        inset = b * 0.22
        self._glyph(p, "alert" if warn else "winapp", badge.adjusted(inset, inset, -inset, -inset),
                    QColor("#ffffff"), 2.0)

    def _glyph(self, p: QPainter, name: str, r: QRectF, colour: QColor, stroke: float) -> None:
        path = glyph_path(name, r.width())
        path.translate(r.topLeft())
        pen = QPen(colour, stroke * r.width() / 24 * 1.2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)
        if name == "winapp":
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(colour)
            k = r.width() / 24
            for cx in (6.6, 8.8):
                p.drawEllipse(QPointF(r.left() + cx * k, r.top() + 6.8 * k), 0.75 * k, 0.75 * k)
        elif name == "alert":
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(colour)
            k = r.width() / 24
            p.drawEllipse(QPointF(r.left() + 12 * k, r.top() + 16.8 * k), 1.1 * k, 1.1 * k)

    def _chip(self, p: QPainter, r: QRectF) -> None:
        """The "x86-64 · direct execution" well: sunken, rounded rectangle."""
        L, f = self.look, self._fonts()
        text = model.mode_line(self.state)
        g = L.px(16)
        w = QFontMetricsF(f["chip"]).horizontalAdvance(text) + g + L.px(8) + 2 * L.px(14)
        chip = QRectF(r.center().x() - w / 2, r.top(), w, r.height())
        p.setPen(QPen(L.line, 1))
        p.setBrush(L.well)
        p.drawRoundedRect(chip.adjusted(0.5, 0.5, -0.5, -0.5), L.px(L.radius_control), L.px(L.radius_control))
        self._glyph(p, "chip", QRectF(chip.left() + L.px(14), chip.center().y() - g / 2, g, g), L.text2, 1.7)
        p.setPen(L.text2)
        p.setFont(f["chip"])
        p.drawText(chip.adjusted(L.px(14) + g + L.px(8), 0, -L.px(14), 0),
                   int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), text)

    def _track(self, p: QPainter, r: QRectF) -> None:
        L = self.look
        rad = r.height() / 2
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(L.track)
        p.drawRoundedRect(r, rad, rad)
        # The sunken well's inner shadow: a darker top edge.
        shade = QColor(0, 0, 0, 40 if L.dark else 18)
        p.setBrush(shade)
        p.drawRoundedRect(QRectF(r.left(), r.top(), r.width(), r.height() * 0.45), rad, rad)
        frac = max(0.0, min(1.0, self.shown_fraction))
        if frac > 0:
            fill = QRectF(r.left(), r.top(), max(r.height(), r.width() * frac), r.height())
            p.setBrush(L.accent)
            p.drawRoundedRect(fill, rad, rad)

    def _hints(self, p: QPainter, r: QRectF) -> None:
        L, f = self.look, self._fonts()
        p.setPen(QPen(L.line, 1))
        p.setBrush(L.well)
        p.drawRoundedRect(r.adjusted(0.5, 0.5, -0.5, -0.5), L.px(L.radius_card), L.px(L.radius_card))
        pad = L.px(16)
        y = r.top() + pad
        bullet = L.px(18)
        for hint in self.state.error.get("hints", []):
            h = self._wrap_h(f["body"], hint, r.width() - 2 * pad - bullet)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(L.text3)
            line_mid = y + QFontMetricsF(f["body"]).height() / 2
            p.drawEllipse(QPointF(r.left() + pad + L.px(5), line_mid), L.px(2.5), L.px(2.5))
            p.setPen(L.text)
            p.setFont(f["body"])
            p.drawText(QRectF(r.left() + pad + bullet, y, r.width() - 2 * pad - bullet, h),
                       int(Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap), hint)
            y += h + L.px(6)

    # --- keys ---------------------------------------------------------------
    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            actions = [a for a, _, _ in model.buttons(self.state)]
            if "cancel" in actions:
                self.action.emit("cancel")
            elif "close" in actions:
                self.action.emit("close")
            return
        super().keyPressEvent(event)

    def render_image(self) -> QImage:
        """The window as an image (previews and tests)."""
        self._place_buttons()
        img = QImage(self.size() * self.devicePixelRatioF(), QImage.Format.Format_ARGB32_Premultiplied)
        img.setDevicePixelRatio(self.devicePixelRatioF())
        img.fill(Qt.GlobalColor.transparent)
        self.render(img)
        return img
