"""Entrypoint do Argos Windows client."""

from __future__ import annotations

import argparse
import signal
import sys
import time

from argos_win.app.streaming_orchestrator import StreamingOrchestrator
from argos_win.config.store import CONFIG_DIR, load_settings, save_settings
from argos_win.infrastructure.logging import setup_logging
from argos_win.protocol.constants import DEFAULT_PORT, SIGNALING_PATH
from argos_win.services.network_info import build_signaling_url, get_local_lan_ip


def main_headless() -> int:
    """Servidor signaling sem GUI (útil no WSL sem WSLg)."""
    setup_logging(log_dir=CONFIG_DIR / "logs")
    settings = load_settings()
    orchestrator = StreamingOrchestrator(settings)

    def shutdown(_sig=None, _frame=None) -> None:
        orchestrator.stop_server()
        save_settings(settings)
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    orchestrator.start_server()
    lan_ip = get_local_lan_ip()
    url = build_signaling_url(lan_ip, settings.signaling_port, SIGNALING_PATH)
    print("Argos — modo headless (sem janela)")
    print(f"  Signaling: {url}")
    print(f"  Health:    http://{lan_ip}:{settings.signaling_port}/health")
    print("  Configure o IP do PC no app Android e toque Iniciar.")
    print("  Ctrl+C para parar.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown()
    return 0


def main_gui() -> int:
    from argos_win.infrastructure.qt_platform import fix_qt_platform_plugins

    fix_qt_platform_plugins()

    from PyQt5.QtWidgets import QApplication

    from argos_win.gui.main_window import MainWindow

    setup_logging(log_dir=CONFIG_DIR / "logs")
    settings = load_settings()
    app = QApplication(sys.argv)
    app.setApplicationName("Argos")
    app.setOrganizationName("Argos")

    orchestrator = StreamingOrchestrator(settings)
    window = MainWindow(settings, orchestrator)
    window.show()

    code = app.exec_()
    save_settings(settings)
    orchestrator.stop_server()
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description="Argos Windows client")
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Apenas servidor WebSocket/WebRTC, sem interface gráfica",
    )
    args, _ = parser.parse_known_args()
    if args.headless:
        return main_headless()
    return main_gui()


if __name__ == "__main__":
    raise SystemExit(main())
