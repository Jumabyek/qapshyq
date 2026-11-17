"""Light and dark themes: a color palette + one Qt style sheet (QSS)."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QGuiApplication, QPalette
from PySide6.QtWidgets import QApplication

from app.engine.sevenzip import BASE_DIR

# Check mark drawn inside checked checkboxes (QSS needs forward slashes).
CHECK_ICON = (BASE_DIR / "assets" / "check.svg").as_posix()

PALETTES = {
    "dark": {
        "bg": "#111318", "surface": "#1a1d24", "surface2": "#242833", "alt": "#1d2028",
        "text": "#e9ebf1", "muted": "#8a92a6", "border": "#2b303c", "hover": "#222631",
        "accent": "#6c8cff", "accent_hover": "#859fff", "accent_soft": "#26305a",
        "danger": "#ff6b6b", "success": "#3ecf8e",
    },
    "light": {
        "bg": "#f4f5f9", "surface": "#ffffff", "surface2": "#eceef4", "alt": "#f8f9fc",
        "text": "#161a23", "muted": "#687087", "border": "#dfe2ea", "hover": "#f0f2f8",
        "accent": "#3d63f5", "accent_hover": "#2f53e0", "accent_soft": "#e3e9ff",
        "danger": "#e5484d", "success": "#18a058",
    },
}

_QSS = """
* {{ outline: none; }}
QWidget {{ background: {bg}; color: {text}; font-size: 13px; }}
QLabel, QCheckBox, QRadioButton {{ background: transparent; }}
QLabel#title {{ font-size: 20px; font-weight: 700; }}
QLabel#h2 {{ font-size: 17px; font-weight: 700; }}
QLabel#h3 {{ font-size: 13px; font-weight: 700; }}
QLabel#muted {{ color: {muted}; }}
QLabel#small {{ color: {muted}; font-size: 12px; }}
QLabel#error {{ color: {danger}; font-weight: 600; }}

QFrame#card {{ background: {surface}; border: 1px solid {border}; border-radius: 14px; }}
QFrame#card QWidget {{ background: transparent; }}
QFrame#dropZone {{ background: {surface}; border: 2px dashed {border}; border-radius: 18px; }}
QFrame#dropZone[dragging="true"] {{ border-color: {accent}; background: {accent_soft}; }}
QFrame#dropZone QWidget {{ background: transparent; }}

QPushButton {{
    background: {surface2}; color: {text}; border: 1px solid {border};
    border-radius: 9px; padding: 8px 16px; font-weight: 600;
}}
QPushButton:hover {{ border-color: {accent}; }}
QPushButton:disabled {{ color: {muted}; border-color: {border}; }}
QPushButton#primary {{ background: {accent}; color: #ffffff; border: 1px solid {accent}; }}
QPushButton#primary:hover {{ background: {accent_hover}; border-color: {accent_hover}; }}
QPushButton#primary:disabled {{ background: {surface2}; color: {muted}; border-color: {border}; }}
QPushButton#ghost {{ background: transparent; border: 1px solid transparent; }}
QPushButton#ghost:hover {{ background: {hover}; border-color: {border}; }}
QPushButton#segment {{ border-radius: 8px; padding: 7px 14px; min-width: 64px; }}
QPushButton#segment:checked {{ background: {accent}; color: #ffffff; border-color: {accent}; }}

QLineEdit, QComboBox {{
    background: {surface}; border: 1px solid {border}; border-radius: 8px;
    padding: 7px 10px; selection-background-color: {accent}; selection-color: #ffffff;
}}
QLineEdit:focus {{ border-color: {accent}; }}
QLineEdit:disabled {{ color: {muted}; background: {surface2}; }}

QTreeWidget, QListWidget {{
    background: {surface}; alternate-background-color: {alt};
    border: 1px solid {border}; border-radius: 12px; padding: 4px;
}}
QTreeWidget::item, QListWidget::item {{ padding: 4px 2px; border: none; }}
QTreeWidget::item:hover, QListWidget::item:hover {{ background: {hover}; }}
QTreeWidget::item:selected, QListWidget::item:selected {{ background: {accent_soft}; color: {text}; }}
QHeaderView {{ background: {surface}; border: none; }}
QHeaderView::section {{
    background: {surface}; color: {muted}; border: none; border-bottom: 1px solid {border};
    padding: 6px 8px; font-weight: 600;
}}

QProgressBar {{
    background: {surface2}; border: none; border-radius: 5px;
    min-height: 10px; max-height: 10px; color: transparent;
}}
QProgressBar::chunk {{ background: {accent}; border-radius: 5px; }}

QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {border}; border-radius: 4px; min-height: 30px; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: {border}; border-radius: 4px; min-width: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

QCheckBox::indicator {{
    width: 16px; height: 16px; border: 1px solid {muted}; border-radius: 5px; background: {surface};
}}
QCheckBox::indicator:hover {{ border-color: {accent}; }}
QCheckBox::indicator:checked {{ background: {accent}; border-color: {accent}; image: url("{check}"); }}
QCheckBox::indicator:disabled {{ border-color: {border}; background: {surface2}; }}
QCheckBox:disabled {{ color: {muted}; }}

QToolTip {{ background: {surface2}; color: {text}; border: 1px solid {border}; padding: 4px 8px; }}
QMenu {{ background: {surface}; border: 1px solid {border}; padding: 4px; }}
QMenu::item {{ padding: 6px 18px; border-radius: 6px; }}
QMenu::item:selected {{ background: {accent_soft}; }}
"""


def system_theme() -> str:
    """'dark' or 'light', following the operating system setting."""
    hints = QGuiApplication.styleHints()
    scheme = getattr(hints, "colorScheme", lambda: Qt.ColorScheme.Unknown)()
    return "dark" if scheme == Qt.ColorScheme.Dark else "light"


def color(theme: str, name: str) -> str:
    return PALETTES[theme][name]


def apply_theme(app: QApplication, theme: str) -> None:
    """Apply palette (used by built-in arrows/checkboxes) and style sheet."""
    p = PALETTES[theme]
    palette = QPalette()
    roles = {
        QPalette.ColorRole.Window: p["bg"], QPalette.ColorRole.WindowText: p["text"],
        QPalette.ColorRole.Base: p["surface"], QPalette.ColorRole.AlternateBase: p["alt"],
        QPalette.ColorRole.Text: p["text"], QPalette.ColorRole.Button: p["surface2"],
        QPalette.ColorRole.ButtonText: p["text"], QPalette.ColorRole.Highlight: p["accent"],
        QPalette.ColorRole.HighlightedText: "#ffffff", QPalette.ColorRole.ToolTipBase: p["surface2"],
        QPalette.ColorRole.ToolTipText: p["text"], QPalette.ColorRole.PlaceholderText: p["muted"],
        QPalette.ColorRole.Link: p["accent"],
    }
    for role, value in roles.items():
        palette.setColor(role, QColor(value))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(p["muted"]))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(p["muted"]))
    app.setPalette(palette)
    app.setStyleSheet(_QSS.format(check=CHECK_ICON, **p))
