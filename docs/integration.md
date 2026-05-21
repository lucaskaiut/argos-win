# Integração Android ↔ Windows

Contrato implementado pelo client Windows (`argos-win`).

## Endpoint

```
ws://{WINDOWS_HOST}:8765/argos/signaling
```

- **Windows**: servidor WebSocket (bind `0.0.0.0:8765`)
- **Android**: cliente — envia `register`, `offer`, ICE; recebe `registered`, `answer`

## Fluxo

1. Android → `register` → Windows → `registered`
2. Android → `offer` (SDP + meta H.264) → Windows → `answer`
3. ICE trickle bidirecional (`ice-candidate`)
4. Mídia WebRTC P2P na LAN (`iceServers=[]`)
5. Heartbeat: Android `ping` → Windows `pong` (~5 s)
6. Android `bye` → Windows fecha `RTCPeerConnection`

## Códigos de erro (Windows → Android)

| Código | Quando |
|--------|--------|
| `INVALID_SDP` | Offer sem SDP |
| `SESSION_BUSY` | Outra sessão ativa |
| `UNSUPPORTED_CODEC` | Codec diferente de H.264 |
| `INTERNAL_ERROR` | Falha ICE ou exceção |

## Referência Android

Ver repositório `argos-app`: `src/services/webrtc/`, `src/constants/streaming.ts`.
