"""Utilitários de rede — IP LAN do Windows."""

from __future__ import annotations

import socket


def get_local_lan_ip() -> str:
    """Retorna o IPv4 da interface usada para saída na LAN."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def build_signaling_url(ip: str, port: int, path: str) -> str:
    return f"ws://{ip}:{port}{path}"
