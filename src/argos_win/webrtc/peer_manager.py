"""Gerenciamento RTCPeerConnection (answerer)."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiortc import (
    RTCIceCandidate,
    RTCPeerConnection,
    RTCSessionDescription,
    RTCConfiguration,
)

from argos_win.protocol import messages
from argos_win.webrtc.codec_policy import validate_offer_video
from argos_win.webrtc.video_track_consumer import VideoTrackConsumer
from argos_win.services.frame_pipeline import FramePipeline

logger = logging.getLogger(__name__)

OnError = Callable[[str, str], Awaitable[None]]


class PeerManager:
    def __init__(
        self,
        pipeline: FramePipeline,
        send_ws: Callable[[dict[str, Any]], Awaitable[None]],
        session_id: str,
        on_ice_connected: Callable[[], None] | None = None,
        on_media_stopped: Callable[[], None] | None = None,
        on_error: OnError | None = None,
    ) -> None:
        self._pipeline = pipeline
        self._send_ws = send_ws
        self._session_id = session_id
        self._on_ice_connected = on_ice_connected
        self._on_media_stopped = on_media_stopped
        self._on_error = on_error
        self._pc: RTCPeerConnection | None = None
        self._consumer = VideoTrackConsumer(
            pipeline,
            on_connected=on_ice_connected,
            on_stopped=on_media_stopped,
        )

    @property
    def peer_connection(self) -> RTCPeerConnection | None:
        return self._pc

    async def handle_offer(self, data: dict[str, Any]) -> bool:
        sdp = data.get("sdp")
        if not sdp:
            if self._on_error:
                await self._on_error("INVALID_SDP", "Campo sdp ausente no offer")
            return False

        video = data.get("video") or {}
        codec_err = validate_offer_video(video)
        if codec_err:
            if self._on_error:
                await self._on_error(codec_err, f"Codec não suportado: {video.get('codec')}")
            return False

        width = int(video.get("width") or 1280)
        height = int(video.get("height") or 1080)
        fps = int(video.get("fps") or 30)
        self._pipeline.set_video_meta(width, height, fps)

        if self._pc:
            await self.close()

        pc = RTCPeerConnection(configuration=RTCConfiguration(iceServers=[]))
        self._pc = pc

        @pc.on("track")
        def on_track(track) -> None:
            logger.info("Track recebido: %s", track.kind)
            if track.kind == "video":
                self._consumer.start(track)

        @pc.on("icecandidate")
        async def on_ice(candidate) -> None:
            if candidate and candidate.candidate:
                await self._send_ws(
                    messages.build_ice_candidate(
                        self._session_id,
                        candidate.candidate,
                        candidate.sdpMid,
                        candidate.sdpMLineIndex,
                    )
                )

        @pc.on("iceconnectionstatechange")
        async def on_ice_state() -> None:
            logger.info("ICE state: %s", pc.iceConnectionState)
            if pc.iceConnectionState == "failed" and self._on_error:
                await self._on_error("INTERNAL_ERROR", "Falha na conexão ICE")

        try:
            await pc.setRemoteDescription(RTCSessionDescription(sdp=sdp, type="offer"))
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)
            await self._send_ws(messages.build_answer(self._session_id, pc.localDescription.sdp))
            logger.info("Answer enviado session=%s", self._session_id)
            return True
        except Exception as exc:
            logger.exception("Erro ao processar offer")
            if self._on_error:
                await self._on_error("INTERNAL_ERROR", str(exc))
            await self.close()
            return False

    async def add_ice_candidate(self, candidate: dict[str, Any]) -> None:
        if not self._pc or not candidate or not candidate.get("candidate"):
            return
        ice = RTCIceCandidate(
            sdpMid=candidate.get("sdpMid"),
            sdpMLineIndex=candidate.get("sdpMLineIndex"),
            candidate=candidate.get("candidate"),
        )
        await self._pc.addIceCandidate(ice)

    async def close(self) -> None:
        await self._consumer.stop()
        if self._pc:
            await self._pc.close()
            self._pc = None
