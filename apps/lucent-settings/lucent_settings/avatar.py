"""The default account picture: initials on the design's avatar gradient
(pebble-drift.css .avatar: 135deg, #6a86ff, #9a62e0 60%, #d0679c), as a
rounded square like the one Settings draws."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QImage, QLinearGradient, QPainter


def initials_png(text: str, out: Path, size: int = 256) -> Path:
    img = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    grad = QLinearGradient(0, 0, size, size)
    grad.setColorAt(0, QColor("#6a86ff"))
    grad.setColorAt(0.6, QColor("#9a62e0"))
    grad.setColorAt(1, QColor("#d0679c"))
    p.setBrush(grad)
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(QRectF(0, 0, size, size), size * 0.28, size * 0.28)
    font = QFont("Inter")
    font.setPixelSize(int(size * (0.40 if len(text) < 2 else 0.34)))
    font.setWeight(QFont.Weight.Bold)
    p.setFont(font)
    p.setPen(QColor("#ffffff"))
    p.drawText(QRectF(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, text)
    p.end()
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(out), "PNG")
    return out
