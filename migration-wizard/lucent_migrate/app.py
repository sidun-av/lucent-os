"""«Переезд с Windows» — thin PySide6 front-end over the tested core modules."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Qt, Signal
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QLabel, QListWidget, QListWidgetItem,
    QProgressBar, QRadioButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWizard,
    QWizardPage,
)

from . import browsers, copying, drive_letters, firstrun, volumes, wifi, windows, xdg

FOLDER_TITLES = {
    "DESKTOP": "Рабочий стол", "DOCUMENTS": "Документы", "DOWNLOAD": "Загрузки",
    "MUSIC": "Музыка", "PICTURES": "Изображения", "VIDEOS": "Видео",
}


@dataclass
class Source:
    volume: volumes.Volume
    root: Path
    user: windows.WindowsUser


class Worker(QObject):
    """Runs a callable off the GUI thread."""
    finished = Signal(object)
    progress = Signal(int, int, str)

    def __init__(self, fn):
        super().__init__()
        self._fn = fn
        self.cancel = False

    def run(self):
        self.finished.emit(self._fn(self))


def run_in_thread(owner, fn, on_done, on_progress=None) -> Worker:
    thread = QThread(owner)
    worker = Worker(fn)
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.finished.connect(on_done)
    if on_progress:
        worker.progress.connect(on_progress)
    worker.finished.connect(thread.quit)
    thread.finished.connect(thread.deleteLater)
    owner._workers = getattr(owner, "_workers", []) + [(thread, worker)]
    thread.start()
    return worker


def _wrap(text: str) -> QLabel:
    label = QLabel(text)
    label.setWordWrap(True)
    label.setTextFormat(Qt.TextFormat.RichText)
    return label


class IntroPage(QWizardPage):
    def __init__(self, wiz: "MigrationWizard"):
        super().__init__()
        self.wiz = wiz
        self.setTitle("Переезд с Windows")
        lay = QVBoxLayout(self)
        lay.addWidget(_wrap(
            "Этот помощник перенесёт ваши документы, фотографии, музыку и закладки "
            "браузера с диска Windows. Диск Windows открывается <b>только для чтения</b> — "
            "на нём ничего не изменится."))
        self.status = _wrap("")
        lay.addWidget(self.status)
        self.never = QCheckBox("Больше не показывать при входе")
        lay.addWidget(self.never)
        lay.addStretch()

    def initializePage(self):
        found = self.wiz.all_volumes
        locked = [v for v in found if v.bitlocker]
        lines = [f"Найдено дисков Windows: <b>{len(volumes.migratable(found))}</b>."]
        if locked:
            lines.append(
                "Некоторые диски зашифрованы <b>BitLocker</b>. Откройте их в «Файлах» (Dolphin) "
                "и введите ключ восстановления BitLocker (его можно найти на "
                "account.microsoft.com/devices/recoverykey), затем запустите помощник снова.")
        if not volumes.migratable(found):
            lines.append("Читаемых дисков Windows не найдено. Подключите диск и запустите помощник ещё раз.")
        self.status.setText("<br><br>".join(lines))

    def validatePage(self):
        if self.never.isChecked():
            firstrun.mark_done(firstrun.config_dir())
        return bool(volumes.migratable(self.wiz.all_volumes))


class SourcePage(QWizardPage):
    def __init__(self, wiz: "MigrationWizard"):
        super().__init__()
        self.wiz = wiz
        self.setTitle("Чьи файлы перенести?")
        lay = QVBoxLayout(self)
        self.list = QListWidget()
        self.list.itemSelectionChanged.connect(self.completeChanged)
        self.note = _wrap("")
        lay.addWidget(self.list)
        lay.addWidget(self.note)

    def initializePage(self):
        self.list.clear()
        errors = []
        roots: dict[str, Path] = {}
        for vol in volumes.migratable(self.wiz.all_volumes):
            try:
                roots[vol.path] = Path(volumes.mount_readonly(vol))
            except OSError as exc:
                errors.append(f"{vol.path}: {exc}")
        vols = [v for v in self.wiz.all_volumes if v.path in roots]
        letters = drive_letters.assign(vols, lambda v: windows.is_windows_system(roots[v.path]))
        for vol in vols:
            root = roots[vol.path]
            letter = letters.get(vol.uuid or "")
            disk = drive_letters.display_name(letter, vol.label) if letter else (vol.label or vol.path)
            for user in windows.find_users(root):
                item = QListWidgetItem(f"{user.name}  —  {disk}")
                item.setData(Qt.ItemDataRole.UserRole, Source(vol, root, user))
                self.list.addItem(item)
        if self.list.count():
            self.list.setCurrentRow(0)
        msg = "" if self.list.count() else "На дисках Windows не найдено папок пользователей."
        if errors:
            msg += "<br>Не удалось открыть: " + "; ".join(errors)
        self.note.setText(msg)

    def isComplete(self):
        return bool(self.list.selectedItems())

    def validatePage(self):
        self.wiz.source = self.list.selectedItems()[0].data(Qt.ItemDataRole.UserRole)
        return True


class FoldersPage(QWizardPage):
    def __init__(self, wiz: "MigrationWizard"):
        super().__init__()
        self.wiz = wiz
        self.setTitle("Что перенести")
        lay = QVBoxLayout(self)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Папка", "Размер", "Куда"])
        lay.addWidget(self.tree)
        lay.addWidget(QLabel("Если файл с таким именем уже есть:"))
        self.policy = QButtonGroup(self)
        for i, (pol, text) in enumerate([
            (copying.Policy.RENAME, "Сохранить оба (файл (2).docx)"),
            (copying.Policy.NEWER, "Заменить, если файл из Windows новее"),
            (copying.Policy.SKIP, "Пропустить"),
        ]):
            btn = QRadioButton(text)
            btn.setChecked(i == 0)
            btn.setProperty("policy", pol)
            self.policy.addButton(btn)
            lay.addWidget(btn)

    def initializePage(self):
        self.tree.clear()
        targets = xdg.target_dirs()
        self.items: list[tuple[QTreeWidgetItem, Path, Path]] = []
        for key, sources in self.wiz.source.user.folders.items():
            for src in sources:
                item = QTreeWidgetItem([f"{FOLDER_TITLES[key]}  ({src.name})", "…", str(targets[key])])
                item.setCheckState(0, Qt.CheckState.Checked)
                self.tree.addTopLevelItem(item)
                self.items.append((item, src, targets[key]))
        for i in range(3):
            self.tree.resizeColumnToContents(i)
        jobs = [(i, src) for i, (_, src, _) in enumerate(self.items)]

        def measure(worker):
            return [(i, copying.scan(src)) for i, src in jobs]

        def done(results):
            for i, stats in results:
                self.items[i][0].setText(1, f"{volumes.human_size(stats.bytes)} · {stats.files} файлов")

        run_in_thread(self, measure, done)

    def validatePage(self):
        self.wiz.jobs = [(src, dst) for item, src, dst in self.items
                         if item.checkState(0) == Qt.CheckState.Checked]
        self.wiz.policy = self.policy.checkedButton().property("policy")
        return True


class ExtrasPage(QWizardPage):
    def __init__(self, wiz: "MigrationWizard"):
        super().__init__()
        self.wiz = wiz
        self.setTitle("Браузеры и Wi-Fi")
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("<b>Закладки браузеров</b>"))
        self.browsers = QListWidget()
        lay.addWidget(self.browsers)
        lay.addWidget(QLabel("<b>Сети Wi-Fi</b>"))
        lay.addWidget(_wrap(
            "Windows хранит пароли Wi-Fi в зашифрованном виде (DPAPI), привязанном к самой "
            "Windows, — расшифровать их отсюда невозможно. Поэтому переносятся только "
            "<b>названия сетей</b>; пароль спросят один раз при первом подключении."))
        self.wifi = QListWidget()
        lay.addWidget(self.wifi)

    def initializePage(self):
        self.browsers.clear()
        self.wifi.clear()
        for prof in browsers.find_profiles(self.wiz.source.user.home):
            try:
                tree = browsers.read_profile(prof)
            except Exception as exc:  # corrupt profile: show, don't crash
                item = QListWidgetItem(f"{prof.browser} ({prof.name}) — ошибка чтения: {exc}")
                item.setFlags(Qt.ItemFlag.NoItemFlags)
                self.browsers.addItem(item)
                continue
            item = QListWidgetItem(f"{prof.browser} ({prof.name}) — закладок: {browsers.count_links(tree)}")
            item.setCheckState(Qt.CheckState.Checked)
            item.setData(Qt.ItemDataRole.UserRole, (prof, tree))
            self.browsers.addItem(item)
        for prof in wifi.find_profiles(self.wiz.source.root):
            args = wifi.nmcli_add_args(prof)
            suffix = "" if args else " — корпоративная сеть, настройте вручную"
            item = QListWidgetItem(prof.ssid + suffix)
            item.setCheckState(Qt.CheckState.Checked if args else Qt.CheckState.Unchecked)
            if not args:
                item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setData(Qt.ItemDataRole.UserRole, args)
            self.wifi.addItem(item)

    def _checked(self, widget):
        return [widget.item(i).data(Qt.ItemDataRole.UserRole) for i in range(widget.count())
                if widget.item(i).checkState() == Qt.CheckState.Checked]

    def validatePage(self):
        self.wiz.bookmarks = self._checked(self.browsers)
        self.wiz.networks = self._checked(self.wifi)
        return True


class CopyPage(QWizardPage):
    def __init__(self, wiz: "MigrationWizard"):
        super().__init__()
        self.wiz = wiz
        self.setTitle("Переносим…")
        lay = QVBoxLayout(self)
        self.bar = QProgressBar()
        self.label = _wrap("")
        lay.addWidget(self.bar)
        lay.addWidget(self.label)
        lay.addStretch()
        self.done = False

    def initializePage(self):
        self.done = False
        wiz = self.wiz

        def work(worker: Worker):
            ops = [op for src, dst in wiz.jobs for op in copying.plan(src, dst, wiz.policy)]
            total = sum(op.size for op in ops) or 1
            result = copying.execute(
                ops,
                progress=lambda d, t, op: worker.progress.emit(int(d * 1000 / total), 1000, op.src.name),
                cancelled=lambda: worker.cancel,
            )
            notes = []
            if wiz.bookmarks:
                out = xdg.target_dirs()["DOCUMENTS"] / "Закладки из Windows"
                out.mkdir(parents=True, exist_ok=True)
                for prof, tree in wiz.bookmarks:
                    (out / browsers.export_name(prof)).write_text(browsers.to_netscape_html(tree), encoding="utf-8")
                notes.append(
                    f"Закладки сохранены в «{out}». В Firefox: Закладки → Управление закладками → "
                    "Импорт и резервные копии → Импорт закладок из HTML-файла.")
            added = 0
            for args in wiz.networks:
                if subprocess.run(args, capture_output=True).returncode == 0:
                    added += 1
            if wiz.networks:
                notes.append(f"Добавлено сетей Wi-Fi: {added} из {len(wiz.networks)}.")
            return result, notes

        self.worker = run_in_thread(self, work, self._finished, self._progress)

    def _progress(self, done, total, name):
        self.bar.setRange(0, total)
        self.bar.setValue(done)
        self.label.setText(name)

    def _finished(self, payload):
        self.wiz.result, self.wiz.notes = payload
        self.done = True
        self.completeChanged.emit()
        self.wiz.next()

    def isComplete(self):
        return self.done


class DonePage(QWizardPage):
    def __init__(self, wiz: "MigrationWizard"):
        super().__init__()
        self.wiz = wiz
        self.setTitle("Готово")
        self.text = _wrap("")
        lay = QVBoxLayout(self)
        lay.addWidget(self.text)
        self.errors = QListWidget()
        lay.addWidget(self.errors)

    def initializePage(self):
        r = self.wiz.result
        lines = [f"Скопировано файлов: <b>{r.copied}</b>, пропущено: {r.skipped}."]
        if r.cancelled:
            lines.append("Перенос остановлен. Уже скопированные файлы остались на месте.")
        if r.errors:
            lines.append(f"Не удалось скопировать: {len(r.errors)} (список ниже).")
        lines += self.wiz.notes
        self.text.setText("<br><br>".join(lines))
        self.errors.clear()
        self.errors.setVisible(bool(r.errors))
        for path, err in r.errors:
            self.errors.addItem(f"{path}: {err}")
        firstrun.mark_done(firstrun.config_dir())


class MigrationWizard(QWizard):
    def __init__(self, all_volumes: list[volumes.Volume]):
        super().__init__()
        self.all_volumes = all_volumes
        self.source: Source | None = None
        self.jobs: list[tuple[Path, Path]] = []
        self.policy = copying.Policy.RENAME
        self.bookmarks: list = []
        self.networks: list = []
        self.notes: list[str] = []
        self.setWindowTitle("Переезд с Windows")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.resize(760, 560)
        for page in (IntroPage, SourcePage, FoldersPage, ExtrasPage, CopyPage, DonePage):
            self.addPage(page(self))
        self.setButtonText(QWizard.WizardButton.NextButton, "Далее")
        self.setButtonText(QWizard.WizardButton.BackButton, "Назад")
        self.setButtonText(QWizard.WizardButton.CancelButton, "Отмена")
        self.setButtonText(QWizard.WizardButton.FinishButton, "Готово")

    def reject(self):
        page = self.currentPage()
        if isinstance(page, CopyPage) and not page.done:
            page.worker.cancel = True  # finish gracefully, then show the summary
            return
        super().reject()


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv if argv is None else argv
    try:
        found = volumes.run_lsblk()
    except (OSError, subprocess.CalledProcessError):
        found = []
    if "--first-run" in argv and not firstrun.should_autostart(firstrun.config_dir(), found):
        return 0
    app = QApplication(argv)
    app.setApplicationName("lucent-migrate")
    app.setDesktopFileName("org.lucent.Migrate")
    wiz = MigrationWizard(found)
    wiz.show()
    return app.exec()
