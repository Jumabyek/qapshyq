"""Qapshyq - a modern, free, offline archive manager.

Run:  python main.py              (opens the start screen)
      python main.py photos.zip   (opens an archive directly)
"""
import sys
from pathlib import Path

from PySide6.QtCore import QEvent
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow


class QapshyqApp(QApplication):
    """Also handles macOS "Open with Qapshyq" from Finder (FileOpen events)."""

    window = None
    pending: list = []   # files opened before the window existed

    def event(self, event) -> bool:
        if event.type() == QEvent.Type.FileOpen:
            path = Path(event.file())
            if self.window is not None:
                self.window.handle_paths([path])
            else:
                self.pending.append(path)
            return True
        return super().event(event)


def main() -> int:
    app = QapshyqApp(sys.argv)
    app.setApplicationName("Qapshyq")
    app.setOrganizationName("Qapshyq")
    app.setStyle("Fusion")  # same modern look on every system; colors come from theme.py
    if sys.platform.startswith("win"):
        app.setFont(QFont("Segoe UI", 10))

    paths = [Path(arg).resolve() for arg in sys.argv[1:] if Path(arg).exists()]
    window = MainWindow(paths + app.pending)
    app.window = window
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
