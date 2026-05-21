"""Configurações da aplicação."""

from __future__ import annotations

from dataclasses import dataclass

from argos_win.protocol.constants import DEFAULT_PORT


@dataclass
class AppSettings:
    signaling_host: str = "0.0.0.0"
    signaling_port: int = DEFAULT_PORT
    auto_start_server: bool = False
    virtual_cam_width: int = 1280
    virtual_cam_height: int = 720
    virtual_cam_fps: int = 30
    virtual_cam_enabled: bool = True
    heartbeat_timeout_sec: float = 15.0
