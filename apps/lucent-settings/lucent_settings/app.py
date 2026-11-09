"""Lucent Settings: the ten things people actually change, in plain words.

PySide6 + QML. Pages live in qml/pages, the Lucent look (tokens from
docs/mockups/lucent.css) in qml/Lucent. Each page talks to one controller
in sections.py, which runs the backends (backends/*) in the background.

  lucent-settings [--page network|bluetooth|display|sound|appearance|users|
                          updates|winapps|habits|about]
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from PySide6.QtCore import Property, QByteArray, QEvent, QFileSystemWatcher, QObject, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QColor, QFontDatabase, QGuiApplication, QIcon, QImage, QPainter
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickImageProvider, QQuickWindow
from PySide6.QtSvg import QSvgRenderer

from . import i18n, kconfig, symbols
from .backends import appearance
from .i18n import _, ngettext
from .run import Runner
from .sections import sections

QML_DIR = Path(__file__).parent / "qml"
# Figtree (SIL OFL 1.1, fonts/OFL.txt): the 2026 design's typeface, bundled
# so the system's own fonts stay as they are.
FONTS = sorted((Path(__file__).parent / "fonts").glob("*.ttf"))
PAGES = ["network", "bluetooth", "display", "sound", "appearance", "habits", "users", "updates", "winapps", "about"]


class SymbolProvider(QQuickImageProvider):
    """image://sym/<name>/<RRGGBB or AARRGGBB>: a line symbol in any colour."""

    def __init__(self):
        super().__init__(QQuickImageProvider.ImageType.Image)

    def requestImage(self, id_, size, requested):
        name, _sep, color = id_.partition("/")
        w = requested.width() if requested.width() > 0 else 48
        h = requested.height() if requested.height() > 0 else w
        img = QImage(w, h, QImage.Format.Format_ARGB32_Premultiplied)
        img.fill(Qt.GlobalColor.transparent)
        c = QColor("#" + color.lstrip("#")) if color else QColor("#000000")
        hex_color = c.name(QColor.NameFormat.HexRgb)
        renderer = QSvgRenderer(QByteArray(symbols.svg(name, hex_color)))
        p = QPainter(img)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if c.alpha() < 255:
            p.setOpacity(c.alphaF())
        renderer.render(p)
        p.end()
        if size is not None:
            size.setWidth(w)
            size.setHeight(h)
        return img


class System(QObject):
    """What every page needs: light/dark, accent, translations.

    Light/dark and the accent follow ~/.config/kdeglobals (watched), which
    every theme switch rewrites, whoever makes it (this app, Quick Settings,
    Auto at sunset); the Qt palette is only the fallback."""

    themeChanged = Signal()

    def __init__(self, app: QGuiApplication, start_page: str):
        super().__init__()
        self._app = app
        self._page = start_page
        app.installEventFilter(self)
        self._watch = QFileSystemWatcher(self)
        cfg = kconfig.config_home()
        self._watch.addPath(str(cfg))  # kdeglobals is replaced, not edited in place
        if (cfg / "kdeglobals").exists():
            self._watch.addPath(str(cfg / "kdeglobals"))
        self._watch.directoryChanged.connect(self._config_changed)
        self._watch.fileChanged.connect(self._config_changed)
        self._debounce = QTimer(self, singleShot=True, interval=150)
        self._debounce.timeout.connect(self.themeChanged)

    def _config_changed(self, _path):
        kg = kconfig.config_home() / "kdeglobals"
        if kg.exists() and str(kg) not in self._watch.files():
            self._watch.addPath(str(kg))
        self._debounce.start()

    def eventFilter(self, obj, ev):
        if obj is self._app and ev.type() == QEvent.Type.ApplicationPaletteChange:
            self._debounce.start()
        return False

    @staticmethod
    def _rgb(group: str) -> QColor | None:
        value = kconfig.read("kdeglobals", group, "BackgroundNormal", "")
        try:
            r, g, b = (int(x) for x in value.split(",")[:3])
        except ValueError:
            return None
        return QColor(r, g, b)

    def _dark(self):
        forced = os.environ.get("LUCENT_SETTINGS_THEME")
        if forced in ("light", "dark"):
            return forced == "dark"
        window = self._rgb("Colors:Window") or self._app.palette().window().color()
        return window.lightness() < 128

    def _accent(self):
        if os.environ.get("LUCENT_SETTINGS_THEME"):
            return QColor("#5b8bff" if self._dark() else "#3b6ef5")
        own = appearance.chosen_accent()
        if own:
            return QColor(own)
        return self._rgb("Colors:Selection") or self._app.palette().highlight().color()

    dark = Property(bool, _dark, notify=themeChanged)
    accent = Property(QColor, _accent, notify=themeChanged)
    startPage = Property(str, lambda self: self._page, constant=True)
    language = Property(str, lambda self: i18n.language(), constant=True)

    @Slot(str, result=str)
    def tr(self, text):
        return _(text)

    @Slot(str, str, int, result=str)
    def trn(self, singular, plural, n):
        return ngettext(singular, plural, n).replace("{n}", str(n))

    @Slot(str, result=bool)
    def exists(self, url):
        return Path(url.removeprefix("file://")).exists()


