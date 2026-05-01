#!/usr/bin/env bash
# Install CommonSense desktop launcher on Linux/Pi.
# Adds entry to applications menu AND a clickable icon on the Desktop.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOME_DIR="${HOME}"
APP_DIR="${HOME_DIR}/.local/share/applications"
DESKTOP_DIR="${HOME_DIR}/Desktop"

mkdir -p "${APP_DIR}"
[ -d "${DESKTOP_DIR}" ] || DESKTOP_DIR="${HOME_DIR}"

SRC="${SCRIPT_DIR}/commonsense.desktop"
DST_APP="${APP_DIR}/commonsense.desktop"
DST_DESK="${DESKTOP_DIR}/CommonSense.desktop"

# Substitute __HOME__ token
sed "s|__HOME__|${HOME_DIR}|g" "${SRC}" > "${DST_APP}"
chmod +x "${DST_APP}"
cp "${DST_APP}" "${DST_DESK}"
chmod +x "${DST_DESK}"

# Mark desktop file as trusted (Pi OS / GNOME variant)
if command -v gio >/dev/null 2>&1; then
    gio set "${DST_DESK}" metadata::trusted true 2>/dev/null || true
fi
# Old PCManFM/LXDE trick — touch executable bit
chmod 755 "${DST_DESK}"

# Refresh the apps menu cache if available
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${APP_DIR}" 2>/dev/null || true
fi

echo "Installed launcher:"
echo "  ${DST_APP}"
echo "  ${DST_DESK}"
echo ""
echo "If the desktop icon shows a '?' or asks 'Trust?', right-click it and choose"
echo "'Allow Launching' (or open Files manager Preferences → enable executable .desktop)."
