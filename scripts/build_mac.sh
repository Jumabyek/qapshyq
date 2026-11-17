#!/bin/bash
# ---------------------------------------------------------------------------
#  Build Qapshyq for macOS:  dist/Qapshyq.app  and  dist/Qapshyq-<version>-mac.dmg
#  Usage:  bash scripts/build_mac.sh
# ---------------------------------------------------------------------------
set -euo pipefail
cd "$(dirname "$0")/.."

bash scripts/setup_mac.sh
.venv/bin/python -m pip install -r requirements-dev.txt --quiet

echo "Running tests..."
.venv/bin/python -m unittest discover -s tests

echo "Building the app with PyInstaller..."
.venv/bin/pyinstaller --noconfirm --clean qapshyq.spec

VERSION="$(.venv/bin/python -c 'from app import __version__; print(__version__)')"
DMG="dist/Qapshyq-${VERSION}-mac.dmg"
echo "Packing $DMG ..."
rm -rf dist/dmg "$DMG"
mkdir -p dist/dmg
cp -R dist/Qapshyq.app dist/dmg/
ln -s /Applications dist/dmg/Applications       # drag-to-install shortcut
hdiutil create -volname "Qapshyq" -srcfolder dist/dmg -ov -format UDZO "$DMG"
rm -rf dist/dmg
echo "Done! $DMG"
