"""Sessão WebSocket + WebRTC por conexão Android."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any, Callable

from aiohttp import web

from argos_win.protocol import errors, messages
from argos_win.webrtc.peer_manager import PeerManager

if TYPE_CHECKING:
    from argos_win.services.frame_pipeline import FramePipeline

logger = logging.getLogger(__name__)


class SessionCallbacks:
    """Callbacks para o orchestrator."""

    def __init__(self) -> None:
        self._active: ArgosSession | None = None
        self.on_mobile_registered: Callable[[str, str, int], None] = lambda *_: None
        self.on_negotiating: Callable[[], None] = lambda: None
        self.on_media_connected: Callable[[], None] = lambda: None
        self.on_media_stopped: Callable[[], None] = lambda: None
        self.on_mobile_bye: Callable[[str], None] = lambda _: None
        self.on_signaling_error: Callable[[str, str], None] = lambda *_: None
        self.on_client_disconnected: Callable[[], None] = lambda: None

    def is_session_busy(self, session: ArgosSession) -> bool:
        if self._active is None or self._active is session:
            return False
        return self._active.registered

    def set_active_session(self, session: ArgosSession) -> None:
        self._active = session

    def clear_active_session(self, session: ArgosSession) -> None:
        if self._active is session:
            self._active = None


class ArgosSession:
    def __init__(
        self,
        ws: web.WebSocketResponse,
        session_id: str,
        pipeline: FramePipeline,
        callbacks: SessionCallbacks,
    ) -> None:
        self.ws = ws
        self.session_id = session_id
        self._pipeline = pipeline
        self._callbacks = callbacks
        self.device_id: str | None = None
        self.mobile_local_ip: str | None = None
        self.mobile_local_port: int | None = None
        self.registered = False
        self._peer: PeerManager | None = None
        self._last_heartbeat = time.monotonic()

    @property
    def has_active_peer(self) -> bool:
        return self._peer is not None and self._peer.peer_connection is not None

    async def send_json(self, payload: dict[str, Any]) -> None:
        import json

        await self.ws.send_str(json.dumps(payload))

    def touch_heartbeat(self) -> None:
        self._last_heartbeat = time.monotonic()

    @property
    def seconds_since_heartbeat(self) -> float:
        return time.monotonic() - self._last_heartbeat

    async def handle_register(self, data: dict[str, Any]) -> None:
        if self._callbacks.is_session_busy(self):
            await self.send_json(
                messages.build_error(
                    errors.SESSION_BUSY,
                    "Sessão ativa em outro dispositivo",
                    self.session_id,
                )
            )
            return

        self.device_id = data.get("deviceId")
        self.mobile_local_ip = data.get("localIp")
        self.mobile_local_port = data.get("localPort")
        self.registered = True
        if data.get("sessionId"):
            self.session_id = data["sessionId"]

        logger.info(
            "Register deviceId=%s localIp=%s:%s",
            self.device_id,
            self.mobile_local_ip,
            self.mobile_local_port,
        )

        await self.send_json(messages.build_registered(self.session_id))
        self._callbacks.set_active_session(self)
        self._callbacks.on_mobile_registered(
            self.device_id or "",
            self.mobile_local_ip or "",
            int(self.mobile_local_port or 0),
        )

    async def handle_offer(self, data: dict[str, Any]) -> None:
        self._callbacks.on_negotiating()

        async def send_ws(payload: dict[str, Any]) -> None:
            await self.send_json(payload)

        async def on_error(code: str, message: str) -> None:
            await self.send_json(messages.build_error(code, message, self.session_id))
            self._callbacks.on_signaling_error(code, message)

        self._peer = PeerManager(
            self._pipeline,
            send_ws=send_ws,
            session_id=self.session_id,
            on_ice_connected=self._callbacks.on_media_connected,
            on_media_stopped=self._callbacks.on_media_stopped,
            on_error=on_error,
        )
        await self._peer.handle_offer(data)

    async def handle_ice_candidate(self, data: dict[str, Any]) -> None:
        if self._peer:
            await self._peer.add_ice_candidate(data.get("candidate") or {})

    async def handle_ping(self, data: dict[str, Any]) -> None:
        self.touch_heartbeat()
        await self.send_json(messages.build_pong(self.session_id, data.get("timestamp")))

    async def handle_bye(self, data: dict[str, Any]) -> None:
        logger.info("Bye recebido: %s", data.get("reason"))
        await self.close()
        self._callbacks.on_mobile_bye(data.get("reason", ""))

    async def close(self) -> None:
        if self._peer:
            await self._peer.close()
            self._peer = None
        self._callbacks.clear_active_session(self)
