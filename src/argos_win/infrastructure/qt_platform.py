"""Corrige conflito de plugins Qt entre opencv-python e PyQt5 (comum no Linux/WSL)."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def fix_qt_platform_plugins() -> None:
    """
    OpenCV (opencv-python) embute plugins Qt em cv2/qt/plugins que quebram o PyQt5.
    Força o uso dos plugins do PyQt5 antes de criar QApplication.
    """
    # Remove caminhos que o OpenCV possa ter injetado no processo.
    for key in ("QT_QPA_PLATFORM_PLUGIN_PATH", "QT_PLUGIN_PATH"):
        os.environ.pop(key, None)

    try:
        import PyQt5
    except ImportError:
        return

    plugins_dir = Path(PyQt5.__file__).resolve().parent / "Qt5" / "plugins" / "platforms"
    if plugins_dir.is_dir():
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(plugins_dir)

    # Evita que cv2/qt/plugins entre no caminho de busca do Qt.
    for entry in list(sys.path):
        if "cv2" in entry.replace("\\", "/"):
            qt_plugins = Path(entry) / "qt" / "plugins"
            if qt_plugins.exists():
                break
