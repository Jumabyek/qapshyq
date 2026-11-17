"""Small helpers used across the app."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices


def human_size(num_bytes: int) -> str:
    """1536 -> '1.5 KB'."""
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.0f} {unit}" if unit == "B" or size >= 100 else f"{size:.1f} {unit}"
        size /= 1024
    return f"{num_bytes} B"


def open_path(path: Path) -> None:
    """Open a file or folder with the system's default app."""
    QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))


def unique_path(path: Path) -> Path:
    """'Archive.zip' -> 'Archive (2).zip' if the name is already taken."""
    if not path.exists():
        return path
    number = 2
    while True:
        candidate = path.with_name(f"{path.stem} ({number}){path.suffix}")
        if not candidate.exists():
            return candidate
        number += 1
