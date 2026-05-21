"""Estados globais da conexão."""

from enum import Enum, auto


class ConnectionState(Enum):
    STOPPED = auto()
    WAITING_MOBILE = auto()
    NEGOTIATING = auto()
    CONNECTED = auto()
    ERROR = auto()
