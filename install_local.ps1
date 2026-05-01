# One-shot local install for CommonSense (Sense HAT editor).
# Usage (from repo):  powershell -ExecutionPolicy Bypass -File .\CommonSense\install_local.ps1
# Or copy CommonSense folder to D:\CommonSense and run this script from inside that folder.

$ErrorActionPreference = "Stop"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = $ScriptRoot
if (-not (Test-Path (Join-Path $RepoRoot "setup.py"))) {
    Write-Host "setup.py not found next to install_local.ps1. RepoRoot=$RepoRoot" -ForegroundColor Red
    exit 1
}

$VenvDir = Join-Path $RepoRoot "venv"
if (-not (Test-Path $VenvDir)) {
    Write-Host "Creating venv at $VenvDir ..."
    py -3 -m venv $VenvDir
}

$Py = Join-Path $VenvDir "Scripts\python.exe"
$Pip = Join-Path $VenvDir "Scripts\pip.exe"
if (-not (Test-Path $Py)) {
    Write-Host "Python venv missing Scripts\python.exe" -ForegroundColor Red
    exit 1
}

Write-Host "Upgrading pip and installing package (editable) ..."
& $Py -m pip install --upgrade pip
& $Pip install -e $RepoRoot

Write-Host ""
Write-Host "Done. Activate:  .\venv\Scripts\Activate.ps1"
Write-Host "Run editor:     common-sense"
Write-Host "Or:             python -m commonsense.sense_paint.editor"
Write-Host "Tests:          pip install pytest && pytest -q $RepoRoot\tests"
