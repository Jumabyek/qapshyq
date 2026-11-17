#!/bin/bash
# Double-click in Finder to build the macOS installer:
#   dist/Qapshyq.app  and  dist/Qapshyq-<version>-mac.dmg
cd "$(dirname "$0")"
if bash scripts/build_mac.sh; then
    echo
    echo "Success! Opening the dist folder..."
    open dist
else
    echo
    echo "Build failed - send a screenshot of this window."
fi
read -r -p "Press Enter to close."
