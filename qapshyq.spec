# -*- mode: python ; coding: utf-8 -*-
# PyInstaller recipe: turns the Python project into a real app.
#   Windows -> dist/Qapshyq/Qapshyq.exe     macOS -> dist/Qapshyq.app
# Build with:  pyinstaller --noconfirm --clean qapshyq.spec
import sys
from pathlib import Path

ROOT = Path(SPECPATH)
IS_WINDOWS = sys.platform.startswith("win")
IS_MAC = sys.platform == "darwin"
sys.path.insert(0, str(ROOT))
from app import __version__  # noqa: E402

# The 7-Zip engine must be in bin/ (the setup scripts put it there).
engine = ["bin/7z.exe", "bin/7z.dll"] if IS_WINDOWS else ["bin/7zz"]
for file in engine:
    if not (ROOT / file).is_file():
        raise SystemExit(f"Missing {file}. Run the setup script first.")

a = Analysis(
    ["main.py"],
    pathex=[str(ROOT)],
    binaries=[(file, "bin") for file in engine],
    datas=[
        ("assets/icon.png", "assets"),
        ("assets/check.svg", "assets"),
        ("bin/7-Zip-License.txt", "bin"),
        ("LICENSE", "."),
        ("THIRD_PARTY_NOTICES.md", "."),
    ],
    # Qt modules we never use: leaving them out makes the app much smaller.
    excludes=[
        "tkinter", "PySide6.QtNetwork", "PySide6.QtQml", "PySide6.QtQuick",
        "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtMultimedia",
        "PySide6.QtPdf", "PySide6.Qt3DCore", "PySide6.QtCharts", "PySide6.QtDataVisualization",
    ],
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Qapshyq",
    console=False,               # no black console window
    upx=False,
    icon=str(ROOT / ("assets/icon.ico" if IS_WINDOWS else "assets/icon.icns")),
)

coll = COLLECT(exe, a.binaries, a.datas, name="Qapshyq", upx=False)

if IS_MAC:
    archive_types = ["zip", "rar", "7z", "tar", "gz", "tgz", "bz2", "xz"]
    app = BUNDLE(
        coll,
        name="Qapshyq.app",
        icon=str(ROOT / "assets/icon.icns"),
        bundle_identifier="app.qapshyq",
        version=__version__,
        info_plist={
            "CFBundleShortVersionString": __version__,
            "NSHighResolutionCapable": True,
            "NSRequiresAquaSystemAppearance": False,   # allow dark mode
            # Lets Finder offer "Open With > Qapshyq" for archives.
            "CFBundleDocumentTypes": [{
                "CFBundleTypeName": "Archive",
                "CFBundleTypeRole": "Viewer",
                "LSHandlerRank": "Alternate",
                "CFBundleTypeExtensions": archive_types,
            }],
        },
    )
