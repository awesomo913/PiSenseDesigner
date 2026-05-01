#!/usr/bin/env bash
# CommonSense — Linux / Raspberry Pi installer
# Usage: bash install_local.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== CommonSense installer (Linux / Pi) ==="

# ── system packages ──────────────────────────────────────────────────────────
echo "[1/4] Installing system packages (requires sudo)..."
sudo apt-get update -qq
sudo apt-get install -y python3-pip python3-tk python3-venv python3-dev

# Install sense-hat system package if on Pi hardware
if python3 -c "import sense_hat" 2>/dev/null; then
    echo "      sense_hat already importable — skipping apt sense-hat."
elif dpkg -l sense-hat &>/dev/null; then
    echo "      sense-hat apt package already installed."
else
    echo "      Attempting 'sudo apt-get install -y sense-hat' (Pi only, ok to fail)..."
    sudo apt-get install -y sense-hat 2>/dev/null || echo "      (sense-hat apt package not available — hardware preview disabled)"
fi

# ── virtual environment ───────────────────────────────────────────────────────
echo "[2/4] Creating venv (inherits system site-packages for sense_hat / RPi.GPIO)..."
python3 -m venv --system-site-packages venv

# ── pip install ───────────────────────────────────────────────────────────────
echo "[3/4] Installing CommonSense in editable mode..."
venv/bin/pip install --upgrade pip -q
venv/bin/pip install -e ".[dev]" -q

# ── launcher script ───────────────────────────────────────────────────────────
echo "[4/5] Writing run.sh convenience launcher..."
cat > run.sh <<'RUN'
#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
source venv/bin/activate
exec common-sense "$@"
RUN
chmod +x run.sh

echo "[5/5] Installing desktop launcher..."
chmod +x setup_desktop.sh 2>/dev/null || true
bash setup_desktop.sh || echo "      (desktop setup failed — you can rerun: bash setup_desktop.sh)"

echo ""
echo "=== Done! ==="
echo ""
echo "Launch options:"
echo "  ./run.sh                         # convenience launcher"
echo "  source venv/bin/activate && common-sense   # manual"
echo "  venv/bin/python -m commonsense.sense_paint.editor  # no activation needed"
echo ""
echo "On a headless Pi, set DISPLAY first:"
echo "  DISPLAY=:0 ./run.sh"
