"""Pipeline thread-safe de frames BGR (último frame wins)."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    pass


class FramePipeline:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._latest: np.ndarray | None = None
        self._width = 0
        self._height = 0
        self._fps = 30

    def set_video_meta(self, width: int, height: int, fps: int) -> None:
        with self._lock:
            self._width = width
            self._height = height
            self._fps = fps if fps > 0 else 30

    @property
    def video_meta(self) -> tuple[int, int, int]:
        with self._lock:
            return self._width, self._height, self._fps

    def push(self, frame_bgr: np.ndarray) -> None:
        with self._lock:
            self._latest = frame_bgr

    def pop_latest(self) -> np.ndarray | None:
        with self._lock:
            frame = self._latest
            self._latest = None
            return frame

    def peek_latest(self) -> np.ndarray | None:
        with self._lock:
            return self._latest

    def clear(self) -> None:
        with self._lock:
            self._latest = None
