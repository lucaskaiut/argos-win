"""Orquestrador principal — servidor signaling, WebRTC, pipeline e webcam virtual."""

from __future__ import annotations

import asyncio
import logging
import threading
from typing import TYPE_CHECKING

from PyQt5.QtCore import QObject, pyqtSignal

from argos_win.app.connection_state import ConnectionState
from argos_win.config.settings import AppSettings
from argos_win.services.frame_pipeline import FramePipeline
from argos_win.services.virtual_camera import VirtualCameraService
from argos_win.signaling.server import SignalingServer
from argos_win.signaling.session import SessionCallbacks

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class StreamingOrchestrator(QObject):
    state_changed = pyqtSignal(object)
    mobile_registered = pyqtSignal(str, str, int)
    error_message = pyqtSignal(str)
    virtual_cam_warning = pyqtSignal(str)

    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        self._settings = settings
        self._state = ConnectionState.STOPPED
        self._pipeline = FramePipeline()
        self._virtual_cam: VirtualCameraService | None = None
        self._callbacks = SessionCallbacks()
        self._server: SignalingServer | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._wire_callbacks()

    @property
    def state(self) -> ConnectionState:
        return self._state

    @property
    def pipeline(self) -> FramePipeline:
        return self._pipeline

    @property
    def settings(self) -> AppSettings:
        return self._settings

    def _wire_callbacks(self) -> None:
        self._callbacks.on_mobile_registered = self._on_mobile_registered
        self._callbacks.on_negotiating = lambda: self._set_state(ConnectionState.NEGOTIATING)
        self._callbacks.on_media_connected = self._on_media_connected
        self._callbacks.on_media_stopped = self._on_media_stopped
        self._callbacks.on_mobile_bye = self._on_mobile_bye
        self._callbacks.on_signaling_error = self._on_signaling_error
        self._callbacks.on_client_disconnected = self._on_client_disconnected

    def _set_state(self, state: ConnectionState) -> None:
        if self._state != state:
            self._state = state
            self.state_changed.emit(state)

    def _on_mobile_registered(self, device_id: str, local_ip: str, local_port: int) -> None:
        self.mobile_registered.emit(device_id, local_ip, local_port)
        self._set_state(ConnectionState.WAITING_MOBILE)

    def _on_media_connected(self) -> None:
        self._set_state(ConnectionState.CONNECTED)
        if self._settings.virtual_cam_enabled:
            w, h, fps = self._pipeline.video_meta
            cam_w = self._settings.virtual_cam_width or w
            cam_h = self._settings.virtual_cam_height or h
            cam_fps = self._settings.virtual_cam_fps or fps
            self._virtual_cam = VirtualCameraService(
                cam_w,
                cam_h,
                cam_fps,
                on_error=lambda msg: self.virtual_cam_warning.emit(msg),
            )
            self._virtual_cam.start()

    def _on_media_stopped(self) -> None:
        self._stop_virtual_cam()
        if self._state == ConnectionState.CONNECTED:
            self._set_state(ConnectionState.WAITING_MOBILE)

    def _on_mobile_bye(self, _reason: str) -> None:
        self._pipeline.clear()
        self._stop_virtual_cam()
        if self._thread and self._thread.is_alive():
            self._set_state(ConnectionState.WAITING_MOBILE)
        else:
            self._set_state(ConnectionState.STOPPED)

    def _on_signaling_error(self, code: str, message: str) -> None:
        self.error_message.emit(f"[{code}] {message}")
        self._set_state(ConnectionState.ERROR)

    def _on_client_disconnected(self) -> None:
        self._pipeline.clear()
        self._stop_virtual_cam()
        if self._thread and self._thread.is_alive():
            self._set_state(ConnectionState.WAITING_MOBILE)

    def _stop_virtual_cam(self) -> None:
        if self._virtual_cam:
            self._virtual_cam.stop()
            self._virtual_cam = None

    def push_frame_to_virtual_cam(self, frame) -> None:
        if self._virtual_cam and self._virtual_cam.available:
            self._virtual_cam.push_frame(frame)

    def start_server(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_async_thread, daemon=True)
        self._thread.start()

    def stop_server(self) -> None:
        self._stop_event.set()
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self._async_stop(), self._loop)
        if self._thread:
            self._thread.join(timeout=5.0)
        self._thread = None
        self._pipeline.clear()
        self._stop_virtual_cam()
        self._set_state(ConnectionState.STOPPED)

    def _run_async_thread(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._async_run())
        except Exception:
            logger.exception("Erro no loop asyncio")
            self._set_state(ConnectionState.ERROR)
        finally:
            self._loop.close()
            self._loop = None

    async def _async_run(self) -> None:
        self._server = SignalingServer(
            self._settings.signaling_host,
            self._settings.signaling_port,
            self._pipeline,
            self._callbacks,
        )
        await self._server.start()
        self._set_state(ConnectionState.WAITING_MOBILE)

        while not self._stop_event.is_set():
            await asyncio.sleep(0.2)

        await self._async_stop()

    async def _async_stop(self) -> None:
        if self._server:
            await self._server.stop()
            self._server = None
