"""Construção e validação de mensagens JSON do protocolo."""

from __future__ import annotations

import time
from typing import Any

from argos_win.protocol import errors
from argos_win.protocol.constants import PROTOCOL_VERSION, SERVER_ID


def _base(session_id: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"protocolVersion": PROTOCOL_VERSION}
    if session_id:
        payload["sessionId"] = session_id
    return payload


def build_registered(session_id: str) -> dict[str, Any]:
    return {
        **_base(session_id),
        "type": "registered",
        "serverId": SERVER_ID,
    }


def build_answer(session_id: str, sdp: str) -> dict[str, Any]:
    return {
        **_base(session_id),
        "type": "answer",
        "timestamp": int(time.time() * 1000),
        "sdp": sdp,
    }


def build_pong(session_id: str, timestamp: int | None) -> dict[str, Any]:
    return {
        "type": "pong",
        "sessionId": session_id,
        "timestamp": timestamp if timestamp is not None else int(time.time() * 1000),
    }


def build_ice_candidate(session_id: str, candidate: str, sdp_mid: str | None, sdp_mline_index: int | None) -> dict[str, Any]:
    return {
        **_base(session_id),
        "type": "ice-candidate",
        "timestamp": int(time.time() * 1000),
        "candidate": {
            "candidate": candidate,
            "sdpMid": sdp_mid,
            "sdpMLineIndex": sdp_mline_index,
        },
    }


def build_error(code: str, message: str, session_id: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"type": "error", "code": code, "message": message}
    if session_id:
        payload["sessionId"] = session_id
    return payload


def is_h264_codec(video_meta: dict[str, Any] | None) -> bool:
    if not video_meta:
        return True
    codec = str(video_meta.get("codec", "H264")).upper().replace(".", "")
    return codec in ("H264", "AVC")
