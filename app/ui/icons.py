"""File-type icons drawn in code (no image files needed).

Each file gets a small colored badge with its extension, e.g. a green
"XLSX" or a pink "MP4". This looks the same on Windows and macOS and
keeps the app small.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPainterPath, QPixmap

from app.engine.sevenzip import BASE_DIR

# category -> (badge color, readable name, extensions)
CATEGORIES: dict[str, tuple[str, str, set[str]]] = {
    "image": ("#22b07d", "image", {"png", "jpg", "jpeg", "gif", "bmp", "webp", "heic", "svg", "tif", "tiff", "ico", "raw"}),
    "video": ("#e5487a", "video", {"mp4", "mov", "avi", "mkv", "webm", "wmv", "m4v", "flv"}),
    "audio": ("#f08c2e", "audio", {"mp3", "wav", "flac", "aac", "ogg", "m4a", "wma", "opus"}),
    "pdf": ("#e5484d", "document", {"pdf"}),
    "doc": ("#3d7cf5", "document", {"doc", "docx", "odt", "rtf", "pages"}),
    "sheet": ("#1f9d55", "spreadsheet", {"xls", "xlsx", "csv", "ods", "numbers"}),
    "slides": ("#f06a2e", "presentation", {"ppt", "pptx", "odp", "key"}),
    "text": ("#7a8499", "text file", {"txt", "md", "log", "ini", "cfg", "nfo"}),
    "code": ("#8e5bff", "code file", {"py", "js", "ts", "html", "css", "json", "xml", "c", "cpp", "h",
                                      "java", "go", "rs", "sh", "bat", "php", "rb", "kt", "swift", "yml", "yaml"}),
    "archive": ("#c7922a", "archive", {"zip", "rar", "7z", "tar", "gz", "tgz", "bz2", "xz", "zst", "iso", "cab"}),
    "app": ("#4f5d75", "program", {"exe", "msi", "dmg", "pkg", "app", "apk", "deb", "rpm", "dll"}),
    "font": ("#b0568f", "font", {"ttf", "otf", "woff", "woff2"}),
}
DEFAULT_COLOR = "#7a8499"
FOLDER_COLOR = "#f2b53c"


def _category(ext: str) -> tuple[str, str]:
    for color, label, exts in CATEGORIES.values():
        if ext in exts:
            return color, label
    return DEFAULT_COLOR, "file"


def extension(name: str) -> str:
    return name.rsplit(".", 1)[-1].lower() if "." in name.strip(".") else ""


def type_label(name: str, is_dir: bool = False) -> str:
    """'photo.JPG' -> 'JPG image'."""
    if is_dir:
        return "Folder"
    ext = extension(name)
    if not ext:
        return "File"
    _, label = _category(ext)
    return f"{ext.upper()} {label}"


@lru_cache(maxsize=256)
def file_icon(name: str) -> QIcon:
    """Rounded badge in the category color with the extension written on it."""
    ext = extension(name)
    color, _ = _category(ext)
    size = 64
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Page shape with a folded corner.
    page = QPainterPath()
    page.moveTo(12, 4)
    page.lineTo(40, 4)
    page.lineTo(54, 18)
    page.lineTo(54, 56)
    page.quadTo(54, 60, 50, 60)
    page.lineTo(14, 60)
    page.quadTo(10, 60, 10, 56)
    page.lineTo(10, 8)
    page.quadTo(10, 4, 14, 4)
    p.fillPath(page, QColor(color))
    fold = QPainterPath()
    fold.moveTo(40, 4)
    fold.lineTo(40, 18)
    fold.lineTo(54, 18)
    fold.closeSubpath()
    p.fillPath(fold, QColor(255, 255, 255, 90))

    # Extension text.
    label = (ext[:4] or "").upper()
    if label:
        font = QFont()
        font.setBold(True)
        font.setPixelSize(15 if len(label) <= 3 else 12)
        p.setFont(font)
        p.setPen(QColor("white"))
        p.drawText(QRectF(10, 28, 44, 26), Qt.AlignmentFlag.AlignCenter, label)
    p.end()
    return QIcon(pix)


@lru_cache(maxsize=1)
def folder_icon() -> QIcon:
    size = 64
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    back = QPainterPath()
    back.addRoundedRect(QRectF(6, 12, 52, 42), 6, 6)
    tab = QPainterPath()
    tab.addRoundedRect(QRectF(6, 8, 24, 12), 4, 4)
    p.fillPath(tab, QColor(FOLDER_COLOR).darker(115))
    p.fillPath(back, QColor(FOLDER_COLOR).darker(115))
    front = QPainterPath()
    front.addRoundedRect(QRectF(6, 20, 52, 36), 6, 6)
    p.fillPath(front, QColor(FOLDER_COLOR))
    p.end()
    return QIcon(pix)


def icon_for(name: str, is_dir: bool) -> QIcon:
    return folder_icon() if is_dir else file_icon(name)


@lru_cache(maxsize=1)
def app_icon() -> QIcon:
    """The app logo from assets/ (created by scripts/make_icon.py)."""
    path = Path(BASE_DIR) / "assets" / "icon.png"
    return QIcon(str(path)) if path.is_file() else file_icon("app.zip")
