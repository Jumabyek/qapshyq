"""Small dialog that asks for an archive password."""
from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QCheckBox, QDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget,
)


class PasswordDialog(QDialog):
    def __init__(self, parent: QWidget, archive_name: str, wrong: bool) -> None:
        super().__init__(parent)
        self.setWindowTitle("Password required")
        self.setMinimumWidth(420)

        title = QLabel("🔒  Password required")
        title.setObjectName("h2")
        text = QLabel(f"“{archive_name}” is protected. Enter its password to continue.")
        text.setObjectName("muted")
        text.setWordWrap(True)
        error = QLabel("That password is not correct. Please try again.")
        error.setObjectName("error")
        error.setVisible(wrong)

        self.field = QLineEdit()
        self.field.setEchoMode(QLineEdit.EchoMode.Password)
        self.field.setPlaceholderText("Password")
        show = QCheckBox("Show password")
        show.toggled.connect(lambda on: self.field.setEchoMode(
            QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password))

        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        self.ok = QPushButton("Unlock")
        self.ok.setObjectName("primary")
        self.ok.setDefault(True)
        self.ok.setEnabled(False)
        self.ok.clicked.connect(self.accept)
        self.field.textChanged.connect(lambda t: self.ok.setEnabled(bool(t)))
        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(cancel)
        buttons.addWidget(self.ok)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(10)
        for widget in (title, text, error, self.field, show):
            layout.addWidget(widget)
        layout.addSpacing(8)
        layout.addLayout(buttons)


def ask_password(parent: QWidget, archive_name: str, wrong: bool = False) -> Optional[str]:
    """Return the typed password, or None if the user cancelled."""
    dialog = PasswordDialog(parent, archive_name, wrong)
    if dialog.exec() == QDialog.DialogCode.Accepted and dialog.field.text():
        return dialog.field.text()
    return None
