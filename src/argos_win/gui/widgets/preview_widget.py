"""Widget de preview de vídeo."""

from __future__ import annotations

import cv2
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget


class PreviewWidget(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._label = QLabel("Aguardando vídeo…")
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setMinimumSize(640, 360)
        self._label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._label.setStyleSheet(
            "background-color: #1a1a2e; color: #888; border-radius: 8px;"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._label)

    def show_frame(self, frame_bgr: np.ndarray) -> None:
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
        pixmap = QPixmap.fromImage(qimg)
        scaled = pixmap.scaled(
            self._label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self._label.setPixmap(scaled)

    def show_placeholder(self, text: str) -> None:
        self._label.clear()
        self._label.setText(text)
