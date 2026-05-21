"""Persistência de configurações em JSON."""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path

from argos_win.config.settings import AppSettings

CONFIG_DIR = Path(os.environ.get("APPDATA", Path.home())) / "Argos"
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_settings() -> AppSettings:
    if not CONFIG_FILE.exists():
        return AppSettings()
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        return AppSettings(**{k: v for k, v in data.items() if k in AppSettings.__dataclass_fields__})
    except (json.JSONDecodeError, TypeError):
        return AppSettings()


def save_settings(settings: AppSettings) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")
