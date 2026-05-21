from argos_win.protocol.messages import (
    build_registered,
    build_pong,
    is_h264_codec,
)


def test_build_registered():
    msg = build_registered("sess-1")
    assert msg["type"] == "registered"
    assert msg["sessionId"] == "sess-1"
    assert msg["protocolVersion"] == "1.0"


def test_build_pong():
    msg = build_pong("sess-1", 12345)
    assert msg["type"] == "pong"
    assert msg["timestamp"] == 12345


def test_h264_codec():
    assert is_h264_codec({"codec": "H264"})
    assert is_h264_codec({"codec": "h264"})
    assert not is_h264_codec({"codec": "VP8"})
