"""Card at the bottom of the window: what is happening, progress, Cancel."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout


class ProgressPanel(QFrame):
    cancel_clicked = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("card")

        self.title = QLabel()
        self.title.setObjectName("h3")
        self.percent = QLabel()
        self.percent.setObjectName("muted")
        self.current = QLabel()
        self.current.setObjectName("small")
        self.bar = QProgressBar()
        self.bar.setTextVisible(False)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self._on_cancel)

        top = QHBoxLayout()
        top.addWidget(self.title, stretch=1)
        top.addWidget(self.percent)
        text = QVBoxLayout()
        text.setSpacing(8)
        text.addLayout(top)
        text.addWidget(self.bar)
        text.addWidget(self.current)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(16)
        layout.addLayout(text, stretch=1)
        layout.addWidget(self.cancel_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        self.hide()

    def start(self, title: str, indeterminate: bool = False) -> None:
        self.title.setText(title)
        self.percent.setText("")
        self.current.setText("Starting…")
        self.bar.setRange(0, 0 if indeterminate else 100)  # (0, 0) = moving bar
        self.bar.setValue(0)
        self.cancel_btn.setEnabled(True)
        self.cancel_btn.setText("Cancel")
        self.show()

    def update_progress(self, percent: int, current: str) -> None:
        if self.bar.maximum() == 0:
            self.bar.setRange(0, 100)
        self.bar.setValue(percent)
        self.percent.setText(f"{percent}%")
        if current:
            metrics = self.current.fontMetrics()
            width = max(200, self.current.width())
            self.current.setText(metrics.elidedText(current, Qt.TextElideMode.ElideMiddle, width))

    def _on_cancel(self) -> None:
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setText("Cancelling…")
        self.cancel_clicked.emit()