def create_engine(app: QGuiApplication, runner, start_page: str = "appearance"):
    for font in FONTS:
        QFontDatabase.addApplicationFont(str(font))
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(QML_DIR))
    engine.addImageProvider("sym", SymbolProvider())
    system = System(app, start_page)
    system.setParent(engine)
    # Children of the engine: destroyed after its QML, never before.
    secs = sections(runner, engine)
    ctx = engine.rootContext()
    ctx.setContextProperty("System", system)
    for name, sec in secs.items():
        ctx.setContextProperty(name.capitalize() + "Page", sec)
    engine.load(str(QML_DIR / "Main.qml"))
    return engine, system, secs


class OfflineRunner(Runner):
    """--check: every system tool "fails", nothing is started."""

    def run(self, argv, *, timeout=30, stdin=None):
        from .run import Result
        return Result(1, "", "offline check")

    def spawn(self, argv):
        return False


def check(app: QGuiApplication) -> int:
    """Load the window and every page offscreen; fail on any QML warning."""
    from PySide6.QtCore import QtMsgType, qInstallMessageHandler

    problems: list[str] = []

    def handler(kind, ctx, msg):
        if kind in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg) and \
                (ctx.file or "").endswith(".qml"):
            problems.append(msg)
    qInstallMessageHandler(handler)
    engine, _system, _secs = create_engine(app, OfflineRunner())
    roots = engine.rootObjects()
    if not roots:
        problems.append("Main.qml did not load")
    else:
        for page in PAGES:
            roots[0].setProperty("page", page)
            for _ in range(10):
                app.processEvents()
    for p in problems:
        print("lucent-settings --check:", p, file=sys.stderr)
    print(f"lucent-settings --check: {len(PAGES)} pages, {len(problems)} QML problems")
    return 1 if problems else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lucent-settings")
    parser.add_argument("--page", choices=PAGES, default="appearance")
    parser.add_argument("--check", action="store_true", help="load every page offscreen and exit (build check)")
    args, qt_args = parser.parse_known_args(argv if argv is not None else sys.argv[1:])
    if os.geteuid() == 0 and not args.check:
        print("lucent-settings: don't run Settings as root; it asks for permission itself when needed.",
              file=sys.stderr)
        return 1
    i18n.setup()
    QQuickWindow.setTextRenderType(QQuickWindow.TextRenderType.NativeTextRendering)
    if args.check:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QGuiApplication([sys.argv[0], *qt_args])
    app.setApplicationName("lucent-settings")
    app.setOrganizationName("Lucent")
    app.setApplicationDisplayName(_("Settings"))
    app.setDesktopFileName("org.lucent.Settings")
    app.setWindowIcon(QIcon.fromTheme("systemsettings"))
    if args.check:
        return check(app)
    engine, _system, _secs = create_engine(app, Runner(), args.page)
    if not engine.rootObjects():
        return 1
    return app.exec()


