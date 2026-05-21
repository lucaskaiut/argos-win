"""Servidor aiohttp — signaling + health."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from aiohttp import web

from argos_win.protocol.constants import HEALTH_PATH, SIGNALING_PATH
from argos_win.signaling.session import SessionCallbacks
from argos_win.signaling.websocket_handler import handle_signaling

if TYPE_CHECKING:
    from argos_win.services.frame_pipeline import FramePipeline

logger = logging.getLogger(__name__)


class SignalingServer:
    def __init__(
        self,
        host: str,
        port: int,
        pipeline: FramePipeline,
        callbacks: SessionCallbacks,
    ) -> None:
        self._host = host
        self._port = port
        self._pipeline = pipeline
        self._callbacks = callbacks
        self._runner: web.AppRunner | None = None
        self._site: web.TCPSite | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    @property
    def port(self) -> int:
        return self._port

    def _create_app(self) -> web.Application:
        app = web.Application()
        pipeline = self._pipeline
        callbacks = self._callbacks

        async def health(_request: web.Request) -> web.Response:
            return web.json_response({"status": "ok", "service": "argos-signaling"})

        async def signaling(request: web.Request) -> web.WebSocketResponse:
            return await handle_signaling(request, pipeline, callbacks)

        app.router.add_get(HEALTH_PATH, health)
        app.router.add_get(SIGNALING_PATH, signaling)
        return app

    async def start(self) -> None:
        if self._runner:
            return
        app = self._create_app()
        self._runner = web.AppRunner(app)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, self._host, self._port)
        await self._site.start()
        logger.info("Signaling em ws://<IP_LAN>:%s%s", self._port, SIGNALING_PATH)

    async def stop(self) -> None:
        if self._site:
            await self._site.stop()
            self._site = None
        if self._runner:
            await self._runner.cleanup()
            self._runner = None
        logger.info("Servidor signaling parado")
