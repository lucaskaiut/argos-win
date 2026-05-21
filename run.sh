#!/usr/bin/env bash
# Argos — WSL/Linux. No Windows nativo use:  run.bat  ou  .\run.ps1
# Argos — um comando para instalar deps e iniciar o client.
# Uso:
#   ./run.sh              # GUI (se WSLg/display OK) ou pergunta headless
#   ./run.sh --headless   # só servidor (sem janela)
#   ./run.sh --gui        # força tentativa de GUI
#
# Do Windows (PowerShell), uma linha:
#   wsl -e bash -lc "cd /var/www/html/argos-win && ./run.sh"
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

MODE="auto"   # auto | gui | headless
EXTRA_ARGS=()
for arg in "$@"; do
  case "$arg" in
    --headless) MODE="headless" ;;
    --gui)      MODE="gui" ;;
    *)          EXTRA_ARGS+=("$arg") ;;
  esac
done

log() { echo "[argos] $*"; }
die() { echo "[argos] ERRO: $*" >&2; exit 1; }

# --- Python / venv ---
if command -v python3 &>/dev/null; then
  PY=python3
elif command -v python &>/dev/null; then
  PY=python
else
  die "Python não encontrado. Instale Python 3.11+ ou use WSL: wsl --install"
fi

if ! $PY -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
  die "Requer Python 3.11+. Versão atual: $($PY --version 2>&1)"
fi

if [[ ! -d .venv ]]; then
  log "Criando ambiente virtual…"
  $PY -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
PY=python

log "Instalando/atualizando dependências…"
pip install -q --upgrade pip
pip install -q -e ".[dev]"

# --- Plugins Qt (PyQt5, não OpenCV) ---
export QT_QPA_PLATFORM_PLUGIN_PATH
QT_QPA_PLATFORM_PLUGIN_PATH="$($PY -c "
from pathlib import Path
import PyQt5
print(Path(PyQt5.__file__).resolve().parent / 'Qt5' / 'plugins' / 'platforms')
")"
unset QT_PLUGIN_PATH 2>/dev/null || true

# --- Detectar WSL ---
IN_WSL=false
if grep -qi microsoft /proc/version 2>/dev/null; then
  IN_WSL=true
fi

# --- Display (WSLg / X11) ---
has_display() {
  if [[ -d /mnt/wslg/runtime-dir ]]; then
    export XDG_RUNTIME_DIR=/mnt/wslg/runtime-dir
    export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}"
    export DISPLAY="${DISPLAY:-:0}"
    if [[ -S "${XDG_RUNTIME_DIR}/${WAYLAND_DISPLAY}" ]]; then
      export QT_QPA_PLATFORM=wayland
    fi
    return 0
  fi
  if [[ -S /tmp/.X11-unix/X0 ]] || [[ -S /mnt/wslg/.X11-unix/X0 ]]; then
    export DISPLAY="${DISPLAY:-:0}"
    return 0
  fi
  # VcXsrv / X410: DISPLAY já apontando para IP do Windows
  if [[ -n "${DISPLAY:-}" ]] && [[ "$DISPLAY" != ":0" ]]; then
    return 0
  fi
  return 1
}

# --- Libs xcb (só Linux/WSL) ---
ensure_xcb_libs() {
  if ! command -v ldconfig &>/dev/null; then
    return 0
  fi
  local qcb="$QT_QPA_PLATFORM_PLUGIN_PATH/libqxcb.so"
  if [[ ! -f "$qcb" ]]; then
    return 0
  fi
  if ldd "$qcb" 2>/dev/null | grep -q "not found"; then
    log "Bibliotecas xcb faltando. Tentando instalar via apt…"
    if command -v sudo &>/dev/null; then
      sudo apt-get update -qq
      sudo apt-get install -y -qq \
        libxcb-icccm4 libxcb-keysyms1 libxcb-shape0 libxcb-xinerama0 \
        libxcb-cursor0 libxkbcommon-x11-0 libgl1 libglib2.0-0 \
        2>/dev/null || true
    else
      log "Instale manualmente: sudo apt install libxcb-icccm4 libxcb-keysyms1 libxcb-shape0 libxcb-xinerama0"
    fi
  fi
}

if $IN_WSL; then
  ensure_xcb_libs
fi

# --- Escolher modo de execução ---
run_headless() {
  log "Modo headless — servidor WebSocket/WebRTC (sem janela)"
  exec $PY -m argos_win.main --headless "${EXTRA_ARGS[@]}"
}

run_gui() {
  log "Iniciando interface gráfica…"
  exec $PY -m argos_win.main "${EXTRA_ARGS[@]}"
}

case "$MODE" in
  headless)
    run_headless
    ;;
  gui)
    if ! has_display; then
      die "Display não disponível. Use ./run.sh --headless ou abra pelo Windows Terminal."
    fi
    run_gui
    ;;
  auto)
    if has_display; then
      run_gui
    fi
    echo ""
    log "Display gráfico não disponível nesta sessão."
    if $IN_WSL; then
      echo "  • Abra o Ubuntu pelo Menu Iniciar / Windows Terminal (não terminal remoto)"
      echo "  • Ou: wsl --shutdown  (PowerShell) e abra o WSL de novo"
      echo "  • Ou use modo sem janela agora:"
      echo ""
      read -r -p "  Iniciar em modo --headless? [S/n] " ans
      if [[ -z "$ans" || "${ans,,}" == "s" || "${ans,,}" == "sim" || "${ans,,}" == "y" ]]; then
        run_headless
      fi
      die "Cancelado. Rode: ./run.sh --headless"
    else
      log "Iniciando em modo headless automaticamente…"
      run_headless
    fi
    ;;
esac
