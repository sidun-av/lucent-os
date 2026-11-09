""""Move from Windows" — thin PySide6 front-end over the tested core modules."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QLabel, QListWidget, QListWidgetItem,
    QProgressBar, QRadioButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWizard,
    QWizardPage,
)

from . import browsers, copying, drive_letters, firstrun, style, volumes, wifi, windows, xdg
from .i18n import N_, _, ngettext

FOLDER_TITLES = {
    "DESKTOP": N_("Desktop"), "DOCUMENTS": N_("Documents"), "DOWNLOAD": N_("Downloads"),
    "MUSIC": N_("Music"), "PICTURES": N_("Pictures"), "VIDEOS": N_("Videos"),
}
FOLDER_ICONS = {
    "DESKTOP": "user-desktop", "DOCUMENTS": "folder-documents", "DOWNLOAD": "folder-download",
    "MUSIC": "folder-music", "PICTURES": "folder-pictures", "VIDEOS": "folder-videos",
}


def folder_label(key: str, src: Path) -> str:
    """"Documents", or "Documents  (OneDrive)" when the Windows folder is
    elsewhere / named differently, so the source is never ambiguous."""
    title = _(FOLDER_TITLES[key])
    return title if src.name in (title, FOLDER_TITLES[key]) else f"{title}  ({src.name})"


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
        self.setTitle(_("Move from Windows"))
        lay = QVBoxLayout(self)
        lay.addWidget(_wrap(_(
            "This assistant copies your documents, photos, music and browser bookmarks "
            "from a Windows disk. The Windows disk is opened <b>read-only</b>: nothing "
            "on it will change.")))
        self.status = _wrap("")
        lay.addWidget(self.status)
        self.never = QCheckBox(_("Don't show this again at login"))
        lay.addWidget(self.never)
        lay.addStretch()

    def initializePage(self):
        found = self.wiz.all_volumes
        locked = [v for v in found if v.bitlocker]
        lines = [_("Windows disks found: <b>{n}</b>.").format(n=len(volumes.migratable(found)))]
        if locked:
            lines.append(_(
                "Some disks are encrypted with <b>BitLocker</b>. Open them in Files (Dolphin) "
                "and enter the BitLocker recovery key (you can find it at "
                "account.microsoft.com/devices/recoverykey), then run this assistant again."))
        if not volumes.migratable(found):
            lines.append(_("No readable Windows disks found. Connect the disk and run this assistant again."))
        self.status.setText("<br><br>".join(lines))

    def validatePage(self):
        if self.never.isChecked():
            firstrun.mark_done(firstrun.config_dir())
        return bool(volumes.migratable(self.wiz.all_volumes))


class SourcePage(QWizardPage):
    def __init__(self, wiz: "MigrationWizard"):
        super().__init__()
        self.wiz = wiz
        self.setTitle(_("Whose files should be copied?"))
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
        msg = "" if self.list.count() else _("No user folders were found on the Windows disks.")
        if errors:
            msg += "<br>" + _("Could not open: {errors}").format(errors="; ".join(errors))
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
        self.setTitle(_("What to copy"))
        lay = QVBoxLayout(self)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([_("Folder"), _("Size"), _("Copy to")])
        lay.addWidget(self.tree)
        lay.addWidget(QLabel(_("If a file with the same name already exists:")))
        self.policy = QButtonGroup(self)
        for i, (pol, text) in enumerate([
            (copying.Policy.RENAME, _("Keep both (file (2).docx)")),
            (copying.Policy.NEWER, _("Replace if the Windows file is newer")),
            (copying.Policy.SKIP, _("Skip")),
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
                item = QTreeWidgetItem([folder_label(key, src), "…", str(targets[key])])
                item.setIcon(0, QIcon.fromTheme(FOLDER_ICONS[key], QIcon.fromTheme("folder")))
                item.setCheckState(0, Qt.CheckState.Checked)
                self.tree.addTopLevelItem(item)
                self.items.append((item, src, targets[key]))
        for i in range(3):
            self.tree.resizeColumnToContents(i)
        jobs = [(i, src) for i, (_item, src, _dst) in enumerate(self.items)]

        def measure(worker):
            return [(i, copying.scan(src)) for i, src in jobs]

        def done(results):
            for i, stats in results:
                self.items[i][0].setText(1, volumes.human_size(stats.bytes) + " · " + ngettext(
                    "{n} file", "{n} files", stats.files).format(n=stats.files))

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
        self.setTitle(_("Browsers and Wi-Fi"))
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("<b>" + _("Browser bookmarks") + "</b>"))
        self.browsers = QListWidget()
        lay.addWidget(self.browsers)
        lay.addWidget(QLabel("<b>" + _("Wi-Fi networks") + "</b>"))
        lay.addWidget(_wrap(_(
            "Windows keeps Wi-Fi passwords encrypted (DPAPI) and tied to that Windows "
            "installation, so they cannot be decrypted from here. Only the <b>network "
            "names</b> are copied; you will be asked for each password once, on first connect.")))
        self.wifi = QListWidget()
        lay.addWidget(self.wifi)

    def initializePage(self):
        self.browsers.clear()
        self.wifi.clear()
        for prof in browsers.find_profiles(self.wiz.source.user.home):
            try:
                tree = browsers.read_profile(prof)
            except Exception as exc:  # corrupt profile: show, don't crash
                item = QListWidgetItem(_("{browser} ({profile}): could not read: {error}").format(
                    browser=prof.browser, profile=prof.name, error=exc))
                item.setFlags(Qt.ItemFlag.NoItemFlags)
                self.browsers.addItem(item)
                continue
            item = QListWidgetItem(_("{browser} ({profile}): {n} bookmarks").format(
                browser=prof.browser, profile=prof.name, n=browsers.count_links(tree)))
            item.setCheckState(Qt.CheckState.Checked)
            item.setData(Qt.ItemDataRole.UserRole, (prof, tree))
            self.browsers.addItem(item)
        for prof in wifi.find_profiles(self.wiz.source.root):
            args = wifi.nmcli_add_args(prof)
            suffix = "" if args else " — " + _("enterprise network, set it up manually")
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
        self.setTitle(_("Copying…"))
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
                out = xdg.target_dirs()["DOCUMENTS"] / _("Bookmarks from Windows")
                out.mkdir(parents=True, exist_ok=True)
                for prof, tree in wiz.bookmarks:
                    (out / browsers.export_name(prof)).write_text(browsers.to_netscape_html(tree), encoding="utf-8")
                notes.append(_(
                    "Bookmarks were saved to “{folder}”. In Firefox: Bookmarks → Manage Bookmarks → "
                    "Import and Backup → Import Bookmarks from HTML.").format(folder=out))
            added = 0
            for args in wiz.networks:
                if subprocess.run(args, capture_output=True).returncode == 0:
                    added += 1
            if wiz.networks:
                notes.append(_("Wi-Fi networks added: {added} of {total}.").format(added=added, total=len(wiz.networks)))
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
        self.setTitle(_("Done"))
        self.text = _wrap("")
        lay = QVBoxLayout(self)
        lay.addWidget(self.text)
        self.errors = QListWidget()
        lay.addWidget(self.errors)

    def initializePage(self):
        r = self.wiz.result
        lines = [_("Files copied: <b>{copied}</b>, skipped: {skipped}.").format(copied=r.copied, skipped=r.skipped)]
        if r.cancelled:
            lines.append(_("Copying was stopped. Files that were already copied stay where they are."))
        if r.errors:
            lines.append(_("Could not copy: {n} (see the list below).").format(n=len(r.errors)))
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
        self.setWindowTitle(_("Move from Windows"))
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.resize(760, 560)
        for page in (IntroPage, SourcePage, FoldersPage, ExtrasPage, CopyPage, DonePage):
            self.addPage(page(self))
        self.setButtonText(QWizard.WizardButton.NextButton, _("Next"))
        self.setButtonText(QWizard.WizardButton.BackButton, _("Back"))
        self.setButtonText(QWizard.WizardButton.CancelButton, _("Cancel"))
        self.setButtonText(QWizard.WizardButton.FinishButton, _("Finish"))
        self.sidebar = style.apply(self)  # Lucent look: step sidebar, headings, cards

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
