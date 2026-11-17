"""The home screen: a big area where files can be dropped."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from app.ui.icons import app_icon


def paths_from_mime(mime) -> list[Path]:
    """Local file paths from a drag-and-drop event."""
    return [Path(url.toLocalFile()) for url in mime.urls() if url.isLocalFile()]


class DropZone(QFrame):
    files_dropped = Signal(list)      # list[Path]
    open_clicked = Signal()
    create_clicked = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.setProperty("dragging", False)

        logo = QLabel()
        logo.setPixmap(app_icon().pixmap(96, 96))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Drop files here")
        title.setObjectName("h2")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Drop an archive to open it  ·  drop files or folders to compress them")
        subtitle.setObjectName("muted")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)

        self.open_btn = QPushButton("Open archive…")
        self.open_btn.setObjectName("primary")
        self.open_btn.clicked.connect(self.open_clicked)
        self.create_btn = QPushButton("Create archive…")
        self.create_btn.clicked.connect(self.create_clicked)
        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(self.open_btn)
        buttons.addWidget(self.create_btn)
        buttons.addStretch()

        formats = QLabel("ZIP · RAR · 7Z · TAR · GZ    —    works offline, nothing is uploaded")
        formats.setObjectName("small")
        formats.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout(self)
        layout.addStretch()
        layout.addWidget(logo)
        layout.addSpacing(8)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(18)
        layout.addLayout(buttons)
        layout.addSpacing(18)
        layout.addWidget(formats)
        layout.addStretch()

    # --- drag & drop ---------------------------------------------------------
    def _set_dragging(self, value: bool) -> None:
        self.setProperty("dragging", value)
        self.style().unpolish(self)   # re-apply the [dragging="true"] style
        self.style().polish(self)

    def dragEnterEvent(self, event) -> None:
        if paths_from_mime(event.mimeData()):
            event.acceptProposedAction()
            self._set_dragging(True)

    def dragLeaveEvent(self, event) -> None:
        self._set_dragging(False)

    def dropEvent(self, event) -> None:
        self._set_dragging(False)
        paths = paths_from_mime(event.mimeData())
        if paths:
            event.acceptProposedAction()
            self.files_dropped.emit(paths)
