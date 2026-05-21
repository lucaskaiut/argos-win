# Desenvolvimento no WSL

## Erro `Could not load the Qt platform plugin "xcb"` em `cv2/qt/plugins`

O pacote `opencv-python` traz plugins Qt que conflitam com o PyQt5. O projeto usa **`opencv-python-headless`** e corrige o path em `argos_win.infrastructure.qt_platform`.

### Corrigir ambiente existente

```bash
cd /var/www/html/argos-win
source .venv/bin/activate
pip uninstall -y opencv-python opencv-python-headless 2>/dev/null || true
pip install opencv-python-headless
pip install -e .
```

### Dependências de sistema (plugin xcb)

```bash
sudo apt update
sudo apt install -y \
  libxcb-xinerama0 libxcb-cursor0 libxcb-icccm4 libxcb-image0 \
  libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0 \
  libxcb-xfixes0 libxkbcommon-x11-0 libgl1 libglib2.0-0
```

### Executar

```bash
chmod +x scripts/run_wsl.sh
./scripts/run_wsl.sh
```

Ou manualmente:

```bash
source .venv/bin/activate
unset QT_QPA_PLATFORM_PLUGIN_PATH QT_PLUGIN_PATH
export QT_QPA_PLATFORM_PLUGIN_PATH="$(python -c "import PyQt5, os; from pathlib import Path; print(Path(PyQt5.__file__).parent / 'Qt5' / 'plugins' / 'platforms')")"
export DISPLAY=:0
python -m argos_win.main
```

## Android → servidor no WSL

Use [networkingMode=mirrored](https://learn.microsoft.com/en-us/windows/wsl/networking) no `.wslconfig` ou `portproxy` da porta **8765** do Windows para o IP do WSL.

## `could not connect to display :0`

As libs `libxcb-*` já estão OK; o erro indica que **não há servidor gráfico** nesta sessão do terminal (WSLg inativo).

### Verificar WSLg

```bash
ls /mnt/wslg/runtime-dir    # deve existir ao abrir WSL pelo Windows Terminal
echo $WAYLAND_DISPLAY       # costuma ser wayland-0
```

Se `/mnt/wslg/runtime-dir` **não existir**:

1. Abra o Ubuntu pelo **Menu Iniciar** ou **Windows Terminal** (evite terminal SSH/Cursor sem GUI).
2. No PowerShell: `wsl --shutdown`, abra o WSL de novo.
3. Confirme em `C:\Users\SEU_USUARIO\.wslconfig`:

```ini
[wsl2]
guiApplications=true
```

4. Atualize: `wsl --update`

### Rodar sem GUI (signaling + Android)

```bash
python -m argos_win.main --headless
# ou
./scripts/run_wsl.sh --headless
```

Mostra a URL `ws://IP:8765/argos/signaling` no terminal — útil para testar com o celular sem janela.

### Alternativa: VcXsrv no Windows

1. Instale [VcXsrv](https://sourceforge.net/projects/vcxsrv/)
2. XLaunch → Multiple windows → **Disable access control**
3. No WSL:

```bash
export DISPLAY=$(grep -m1 nameserver /etc/resolv.conf | awk '{print $2}'):0
python -m argos_win.main
```

## Webcam virtual

No WSL/Linux a webcam virtual OBS não existe; use o client para testar **signaling + preview**. Produção: rode no Windows nativo.
