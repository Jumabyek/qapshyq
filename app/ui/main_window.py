"""Main window: connects the screens, dialogs and background jobs."""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import QSettings, QTimer
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPushButton,
    QStackedWidget, QVBoxLayout, QWidget,
)

from app import __version__
from app.engine import archive
from app.engine.errors import ArchiveError, Cancelled, PasswordRequired, WrongPassword
from app.engine.models import ArchiveInfo
from app.engine.sevenzip import engine_version
from app.ui.archive_view import ArchiveView
from app.ui.create_dialog import CreateDialog
from app.ui.drop_zone import DropZone, paths_from_mime
from app.ui.icons import app_icon
from app.ui.password_dialog import ask_password
from app.ui.progress_panel import ProgressPanel
from app.ui.theme import apply_theme, system_theme
from app.utils import open_path
from app.workers.task_worker import Job, TaskWorker

ARCHIVE_FILTER = ("Archives (*.zip *.rar *.7z *.tar *.gz *.tgz *.bz2 *.xz *.zst *.cab *.iso *.001);;"
                  "All files (*)")


class MainWindow(QMainWindow):
    def __init__(self, initial_paths: Optional[list[Path]] = None) -> None:
        super().__init__()
        self.setWindowTitle("Qapshyq")
        self.setWindowIcon(app_icon())
        self.setMinimumSize(760, 520)
        self.setAcceptDrops(True)

        self.settings = QSettings("Qapshyq", "Qapshyq")
        self.theme = str(self.settings.value("theme", system_theme()))
        self.worker: Optional[TaskWorker] = None
        self._busy = False
        self._on_done: Callable = lambda _result: None
        self._on_fail: Optional[Callable[[ArchiveError], bool]] = None
        self.info: Optional[ArchiveInfo] = None
        self.password = ""                 # kept in memory only, never saved
        self.temp_dirs: list[Path] = []    # for files opened by double-click

        # --- header -------------------------------------------------------------
        logo = QLabel()
        logo.setPixmap(app_icon().pixmap(30, 30))
        title = QLabel("Qapshyq")
        title.setObjectName("title")
        self.theme_btn = QPushButton()
        self.theme_btn.setObjectName("ghost")
        self.theme_btn.clicked.connect(self.toggle_theme)
        header = QHBoxLayout()
        header.addWidget(logo)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.theme_btn)

        # --- screens --------------------------------------------------------------
        self.drop_zone = DropZone()
        self.drop_zone.files_dropped.connect(self.handle_paths)
        self.drop_zone.open_clicked.connect(self.choose_archive)
        self.drop_zone.create_clicked.connect(lambda: self.open_create_dialog([]))

        self.archive_view = ArchiveView()
        self.archive_view.extract_default.connect(lambda: self.extract(choose_folder=False))
        self.archive_view.extract_choose.connect(lambda: self.extract(choose_folder=True))
        self.archive_view.close_requested.connect(self.close_archive)
        self.archive_view.tree.open_requested.connect(self.open_entry)

        self.stack = QStackedWidget()
        self.stack.addWidget(self.drop_zone)
        self.stack.addWidget(self.archive_view)

        self.progress = ProgressPanel()
        self.progress.cancel_clicked.connect(self.cancel_task)

        self.status = QLabel()
        self.status.setObjectName("small")
        self._default_status = (f"Qapshyq {__version__}   ·   engine: {engine_version()}   ·   "
                                "offline, your files never leave this computer")
        self.status.setText(self._default_status)

        root = QVBoxLayout()
        root.setContentsMargins(24, 18, 24, 12)
        root.setSpacing(14)
        root.addLayout(header)
        root.addWidget(self.stack, stretch=1)
        root.addWidget(self.progress)
        root.addWidget(self.status)
        container = QWidget()
        container.setLayout(root)
        self.setCentralWidget(container)

        self.apply_theme()
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.resize(980, 660)
        if initial_paths:
            QTimer.singleShot(0, lambda: self.handle_paths(initial_paths))

    # ======================================================================
    # Theme
    # ======================================================================
    def apply_theme(self) -> None:
        apply_theme(QApplication.instance(), self.theme)
        self.theme_btn.setText("☀  Light" if self.theme == "dark" else "🌙  Dark")

    def toggle_theme(self) -> None:
        self.theme = "light" if self.theme == "dark" else "dark"
        self.settings.setValue("theme", self.theme)
        self.apply_theme()

    # ======================================================================
    # Entry points: drop, open, create
    # ======================================================================
    def dragEnterEvent(self, event) -> None:
        if not self.is_busy() and paths_from_mime(event.mimeData()):
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        paths = paths_from_mime(event.mimeData())
        if paths:
            event.acceptProposedAction()
            self.handle_paths(paths)

    def handle_paths(self, paths: list[Path]) -> None:
        """One archive -> open it. Anything else -> offer to compress it."""
        if self.is_busy():
            return
        if len(paths) == 1 and archive.looks_like_archive(paths[0]):
            self.open_archive(paths[0])
        else:
            self.open_create_dialog(paths)

    def choose_archive(self) -> None:
        start = str(self.settings.value("last_dir", str(Path.home())))
        path, _ = QFileDialog.getOpenFileName(self, "Open archive", start, ARCHIVE_FILTER)
        if path:
            self.settings.setValue("last_dir", str(Path(path).parent))
            self.open_archive(Path(path))

    # ======================================================================
    # Opening (listing) an archive
    # ======================================================================
    def open_archive(self, path: Path, password: str = "") -> None:
        def job(_progress, token):
            return archive.list_archive(path, password, token)

        def done(info: ArchiveInfo) -> None:
            info.headers_encrypted = bool(password)
            self.info = info
            self.password = password
            self.archive_view.set_archive(info)
            self.stack.setCurrentWidget(self.archive_view)
            self.setWindowTitle(f"{path.name} — Qapshyq")

        def failed(error: ArchiveError) -> bool:
            if isinstance(error, (PasswordRequired, WrongPassword)):
                new = ask_password(self, path.name, wrong=isinstance(error, WrongPassword))
                if new:
                    QTimer.singleShot(0, lambda: self.open_archive(path, new))
                return True
            return False

        self.run_task(f"Opening {path.name}", job, done, failed, indeterminate=True)

    def close_archive(self) -> None:
        self.info = None
        self.password = ""
        self.stack.setCurrentWidget(self.drop_zone)
        self.setWindowTitle("Qapshyq")

    # ======================================================================
    # Extracting
    # ======================================================================
    def extract(self, choose_folder: bool) -> None:
        if self.info is None:
            return
        path = self.info.path
        if choose_folder:
            folder = QFileDialog.getExistingDirectory(self, "Extract to folder", str(path.parent))
            if not folder:
                return
            destination = Path(folder)
        else:
            destination = archive.default_extract_dir(path)
        items = self.archive_view.tree.selected_paths() or None

        password = self.password
        if self.info.has_encrypted and not password:
            password = ask_password(self, path.name) or ""
            if not password:
                return
        self._extract(path, destination, items, password)

    def _extract(self, path: Path, destination: Path, items: Optional[list[str]],
                 password: str) -> None:
        def job(progress, token):
            return archive.extract(path, destination, items, password, progress, token)

        def done(folder: Path) -> None:
            self.password = password
            self.archive_view.refresh_target()   # next default folder may be "(2)"
            what = f"{len(items)} item(s)" if items else "Everything"
            self.show_success("Extraction complete", f"{what} extracted to:\n{folder}", folder)

        def failed(error: ArchiveError) -> bool:
            if isinstance(error, (PasswordRequired, WrongPassword)):
                new = ask_password(self, path.name, wrong=bool(password))
                if new:
                    QTimer.singleShot(0, lambda: self._extract(path, destination, items, new))
                return True
            return False

        self.run_task(f"Extracting {path.name}", job, done, failed)

    def open_entry(self, inner_path: str) -> None:
        """Double-click: extract one file to a temp folder and open it."""
        if self.info is None or self.is_busy():
            return
        path, password = self.info.path, self.password
        if self.info.has_encrypted and not password:
            password = ask_password(self, path.name) or ""
            if not password:
                return
        temp = Path(tempfile.mkdtemp(prefix="qapshyq-"))
        self.temp_dirs.append(temp)

        def job(progress, token):
            archive.extract(path, temp, [inner_path], password, progress, token)
            return temp / inner_path

        def done(file_path: Path) -> None:
            self.password = password
            open_path(file_path)

        self.run_task(f"Opening {inner_path.rsplit('/', 1)[-1]}", job, done)

    # ======================================================================
    # Creating
    # ======================================================================
    def open_create_dialog(self, sources: list[Path]) -> None:
        if self.is_busy():
            return
        dialog = CreateDialog(self, sources)
        if not dialog.exec():
            return
        options = dialog.options()

        def job(progress, token):
            return archive.create(options, progress, token)

        def done(output: Path) -> None:
            self.show_success("Archive created", f"Saved as:\n{output}", output.parent)

        self.run_task(f"Compressing to {options.output.name}", job, done)

    # ======================================================================
    # Running background jobs
    # ======================================================================
    def is_busy(self) -> bool:
        return self._busy

    def run_task(self, title: str, job: Job, on_done: Callable,
                 on_fail: Optional[Callable[[ArchiveError], bool]] = None,
                 indeterminate: bool = False) -> None:
        """Run `job` in the background with the progress panel visible.

        on_done(result) runs on success. on_fail(error) may handle an error
        itself (e.g. ask for a password) by returning True.
        """
        if self.is_busy():
            return
        if self.worker is not None:
            self.worker.wait()   # previous thread has already returned; let it end
        self._on_done, self._on_fail = on_done, on_fail
        worker = TaskWorker(job)
        # Connect to methods of this window (a QObject living in the UI thread),
        # so Qt delivers the signals safely in the UI thread.
        worker.progressed.connect(self.progress.update_progress)
        worker.succeeded.connect(self._task_succeeded)
        worker.failed.connect(self._task_failed)
        worker.finished.connect(self._task_finished)
        self.worker = worker
        self.progress.start(title, indeterminate)
        self._set_busy(True)
        worker.start()

    def cancel_task(self) -> None:
        if self.worker:
            self.worker.cancel()

    def _task_succeeded(self, result) -> None:
        self._finish_ui()
        self._on_done(result)

    def _task_failed(self, error: ArchiveError) -> None:
        self._finish_ui()
        if isinstance(error, Cancelled):
            self.flash_status("Cancelled.")
            return
        if self._on_fail and self._on_fail(error):
            return
        self.show_error(error)

    def _finish_ui(self) -> None:
        self.progress.hide()
        self._set_busy(False)

    def _task_finished(self) -> None:
        if self.worker is not None and self.sender() is self.worker:
            self.worker.wait()   # thread is ending; make sure it is fully done
            self.worker = None

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.drop_zone.open_btn.setEnabled(not busy)
        self.drop_zone.create_btn.setEnabled(not busy)
        self.archive_view.set_busy(busy)

    # ======================================================================
    # Messages
    # ======================================================================
    def flash_status(self, text: str) -> None:
        self.status.setText(text)
        QTimer.singleShot(4000, lambda: self.status.setText(self._default_status))

    def show_error(self, error: ArchiveError) -> None:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle("Qapshyq")
        box.setText(error.message)
        if error.details.strip():
            box.setDetailedText(error.details.strip()[-3000:])
        box.exec()

    def show_success(self, title: str, text: str, folder: Path) -> None:
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setIconPixmap(app_icon().pixmap(48, 48))
        box.setText(f"<b>{title}</b>")
        box.setInformativeText(text)
        open_btn = box.addButton("Open folder", QMessageBox.ButtonRole.AcceptRole)
        box.addButton("Close", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        if box.clickedButton() is open_btn:
            open_path(folder)

    # ======================================================================
    # Closing
    # ======================================================================
    def closeEvent(self, event) -> None:
        if self.is_busy():
            answer = QMessageBox.question(self, "Qapshyq", "A task is still running. Stop it and quit?")
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self.worker.cancel()
        if self.worker is not None:
            self.worker.wait(5000)
        self.settings.setValue("geometry", self.saveGeometry())
        for temp in self.temp_dirs:
            shutil.rmtree(temp, ignore_errors=True)
        event.accept()
