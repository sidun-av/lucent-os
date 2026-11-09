"""Run backend calls off the UI thread; deliver results back on it."""

from __future__ import annotations

import logging
import traceback
from typing import Any, Callable

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, Signal, Slot

log = logging.getLogger("lucent-settings")


class _Dispatcher(QObject):
    finished = Signal(object, object)

    def __init__(self):
        super().__init__()
        self.finished.connect(self.deliver, Qt.ConnectionType.QueuedConnection)

    @Slot(object, object)
    def deliver(self, callback, result):
        if callback is not None:
            callback(result)


_dispatcher: _Dispatcher | None = None
# Tests set this to run everything inline (no threads, deterministic).
INLINE = False


class _Task(QRunnable):
    def __init__(self, fn: Callable[[], Any], callback: Callable[[Any], None] | None):
        super().__init__()
        self.fn, self.callback = fn, callback
        self.setAutoDelete(True)

    def run(self):
        try:
            result = self.fn()
        except Exception as e:  # noqa: BLE001 - shown to the user as an error line
            log.error("background task failed:\n%s", traceback.format_exc())
            result = e
        _dispatcher.finished.emit(self.callback, result)


def run(fn: Callable[[], Any], callback: Callable[[Any], None] | None = None) -> None:
    global _dispatcher
    if INLINE:
        try:
            result = fn()
        except Exception as e:  # noqa: BLE001
            result = e
        if callback:
            callback(result)
        return
    if _dispatcher is None:
        _dispatcher = _Dispatcher()
    QThreadPool.globalInstance().start(_Task(fn, callback))
