"""Handler WebSocket /argos/signaling."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from aiohttp import web

from argos_win.signaling.session import ArgosSession, SessionCallbacks

if TYPE_CHECKING:
    from argos_win.services.frame_pipeline import FramePipeline

logger = logging.getLogger(__name__)


async def handle_signaling(
    request: web.Request,
    pipeline: FramePipeline,
    callbacks: SessionCallbacks,
) -> web.WebSocketResponse:
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    session: ArgosSession | None = None
    logger.info("Cliente conectado: %s", request.remote)

    try:
        async for message in ws:
            if message.type != web.WSMsgType.TEXT:
                if message.type in (web.WSMsgType.CLOSE, web.WSMsgType.ERROR):
                    break
                continue

            try:
                data = json.loads(message.data)
            except json.JSONDecodeError:
                logger.warning("Mensagem JSON inválida")
                continue

            msg_type = data.get("type")
            session_id = data.get("sessionId") or "unknown"

            if session is None:
                session = ArgosSession(ws, session_id, pipeline, callbacks)
            elif data.get("sessionId") and data["sessionId"] != session.session_id:
                logger.debug("Ignorando mensagem de sessionId antigo: %s", data["sessionId"])
                continue

            session.session_id = session_id

            if msg_type == "register" and data.get("role") == "mobile":
                await session.handle_register(data)

            elif msg_type == "offer":
                await session.handle_offer(data)

            elif msg_type == "ice-candidate":
                await session.handle_ice_candidate(data)

            elif msg_type == "ping":
                await session.handle_ping(data)

            elif msg_type == "bye":
                await session.handle_bye(data)
                break

    except Exception:
        logger.exception("Erro na sessão signaling")
    finally:
        if session:
            await session.close()
        callbacks.on_client_disconnected()
        logger.info("Cliente desconectado")

    return ws
