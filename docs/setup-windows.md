# Configuração no Windows

## Requisitos

- Windows 10/11
- Python 3.11+
- OBS Studio (para webcam virtual) — instale e ative **Ferramentas → Câmera Virtual OBS**

## Instalação

```powershell
cd argos-win
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

## Executar

```powershell
argos-win
```

ou

```powershell
python -m argos_win.main
```

## Firewall

Permita o executável Python na **rede privada**:

- TCP **8765** (WebSocket signaling)
- UDP nas portas dinâmicas usadas pelo ICE/WebRTC

```powershell
New-NetFirewallRule -DisplayName "Argos Signaling" -Direction Inbound -Protocol TCP -LocalPort 8765 -Action Allow
```

## Uso com o app Android

1. Inicie o Argos no Windows e clique **Iniciar servidor**.
2. Anote o **IP LAN do PC** e a URL `ws://IP:8765/argos/signaling`.
3. No Android, configure o IP do Windows e toque **Iniciar**.
4. O preview deve aparecer; apps externos (Discord, OBS, Chrome) podem usar a câmera virtual.
