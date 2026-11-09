"""Lucent Store: entry point.

  lucent-store                    the store (flatpak backend)
  lucent-store --page updates     open on a page (home, updates, installed,
                                  nextgen, windows, category:<id>, app:<id>,
                                  search:<text>)
  lucent-store --fake             no flatpak: Lucent's default apps, two updates
                                  (preview on any OS; LUCENT_STORE_APPSTREAM=
                                  a Flathub appstream.xml.gz for real search data)
  --screenshot FILE [--size WxH]  render the page to a PNG and quit (previews)
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

APP_ID = "org.lucent.Store"


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="lucent-store", add_help=True)
    p.add_argument("--page", default="home")
    p.add_argument("--fake", action="store_true")
    p.add_argument("--screenshot")
    p.add_argument("--size", default="1600x1000")
    p.add_argument("--delay", type=int, default=900, help="ms before --screenshot is taken")
    return p.parse_args(argv)


def create_engine(store, backend, page: str = "home", size: str = "1600x1000"):
    """The QML engine with the store's objects and image providers, Main.qml loaded."""
    from PySide6.QtCore import QUrl
    from PySide6.QtQml import QQmlApplicationEngine

    from .icons import AppIconProvider, SymbolProvider
    from .store import I18n, qml_dir

    engine = QQmlApplicationEngine()
    engine.addImageProvider("sym", SymbolProvider())
    engine.addImageProvider("app", AppIconProvider(lambda: backend.icon_dirs, store.tiles))
    engine._l10n = I18n(engine)            # keep it alive as long as the engine
    ctx = engine.rootContext()
    ctx.setContextProperty("store", store)
    ctx.setContextProperty("l10n", engine._l10n)
    ctx.setContextProperty("startPage", page)
    w, _x, h = size.partition("x")
    ctx.setContextProperty("startWidth", int(w))
    ctx.setContextProperty("startHeight", int(h))
    engine.load(QUrl.fromLocalFile(str(qml_dir() / "Main.qml")))
    return engine


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if hasattr(os, "geteuid") and os.geteuid() == 0 and not args.fake:   # --fake: the image build's check
        print("lucent-store: don't run the store as root; it asks for permission itself when needed.",
              file=sys.stderr)
        return 1
    if args.screenshot:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        os.environ.setdefault("QT_QUICK_BACKEND", "software")

    from PySide6.QtCore import QTimer
    from PySide6.QtGui import QFontDatabase, QGuiApplication, QIcon
    from PySide6.QtQuickControls2 import QQuickStyle

    from . import catalog as catalog_mod
    from .store import Store

    QQuickStyle.setStyle("Basic")
    app = QGuiApplication(sys.argv[:1])
    app.setApplicationName("lucent-store")
    app.setApplicationDisplayName("Store")
    app.setDesktopFileName(APP_ID)        # Wayland app id = the launcher entry
    app.setWindowIcon(QIcon.fromTheme("system-software-install"))

    fonts = os.environ.get("LUCENT_STORE_FONT_DIR")
    if fonts:
        for f in Path(fonts).glob("*.ttf"):
            QFontDatabase.addApplicationFont(str(f))
    font = app.font()
    font.setFamilies(["Inter", "Noto Sans", font.family()])
    app.setFont(font)

    cat = catalog_mod.load()
    if args.fake:
        from .fake import FakeBackend
        backend = FakeBackend(cat)
        icons = os.environ.get("LUCENT_STORE_ICON_THEME_DIR")
        if icons:
            QIcon.setThemeSearchPaths([icons, *QIcon.themeSearchPaths()])
            QIcon.setThemeName("Lucent-Dark" if os.environ.get("LUCENT_STORE_THEME") == "dark" else "Lucent")
    else:
        from .backend import FlatpakBackend
        backend = FlatpakBackend(cat)

    store = Store(cat, backend)
    app.paletteChanged.connect(store.update_theme)
    hints = app.styleHints()
    if hasattr(hints, "colorSchemeChanged"):
        hints.colorSchemeChanged.connect(store.update_theme)
    engine = create_engine(store, backend, args.page, args.size)
    if not engine.rootObjects():
        return 1
    backend.start()

    if args.screenshot:
        window = engine.rootObjects()[0]

        def shoot():
            window.grabWindow().save(args.screenshot)
            app.quit()
        QTimer.singleShot(args.delay, shoot)
    return app.exec()
