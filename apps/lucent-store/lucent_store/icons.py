"""Image providers for QML: line symbols in any colour, and app icons.

  image://sym/<name>/<rrggbb>     icons/sym-<name>.svg (the mockups' 24 px line icons)
  image://app/<app id>            the app's icon: Lucent's own tiles, then the
                                  icon theme (Lucent on top of Papirus), then
                                  Flathub's cached AppStream icon
  image://app/tile:<name>         icons/app-<name>.svg (store tiles, ArtCraft)
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6.QtCore import QByteArray, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QImage, QPainter
from PySide6.QtQuick import QQuickImageProvider
from PySide6.QtSvg import QSvgRenderer

HERE = Path(__file__).parent / "icons"


def _render_svg(data: bytes, size: QSize) -> QImage:
    img = QImage(size, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    renderer = QSvgRenderer(QByteArray(data))
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(p, QRectF(0, 0, size.width(), size.height()))
    p.end()
    return img


def _size(requested: QSize, default: int) -> QSize:
    w = requested.width() if requested.width() > 0 else default
    h = requested.height() if requested.height() > 0 else w
    return QSize(w, h)


class SymbolProvider(QQuickImageProvider):
    def __init__(self):
        super().__init__(QQuickImageProvider.ImageType.Image)
        self._svg: dict[str, str] = {}

    def requestImage(self, ident: str, size: QSize, requested: QSize) -> QImage:
        name, _sep, color = ident.partition("/")
        if name not in self._svg:
            path = HERE / f"sym-{name}.svg"
            self._svg[name] = path.read_text() if path.exists() else ""
        # QML passes the colour without "#" (it would start a URL fragment).
        c = QColor("#" + color.lstrip("#") if color else "#000000")
        # QtSvg has no 8-digit hex colours: solid colour + opacity on the root.
        svg = self._svg[name].replace("currentColor", c.name(QColor.NameFormat.HexRgb))
        if c.alpha() < 255:
            svg = svg.replace("<svg ", f'<svg opacity="{c.alphaF():.3f}" ', 1)
        img = _render_svg(svg.encode(), _size(requested, 24))
        size.setWidth(img.width())
        size.setHeight(img.height())
        return img


class AppIconProvider(QQuickImageProvider):
    """`icon_dirs` returns the AppStream icon directories (they appear once
    flatpak has fetched Flathub's catalogue); `tiles` maps app ids to store tiles."""

    def __init__(self, icon_dirs: Callable[[], list[Path]], tiles: dict[str, str]):
        super().__init__(QQuickImageProvider.ImageType.Image)
        self.icon_dirs = icon_dirs
        self.tiles = tiles

    def requestImage(self, ident: str, size: QSize, requested: QSize) -> QImage:
        want = _size(requested, 64)
        app_id = ident.split("?")[0]
        img = QImage()
        tile = app_id[5:] if app_id.startswith("tile:") else self.tiles.get(app_id)
        if tile and (HERE / f"app-{tile}.svg").exists():
            img = _render_svg((HERE / f"app-{tile}.svg").read_bytes(), want)
        elif QIcon.hasThemeIcon(app_id):
            img = QIcon.fromTheme(app_id).pixmap(want).toImage()
        else:
            png = next((Path(d) / f"{app_id}.png" for d in self.icon_dirs()
                        if (Path(d) / f"{app_id}.png").exists()), None)
            if png is not None:
                img = QImage(str(png))
        if img.isNull():
            img = _render_svg((HERE / "app-generic.svg").read_bytes(), want)
        if img.size() != want:
            img = img.scaled(want, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        size.setWidth(img.width())
        size.setHeight(img.height())
        return img
