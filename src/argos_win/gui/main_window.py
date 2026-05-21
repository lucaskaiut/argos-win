"""Janela principal do Argos Windows."""

from __future__ import annotations

from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from argos_win.app.connection_state import ConnectionState
from argos_win.app.streaming_orchestrator import StreamingOrchestrator
from argos_win.config.settings import AppSettings
from argos_win.gui.widgets.preview_widget import PreviewWidget
from argos_win.gui.widgets.status_indicator import StatusIndicator
from argos_win.protocol.constants import DEFAULT_PORT, SIGNALING_PATH
from argos_win.services.network_info import build_signaling_url, get_local_lan_ip


class MainWindow(QMainWindow):
    def __init__(self, settings: AppSettings, orchestrator: StreamingOrchestrator) -> None:
        super().__init__()
        self._settings = settings
        self._orchestrator = orchestrator
        self.setWindowTitle("Argos — Webcam Virtual")
        self.setMinimumSize(800, 620)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        self._status = StatusIndicator()
        root.addWidget(self._status)

        self._preview = PreviewWidget()
        root.addWidget(self._preview, stretch=1)

        server_box = QGroupBox("Servidor Windows (configure este IP no app Android)")
        server_form = QFormLayout(server_box)

        lan_ip = get_local_lan_ip()
        self._ip_label = QLabel(lan_ip)
        self._ip_label.setFont(QFont("Consolas", 10))
        self._url_label = QLabel(
            build_signaling_url(lan_ip, settings.signaling_port, SIGNALING_PATH)
        )
        self._url_label.setFont(QFont("Consolas", 9))
        self._url_label.setWordWrap(True)

        self._port_spin = QSpinBox()
        self._port_spin.setRange(1024, 65535)
        self._port_spin.setValue(settings.signaling_port)
        self._port_spin.setEnabled(True)

        server_form.addRow("IP LAN do PC:", self._ip_label)
        server_form.addRow("URL signaling:", self._url_label)
        server_form.addRow("Porta:", self._port_spin)
        root.addWidget(server_box)

        mobile_box = QGroupBox("Celular conectado")
        mobile_form = QFormLayout(mobile_box)
        self._device_label = QLabel("—")
        self._mobile_ip_label = QLabel("—")
        mobile_form.addRow("Device ID:", self._device_label)
        mobile_form.addRow("IP do celular:", self._mobile_ip_label)
        root.addWidget(mobile_box)

        btn_row = QHBoxLayout()
        self._start_btn = QPushButton("Iniciar servidor")
        self._stop_btn = QPushButton("Parar servidor")
        self._stop_btn.setEnabled(False)
        btn_row.addWidget(self._start_btn)
        btn_row.addWidget(self._stop_btn)
        root.addLayout(btn_row)

        self._start_btn.clicked.connect(self._on_start)
        self._stop_btn.clicked.connect(self._on_stop)

        self._orchestrator.state_changed.connect(self._on_state_changed)
        self._orchestrator.mobile_registered.connect(self._on_mobile_registered)
        self._orchestrator.error_message.connect(self._on_error)
        self._orchestrator.virtual_cam_warning.connect(self._on_virtual_cam_warning)

        self._preview_timer = QTimer(self)
        self._preview_timer.setInterval(33)
        self._preview_timer.timeout.connect(self._update_preview)

        self._on_state_changed(orchestrator.state)

        if settings.auto_start_server:
            QTimer.singleShot(300, self._on_start)

    def _on_start(self) -> None:
        self._settings.signaling_port = self._port_spin.value()
        lan_ip = get_local_lan_ip()
        self._url_label.setText(
            build_signaling_url(lan_ip, self._settings.signaling_port, SIGNALING_PATH)
        )
        self._orchestrator.start_server()
        self._start_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._port_spin.setEnabled(False)
        self._preview_timer.start()
        self._preview.show_placeholder("Aguardando conexão do celular…")

    def _on_stop(self) -> None:
        self._preview_timer.stop()
        self._orchestrator.stop_server()
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._port_spin.setEnabled(True)
        self._device_label.setText("—")
        self._mobile_ip_label.setText("—")
        self._preview.show_placeholder("Servidor parado")

    def _on_state_changed(self, state: ConnectionState) -> None:
        self._status.set_state(state)
        if state == ConnectionState.STOPPED:
            self._start_btn.setEnabled(True)
            self._stop_btn.setEnabled(False)

    def _on_mobile_registered(self, device_id: str, local_ip: str, local_port: int) -> None:
        self._device_label.setText(device_id or "—")
        self._mobile_ip_label.setText(
            f"{local_ip}:{local_port}" if local_ip else "—"
        )

    def _on_error(self, message: str) -> None:
        QMessageBox.warning(self, "Erro Argos", message)

    def _on_virtual_cam_warning(self, message: str) -> None:
        QMessageBox.information(self, "Webcam virtual", message)

    def _update_preview(self) -> None:
        frame = self._orchestrator.pipeline.peek_latest()
        if frame is not None:
            self._preview.show_frame(frame)
            if self._orchestrator.state == ConnectionState.CONNECTED:
                self._orchestrator.push_frame_to_virtual_cam(frame)

    def closeEvent(self, event) -> None:
        self._on_stop()
        super().closeEvent(event)
