# Argos Windows Client

Cliente Windows que recebe vídeo em tempo real do **app Android Argos** via Wi-Fi e expõe uma **webcam virtual** para Discord, Chrome, Zoom, OBS e outros apps.

## Funcionalidades

- Servidor WebSocket em `ws://<IP_PC>:8765/argos/signaling`
- WebRTC (H.264) — Android envia, Windows recebe
- Preview em tempo real (PyQt5 + OpenCV)
- Webcam virtual (`pyvirtualcam` + OBS Virtual Camera)
- Heartbeat `ping`/`pong`, tratamento de `bye` e erros do protocolo

## Um comando (Windows nativo)

**PowerShell** (na pasta do projeto):

```powershell
cd C:\caminho\para\argos-win
.\run.ps1
```

Ou **duplo clique** em `run.bat`.

Sem janela (só servidor, para testar com o Android):

```powershell
.\run.ps1 -Headless
```

O script cria o `.venv`, instala dependências e abre o app.

## WSL (opcional)

```bash
./run.sh
```

Ver [docs/wsl-dev.md](docs/wsl-dev.md).

Consulte [docs/setup-windows.md](docs/setup-windows.md) para firewall e drivers.

## Protocolo

O Android conecta ao IP do Windows. Detalhes em [docs/integration.md](docs/integration.md).

## Exemplo standalone (debug)

```bash
python examples/python_signaling_server.py --port 8765
```

## Estrutura

```
src/argos_win/
  app/           # orquestrador e estados
  signaling/     # servidor WebSocket aiohttp
  webrtc/        # aiortc peer + consumo de vídeo
  services/      # pipeline de frames, webcam virtual, rede
  gui/           # interface PyQt5
  protocol/      # mensagens JSON do contrato
```

## Testes

```bash
pip install -e ".[dev]"
pytest
```
