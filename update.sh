#!/usr/bin/env bash
# Pull the latest CommonSense from GitHub, preserve venv + saved animations.
set -euo pipefail

REPO="https://github.com/awesomo913/PiSenseDesigner.git"
HOME_DIR="${HOME}"
CS="${HOME_DIR}/CommonSense"
BAK="${HOME_DIR}/CommonSense.bak.$(date +%s)"

echo "Killing running editor (if any)..."
pkill -9 -f sense_paint 2>/dev/null || true
sleep 1

if [ -d "${CS}" ]; then
    echo "Backing up old install to ${BAK}"
    mv "${CS}" "${BAK}"
fi

echo "Cloning fresh from GitHub..."
git clone --depth 1 "${REPO}" "${CS}"

# Restore venv + user animations from backup if present
if [ -d "${BAK}/venv" ]; then
    echo "Restoring venv (saves apt + pip install time)"
    mv "${BAK}/venv" "${CS}/venv"
fi
if [ -d "${BAK}/MyAnimations" ]; then
    echo "Restoring MyAnimations"
    mv "${BAK}/MyAnimations" "${CS}/MyAnimations"
fi

cd "${CS}"

# pip install editable in case package metadata changed
if [ -d venv ]; then
    venv/bin/pip install -e . --quiet 2>/dev/null || true
fi

# Make sure run.sh + scripts executable
chmod +x run.sh setup_desktop.sh install_local.sh 2>/dev/null || true

# Refresh desktop launcher
if [ -f setup_desktop.sh ]; then
    bash setup_desktop.sh 2>/dev/null || true
fi

# Count what we have
echo ""
echo "================ Update complete ================"
echo "  battles : $(ls examples/battles 2>/dev/null | wc -l) animations"
echo "  sonic   : $(ls examples/sonic 2>/dev/null | wc -l) animations"
echo "  mario   : $(ls examples/mario 2>/dev/null | wc -l) animations"
echo "  fortnite: $(ls examples/fortnite 2>/dev/null | wc -l) animations"
echo "================================================="
echo ""
echo "Old install kept at ${BAK} (delete with: rm -rf ${BAK})"
echo ""
echo "Launching editor..."
./run.sh
