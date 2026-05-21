# Desenvolvimento local no Windows
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
& .\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m argos_win.main
