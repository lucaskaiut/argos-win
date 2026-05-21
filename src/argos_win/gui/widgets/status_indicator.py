"""Indicador visual de status da conexão."""

from __future__ import annotations

from PyQt5.QtWidgets import QHBoxLayout, QLabel, QWidget

from argos_win.app.connection_state import ConnectionState

_STATE_STYLES = {
    ConnectionState.STOPPED: ("#6c757d", "Parado"),
    ConnectionState.WAITING_MOBILE: ("#ffc107", "Aguardando celular"),
    ConnectionState.NEGOTIATING: ("#17a2b8", "Conectando…"),
    ConnectionState.CONNECTED: ("#28a745", "Transmitindo"),
    ConnectionState.ERROR: ("#dc3545", "Erro"),
}


class StatusIndicator(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._dot = QLabel("●")
        self._dot.setStyleSheet("font-size: 18px; color: #6c757d;")
        self._text = QLabel("Parado")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._dot)
        layout.addWidget(self._text)
        layout.addStretch()

    def set_state(self, state: ConnectionState) -> None:
        color, label = _STATE_STYLES.get(state, ("#6c757d", "Desconhecido"))
        self._dot.setStyleSheet(f"font-size: 18px; color: {color};")
        self._text.setText(label)
