# Argos Windows — um comando para instalar e iniciar (nativo Windows, sem WSL).
# Uso:
#   .\run.ps1
#   .\run.ps1 -Headless
#
# Duplo clique ou CMD: run.bat
#
param(
    [switch]$Headless
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function Write-Argos([string]$Message) {
    Write-Host "[argos] $Message"
}

function Find-PythonLauncher {
    $candidates = @(
        @{ Exe = "py"; Args = @("-3.12") },
        @{ Exe = "py"; Args = @("-3.11") },
        @{ Exe = "py"; Args = @("-3") },
        @{ Exe = "python"; Args = @() }
    )
    foreach ($c in $candidates) {
        try {
            $ver = & $c.Exe @($c.Args + "-c", "import sys; print(sys.version_info[0], sys.version_info[1])") 2>$null
            if ($LASTEXITCODE -ne 0) { continue }
            $parts = ($ver -split "\s+") | Where-Object { $_ }
            $major = [int]$parts[0]
            $minor = [int]$parts[1]
            if ($major -ge 3 -and $minor -ge 11) {
                return $c
            }
        } catch { }
    }
    return $null
}

$launcher = Find-PythonLauncher
if (-not $launcher) {
    Write-Host "[argos] ERRO: Python 3.11+ nao encontrado." -ForegroundColor Red
    Write-Host "  Instale: https://www.python.org/downloads/ (marque 'Add python.exe to PATH')"
    exit 1
}

$launchLabel = "$($launcher.Exe) $($launcher.Args -join ' ')"
Write-Argos "Python: $launchLabel"

$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Argos "Criando ambiente virtual..."
    & $launcher.Exe @($launcher.Args + "-m", "venv", ".venv")
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

$VenvPip = Join-Path $Root ".venv\Scripts\pip.exe"
Write-Argos "Instalando/atualizando dependencias..."
& $VenvPip install -q --upgrade pip
& $VenvPip install -q -e .
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if ($Headless) {
    Write-Argos "Modo headless (servidor sem janela)..."
    & $VenvPython -m argos_win.main --headless
} else {
    Write-Argos "Iniciando Argos..."
    & $VenvPython -m argos_win.main
}

exit $LASTEXITCODE
