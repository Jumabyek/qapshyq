"""Dialog for making a new ZIP or 7Z archive."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QDialog, QFileDialog, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from app.engine.models import CreateOptions
from app.ui.icons import icon_for
from app.utils import unique_path

FORMAT_HINTS = {
    "zip": "ZIP opens everywhere — best for sending to other people.",
    "7z": "7Z makes smaller files — best for backups and big folders.",
}


def _segment(labels: list[tuple[str, str]], checked: str) -> tuple[QHBoxLayout, QButtonGroup]:
    """A row of toggle buttons where exactly one is active."""
    row = QHBoxLayout()
    row.setSpacing(6)
    group = QButtonGroup(row)
    for key, text in labels:
        button = QPushButton(text)
        button.setObjectName("segment")
        button.setCheckable(True)
        button.setProperty("key", key)
        button.setChecked(key == checked)
        group.addButton(button)
        row.addWidget(button)
    row.addStretch()
    return row, group


def _checked_key(group: QButtonGroup) -> str:
    return group.checkedButton().property("key")


class CreateDialog(QDialog):
    def __init__(self, parent: QWidget, sources: list[Path]) -> None:
        super().__init__(parent)
        self.setWindowTitle("Create archive")
        self.setMinimumWidth(620)

        title = QLabel("Create archive")
        title.setObjectName("h2")

        # --- files ------------------------------------------------------------------
        self.list = QListWidget()
        self.list.setIconSize(QSize(20, 20))
        self.list.setMinimumHeight(130)
        add_files = QPushButton("+ Files…")
        add_files.clicked.connect(self._add_files)
        add_folder = QPushButton("+ Folder…")
        add_folder.clicked.connect(self._add_folder)
        remove = QPushButton("Remove")
        remove.clicked.connect(self._remove_selected)
        file_buttons = QHBoxLayout()
        for button in (add_files, add_folder, remove):
            file_buttons.addWidget(button)
        file_buttons.addStretch()

        # --- output -------------------------------------------------------------------
        self.output = QLineEdit()
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._browse_output)
        output_row = QHBoxLayout()
        output_row.addWidget(self.output, stretch=1)
        output_row.addWidget(browse)

        # --- format and level -----------------------------------------------------------
        format_row, self.format_group = _segment([("zip", "ZIP"), ("7z", "7Z")], "zip")
        self.format_hint = QLabel(FORMAT_HINTS["zip"])
        self.format_hint.setObjectName("small")
        self.format_hint.setWordWrap(True)
        level_row, self.level_group = _segment(
            [("fast", "Fast"), ("normal", "Normal"), ("maximum", "Maximum")], "normal")
        self.format_group.buttonClicked.connect(self._format_changed)

        # --- password ---------------------------------------------------------------------
        self.password = QLineEdit()
        self.password.setPlaceholderText("Password (optional)")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm = QLineEdit()
        self.confirm.setPlaceholderText("Repeat password")
        self.confirm.setEchoMode(QLineEdit.EchoMode.Password)
        show = QCheckBox("Show")
        show.toggled.connect(self._toggle_show)
        password_row = QHBoxLayout()
        password_row.addWidget(self.password)
        password_row.addWidget(self.confirm)
        password_row.addWidget(show)
        self.encrypt_names = QCheckBox("Also hide file names (7Z only)")
        self.password.textChanged.connect(self._update_state)
        password_hint = QLabel("AES-256 encryption. If the password is lost, the files cannot be recovered.")
        password_hint.setObjectName("small")
        password_hint.setWordWrap(True)

        # --- buttons --------------------------------------------------------------------------
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        self.create_btn = QPushButton("Create")
        self.create_btn.setObjectName("primary")
        self.create_btn.setDefault(True)
        self.create_btn.clicked.connect(self._on_create)
        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(cancel)
        buttons.addWidget(self.create_btn)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)
        rows = [
            ("Files and folders", self.list), (None, file_buttons),
            ("Save as", output_row), ("Format", format_row), (None, self.format_hint),
            ("Compression", level_row), ("Password", password_row),
            (None, self.encrypt_names), (None, password_hint),
        ]
        for row, (label, content) in enumerate(rows):
            if label:
                caption = QLabel(label)
                caption.setObjectName("h3")
                grid.addWidget(caption, row, 0)
            if isinstance(content, QWidget):
                grid.addWidget(content, row, 1)
            else:
                grid.addLayout(content, row, 1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(14)
        layout.addWidget(title)
        layout.addLayout(grid)
        layout.addLayout(buttons)

        self._add_paths(sources)
        self._update_state()

    # --- sources --------------------------------------------------------------------
    def sources(self) -> list[Path]:
        return [Path(self.list.item(i).toolTip()) for i in range(self.list.count())]

    def _add_paths(self, paths: list[Path]) -> None:
        existing = set(self.sources())
        for path in paths:
            if path in existing or not path.exists():
                continue
            item = QListWidgetItem(icon_for(path.name, path.is_dir()), path.name)
            item.setToolTip(str(path))
            self.list.addItem(item)
        if not self.output.text() and self.list.count():
            self.output.setText(str(self._suggest_output()))
        self._update_state()

    def _add_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(self, "Add files")
        self._add_paths([Path(f) for f in files])

    def _add_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Add folder")
        if folder:
            self._add_paths([Path(folder)])

    def _remove_selected(self) -> None:
        for item in self.list.selectedItems():
            self.list.takeItem(self.list.row(item))
        self._update_state()

    # --- output ---------------------------------------------------------------------
    def _extension(self) -> str:
        return "." + _checked_key(self.format_group)

    def _with_extension(self, path: Path) -> Path:
        """Swap .zip <-> .7z, or append the extension if there is none."""
        if path.suffix.lower() in (".zip", ".7z"):
            return path.with_suffix(self._extension())
        return path.with_name(path.name + self._extension())

    def _suggest_output(self) -> Path:
        sources = self.sources()
        first = sources[0]
        name = (first.stem if first.is_file() else first.name) if len(sources) == 1 else "Archive"
        return unique_path(first.parent / f"{name}{self._extension()}")

    def _browse_output(self) -> None:
        fmt = _checked_key(self.format_group)
        path, _ = QFileDialog.getSaveFileName(
            self, "Save archive as", self.output.text(), f"{fmt.upper()} archive (*.{fmt})")
        if path:
            self.output.setText(str(self._with_extension(Path(path))))

    def _format_changed(self) -> None:
        fmt = _checked_key(self.format_group)
        self.format_hint.setText(FORMAT_HINTS[fmt])
        if self.output.text():
            self.output.setText(str(self._with_extension(Path(self.output.text()))))
        self._update_state()

    # --- password -----------------------------------------------------------------------
    def _toggle_show(self, on: bool) -> None:
        mode = QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password
        self.password.setEchoMode(mode)
        self.confirm.setEchoMode(mode)

    def _update_state(self) -> None:
        has_password = bool(self.password.text())
        is_7z = _checked_key(self.format_group) == "7z"
        self.confirm.setEnabled(has_password)
        self.encrypt_names.setEnabled(has_password and is_7z)
        if not (has_password and is_7z):
            self.encrypt_names.setChecked(False)
        self.create_btn.setEnabled(self.list.count() > 0)

    # --- finishing -----------------------------------------------------------------------
    def _on_create(self) -> None:
        if not self.output.text().strip():
            QMessageBox.warning(self, "Create archive", "Choose where to save the archive.")
            return
        if self.password.text() != self.confirm.text():
            QMessageBox.warning(self, "Create archive", "The two passwords do not match.")
            return
        output = self._with_extension(Path(self.output.text().strip()))
        for source in self.sources():
            if source.is_dir() and source in output.parents:
                QMessageBox.warning(self, "Create archive",
                                    "Save the archive outside the folder you are compressing.")
                return
        if output.exists():
            answer = QMessageBox.question(self, "Create archive",
                                          f"“{output.name}” already exists. Replace it?")
            if answer != QMessageBox.StandardButton.Yes:
                return
        self.output.setText(str(output))
        self.accept()

    def options(self) -> Optional[CreateOptions]:
        return CreateOptions(
            sources=self.sources(),
            output=Path(self.output.text()),
            format=_checked_key(self.format_group),
            level=_checked_key(self.level_group),
            password=self.password.text(),
            encrypt_names=self.encrypt_names.isChecked(),
        )
