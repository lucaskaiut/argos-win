"""Política de codec de vídeo."""

from __future__ import annotations

from typing import Any

from argos_win.protocol.messages import is_h264_codec


def validate_offer_video(video: dict[str, Any] | None) -> str | None:
    """Retorna código de erro se codec não suportado; None se OK."""
    if not is_h264_codec(video):
        return "UNSUPPORTED_CODEC"
    return None
