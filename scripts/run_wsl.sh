#!/usr/bin/env bash
# Executa o Argos no WSL. Detecta WSLg ou sugere --headless / VcXsrv.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
HEADLESS=false
for arg in "$@"; do
  [[ "$arg" == "--headless" ]] && HEADLESS=true
done

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -e .

export QT_QPA_PLATFORM_PLUGIN_PATH
QT_QPA_PLATFORM_PLUGIN_PATH="$(python -c "
from pathlib import Path
import PyQt5
print(Path(PyQt5.__file__).resolve().parent / 'Qt5' / 'plugins' / 'platforms')
")"
unset QT_PLUGIN_PATH 2>/dev/null || true

setup_wslg_display() {
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
  return 1
}

if [[ "$HEADLESS" == true ]]; then
  exec python -m argos_win.main --headless "$@"
fi

if ! setup_wslg_display; then
  echo "=============================================="
  echo " WSLg / display não detectado nesta sessão"
  echo "=============================================="
  echo ""
  echo "Opções:"
  echo "  1) Abrir o Ubuntu pelo Menu Iniciar / Windows Terminal"
  echo "     (não use terminal remoto sem GUI), depois:"
  echo "       ./scripts/run_wsl.sh"
  echo ""
  echo "  2) Reiniciar WSL no PowerShell:"
  echo "       wsl --shutdown"
  echo "     e abrir o terminal de novo."
  echo ""
  echo "  3) Rodar sem janela (só servidor, para testar com Android):"
  echo "       ./scripts/run_wsl.sh --headless"
  echo ""
  echo "  4) Rodar no Windows nativo (recomendado para GUI + webcam):"
  echo "       powershell: cd argos-win; pip install -e .; argos-win"
  echo ""
  read -r -p "Tentar mesmo assim com DISPLAY=:0? [s/N] " ans
  if [[ "${ans,,}" != "s" ]]; then
    echo "Abortado. Use: ./scripts/run_wsl.sh --headless"
    exit 1
  fi
  export DISPLAY=:0
fi

exec python -m argos_win.main "$@"
