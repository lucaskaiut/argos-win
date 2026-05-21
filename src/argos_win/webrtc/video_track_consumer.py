"""Consome track de vídeo WebRTC e publica frames no pipeline."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Callable

import numpy as np

if TYPE_CHECKING:
    from aiortc import MediaStreamTrack

    from argos_win.services.frame_pipeline import FramePipeline

logger = logging.getLogger(__name__)


class VideoTrackConsumer:
    def __init__(
        self,
        pipeline: FramePipeline,
        on_connected: Callable[[], None] | None = None,
        on_stopped: Callable[[], None] | None = None,
    ) -> None:
        self._pipeline = pipeline
        self._on_connected = on_connected
        self._on_stopped = on_stopped
        self._task: asyncio.Task | None = None
        self._connected_notified = False

    def start(self, track: MediaStreamTrack) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
        self._connected_notified = False
        self._task = asyncio.create_task(self._consume(track))

    async def stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None
        if self._on_stopped:
            self._on_stopped()

    async def _consume(self, track: MediaStreamTrack) -> None:
        logger.info("Iniciando consumo de track de vídeo")
        try:
            while True:
                frame = await track.recv()
                img = frame.to_ndarray(format="bgr24")
                self._pipeline.push(img)
                if not self._connected_notified:
                    self._connected_notified = True
                    if self._on_connected:
                        self._on_connected()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.info("Track de vídeo encerrado: %s", exc)
        finally:
            if self._on_stopped:
                self._on_stopped()
