#!/usr/bin/env python3
"""
Servidor de signaling standalone (referência / debug).

Requisitos:
    pip install aiortc aiohttp

Uso:
    python examples/python_signaling_server.py --host 0.0.0.0 --port 8765

O app Android conecta em ws://<IP_WINDOWS>:8765/argos/signaling
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from typing import Any

from aiohttp import web
from aiortc import (
    RTCIceCandidate,
    RTCPeerConnection,
    RTCSessionDescription,
    RTCConfiguration,
)
from aiortc.contrib.media import MediaBlackhole

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("argos-windows")

SIGNALING_PATH = "/argos/signaling"


class ArgosSession:
    def __init__(self, ws: web.WebSocketResponse, session_id: str) -> None:
        self.ws = ws
        self.session_id = session_id
        self.pc: RTCPeerConnection | None = None
        self.sink = MediaBlackhole()

    async def close(self) -> None:
        if self.pc:
            await self.pc.close()
            self.pc = None
        await self.sink.stop()


async def send_json(ws: web.WebSocketResponse, payload: dict[str, Any]) -> None:
    await ws.send_str(json.dumps(payload))


async def handle_signaling(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    session: ArgosSession | None = None
    logger.info("Cliente conectado: %s", request.remote)

    try:
        async for message in ws:
            if message.type != web.WSMsgType.TEXT:
                continue

            data = json.loads(message.data)
            msg_type = data.get("type")
            session_id = data.get("sessionId") or "unknown"

            if session is None:
                session = ArgosSession(ws, session_id)
            elif data.get("sessionId") and data["sessionId"] != session.session_id:
                session = ArgosSession(ws, data["sessionId"])

            if msg_type == "register" and data.get("role") == "mobile":
                logger.info(
                    "Register mobile deviceId=%s localIp=%s",
                    data.get("deviceId"),
                    data.get("localIp"),
                )
                await send_json(
                    ws,
                    {
                        "type": "registered",
                        "protocolVersion": "1.0",
                        "sessionId": session_id,
                        "serverId": "windows-python",
                    },
                )

            elif msg_type == "offer" and session:
                await _handle_offer(session, data)

            elif msg_type == "ice-candidate" and session and session.pc:
                await _add_ice_candidate(session.pc, data.get("candidate", {}))

            elif msg_type == "ping":
                await send_json(
                    ws,
                    {"type": "pong", "sessionId": session_id, "timestamp": data.get("timestamp")},
                )

            elif msg_type == "bye":
                logger.info("Bye: %s", data.get("reason"))
                break

    except Exception:
        logger.exception("Erro na sessão signaling")
    finally:
        if session:
            await session.close()
        logger.info("Cliente desconectado")

    return ws


async def _handle_offer(session: ArgosSession, data: dict[str, Any]) -> None:
    sdp = data.get("sdp")
    if not sdp:
        await send_json(
            session.ws,
            {
                "type": "error",
                "code": "INVALID_SDP",
                "message": "Campo sdp ausente no offer",
                "sessionId": session.session_id,
            },
        )
        return

    video = data.get("video", {})
    logger.info(
        "Offer recebido codec=%s %sx%s@%sfps",
        video.get("codec"),
        video.get("width"),
        video.get("height"),
        video.get("fps"),
    )

    pc = RTCPeerConnection(configuration=RTCConfiguration(iceServers=[]))
    session.pc = pc

    @pc.on("track")
    async def on_track(track) -> None:
        logger.info("Track recebido: %s", track.kind)
        if track.kind == "video":
            await session.sink.start()
            while True:
                try:
                    frame = await track.recv()
                    await session.sink.write(frame)
                except Exception:
                    break

    @pc.on("icecandidate")
    async def on_ice(candidate) -> None:
        if candidate:
            await send_json(
                session.ws,
                {
                    "type": "ice-candidate",
                    "sessionId": session.session_id,
                    "candidate": {
                        "candidate": candidate.candidate,
                        "sdpMid": candidate.sdpMid,
                        "sdpMLineIndex": candidate.sdpMLineIndex,
                    },
                },
            )

    await pc.setRemoteDescription(RTCSessionDescription(sdp=sdp, type="offer"))
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    await send_json(
        session.ws,
        {
            "type": "answer",
            "protocolVersion": "1.0",
            "sessionId": session.session_id,
            "sdp": pc.localDescription.sdp,
        },
    )
    logger.info("Answer enviado")


async def _add_ice_candidate(pc: RTCPeerConnection, candidate: dict[str, Any]) -> None:
    if not candidate or not candidate.get("candidate"):
        return
    ice = RTCIceCandidate(
        sdpMid=candidate.get("sdpMid"),
        sdpMLineIndex=candidate.get("sdpMLineIndex"),
        candidate=candidate.get("candidate"),
    )
    await pc.addIceCandidate(ice)


async def health(_request: web.Request) -> web.Response:
    return web.json_response({"status": "ok", "service": "argos-signaling"})


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/health", health)
    app.router.add_get(SIGNALING_PATH, handle_signaling)
    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="Argos Windows signaling + WebRTC")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    logger.info(
        "Signaling em ws://%s:%s%s — configure este IP no app Android",
        args.host if args.host != "0.0.0.0" else "<IP_LAN_WINDOWS>",
        args.port,
        SIGNALING_PATH,
    )

    app = create_app()
    web.run_app(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
