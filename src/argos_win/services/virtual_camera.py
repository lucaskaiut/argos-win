"""Webcam virtual via pyvirtualcam."""

from __future__ import annotations

import logging
import threading
from typing import Callable

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class VirtualCameraService:
    def __init__(
        self,
        width: int,
        height: int,
        fps: int,
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        self._width = width
        self._height = height
        self._fps = fps
        self._on_error = on_error
        self._camera = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._frame_lock = threading.Lock()
        self._pending: np.ndarray | None = None
        self._available = False

    @property
    def available(self) -> bool:
        return self._available

    def start(self) -> bool:
        try:
            import pyvirtualcam

            self._camera = pyvirtualcam.Camera(
                width=self._width,
                height=self._height,
                fps=self._fps,
                fmt=pyvirtualcam.PixelFormat.BGR,
            )
            self._available = True
            self._stop.clear()
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
            logger.info("Webcam virtual iniciada %sx%s@%s", self._width, self._height, self._fps)
            return True
        except Exception as exc:
            self._available = False
            msg = (
                "Não foi possível iniciar a webcam virtual. "
                "Instale o OBS Studio e ative a 'Câmera Virtual OBS'. "
                f"Detalhe: {exc}"
            )
            logger.error(msg)
            if self._on_error:
                self._on_error(msg)
            return False

    def push_frame(self, frame_bgr: np.ndarray) -> None:
        if not self._available:
            return
        resized = cv2.resize(frame_bgr, (self._width, self._height))
        with self._frame_lock:
            self._pending = resized

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None
        if self._camera:
            try:
                self._camera.close()
            except Exception:
                pass
            self._camera = None
        self._available = False
        with self._frame_lock:
            self._pending = None

    def _run_loop(self) -> None:
        import pyvirtualcam

        assert self._camera is not None
        interval = 1.0 / max(self._fps, 1)
        while not self._stop.is_set():
            with self._frame_lock:
                frame = self._pending
            if frame is not None:
                try:
                    self._camera.send(frame)
                    self._camera.sleep_until_next_frame()
                except Exception as exc:
                    logger.warning("Erro ao enviar frame para webcam virtual: %s", exc)
                    self._stop.wait(interval)
            else:
                self._stop.wait(interval)
