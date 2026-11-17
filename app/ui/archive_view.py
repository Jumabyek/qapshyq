"""Screen shown after an archive is opened: header, search, file tree, actions."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget,
)

from app.engine.archive import default_extract_dir
from app.engine.models import ArchiveInfo
from app.ui.file_tree import ArchiveTree
from app.ui.icons import file_icon
from app.utils import human_size


class ArchiveView(QWidget):
    extract_default = Signal()     # "Extract to 'photos'"
    extract_choose = Signal()      # "Extract to…" (pick a folder)
    close_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.info: ArchiveInfo | None = None

        # --- header ------------------------------------------------------------
        self.icon = QLabel()
        self.name = QLabel()
        self.name.setObjectName("h2")
        self.summary = QLabel()
        self.summary.setObjectName("muted")
        names = QVBoxLayout()
        names.setSpacing(2)
        names.addWidget(self.name)
        names.addWidget(self.summary)
        close_btn = QPushButton("✕  Close")
        close_btn.setObjectName("ghost")
        close_btn.clicked.connect(self.close_requested)
        header = QHBoxLayout()
        header.addWidget(self.icon)
        header.addSpacing(6)
        header.addLayout(names, stretch=1)
        header.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignTop)

        # --- toolbar -------------------------------------------------------------
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search in archive…")
        self.search.setClearButtonEnabled(True)
        self.search.setMaximumWidth(320)
        self.selection_label = QLabel()
        self.selection_label.setObjectName("muted")
        self.choose_btn = QPushButton("Extract to…")
        self.choose_btn.clicked.connect(self.extract_choose)
        self.extract_btn = QPushButton()
        self.extract_btn.setObjectName("primary")
        self.extract_btn.clicked.connect(self.extract_default)
        toolbar = QHBoxLayout()
        toolbar.addWidget(self.search)
        toolbar.addSpacing(8)
        toolbar.addWidget(self.selection_label)
        toolbar.addStretch()
        toolbar.addWidget(self.choose_btn)
        toolbar.addWidget(self.extract_btn)

        # --- tree ------------------------------------------------------------------
        self.tree = ArchiveTree()
        self.tree.itemSelectionChanged.connect(self._update_buttons)
        self.search.textChanged.connect(self.tree.apply_filter)

        hint = QLabel("Tip: double-click a file to open it without extracting the whole archive.")
        hint.setObjectName("small")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addLayout(header)
        layout.addLayout(toolbar)
        layout.addWidget(self.tree, stretch=1)
        layout.addWidget(hint)

    def set_archive(self, info: ArchiveInfo) -> None:
        self.info = info
        self.icon.setPixmap(file_icon(info.path.name).pixmap(44, 44))
        self.name.setText(info.path.name)
        parts = [info.format.upper(), f"{len(info.files)} files", human_size(info.total_size)]
        if info.has_encrypted:
            parts.append("🔒 password protected")
        self.summary.setText("   ·   ".join(parts))
        self.search.clear()
        self.tree.show_entries(info.entries)
        self._update_buttons()

    def set_busy(self, busy: bool) -> None:
        for widget in (self.extract_btn, self.choose_btn, self.tree):
            widget.setEnabled(not busy)

    def refresh_target(self) -> None:
        self._update_buttons()

    def _update_buttons(self) -> None:
        if self.info is None:
            return
        count = len(self.tree.selected_paths())
        target = default_extract_dir(self.info.path).name
        if count:
            self.selection_label.setText(f"{count} selected")
            self.extract_btn.setText(f"Extract {count} to “{target}”")
        else:
            self.selection_label.setText("")
            self.extract_btn.setText(f"Extract all to “{target}”")
        self.extract_btn.setToolTip(str(default_extract_dir(self.info.path)))
