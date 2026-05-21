"""Configuração de logging."""

from __future__ import annotations

import logging
import sys
from pathlib import Path


def setup_logging(level: int = logging.INFO, log_dir: Path | None = None) -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_dir / "argos-win.log", encoding="utf-8")
        handlers.append(file_handler)

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
        force=True,
    )
