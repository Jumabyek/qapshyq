#!/bin/bash
# Double-click in Finder to start Qapshyq on macOS (runs setup the first time).
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ] || [ ! -x bin/7zz ]; then
    bash scripts/setup_mac.sh || { read -r -p "Setup failed. Press Enter to close."; exit 1; }
fi
exec .venv/bin/python main.py "$@"
