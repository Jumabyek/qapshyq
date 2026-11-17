#!/bin/bash
# ---------------------------------------------------------------------------
#  Qapshyq setup for macOS: Python packages + the 7-Zip engine (7zz).
#  Safe to run many times. Usage:  bash scripts/setup_mac.sh
# ---------------------------------------------------------------------------
set -euo pipefail
cd "$(dirname "$0")/.."
SEVENZIP_VERSION=2606                 # 26.06
SEVENZIP_TAG="${SEVENZIP_VERSION:0:2}.${SEVENZIP_VERSION:2:2}"

# --- 1. Python -------------------------------------------------------------
PY=""
for candidate in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$candidate" >/dev/null 2>&1 && \
       "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' 2>/dev/null; then
        PY="$candidate"; break
    fi
done
if [ -z "$PY" ]; then
    echo "[!] Python 3.9+ was not found."
    echo "    Install Python 3.12 from https://www.python.org/downloads/macos/ and run this again."
    exit 1
fi
echo "Using $($PY --version)"

# --- 2. Virtual environment with the packages ------------------------------
if [ ! -x .venv/bin/python ]; then
    echo "Creating virtual environment..."
    "$PY" -m venv .venv
fi
.venv/bin/python -m pip install --upgrade pip --quiet
.venv/bin/python -m pip install -r requirements.txt --quiet

# --- 3. 7-Zip engine into bin/ ---------------------------------------------
if [ -x bin/7zz ] && bin/7zz >/dev/null 2>&1; then
    echo "7-Zip engine already in bin/"
else
    echo "Downloading 7-Zip $SEVENZIP_TAG for macOS from the official site..."
    tmp="$(mktemp -d)"
    curl -fL "https://www.7-zip.org/a/7z${SEVENZIP_VERSION}-mac.tar.xz" -o "$tmp/7z.tar.xz" \
      || curl -fL "https://github.com/ip7z/7zip/releases/download/${SEVENZIP_TAG}/7z${SEVENZIP_VERSION}-mac.tar.xz" -o "$tmp/7z.tar.xz"
    tar -xf "$tmp/7z.tar.xz" -C "$tmp"
    cp "$tmp/7zz" bin/7zz
    chmod +x bin/7zz
    xattr -d com.apple.quarantine bin/7zz 2>/dev/null || true
    rm -rf "$tmp"
fi

echo
echo "Setup complete. Start the app with:  ./run_mac.command   (or double-click it in Finder)"
