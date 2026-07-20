"""Centralized logging for the AI Operating System.

Provides structured JSON logging with rotation, multiple destinations,
and consistent formatting across all modules.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


_LOG_DIR: Optional[Path] = None
_INITIALIZED = False


def setup_logging(
    project_root: str,
    log_level: str = "INFO",
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> None:
    global _LOG_DIR, _INITIALIZED

    if _INITIALIZED:
        return

    _LOG_DIR = Path(project_root) / "logs"
    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    json_fmt = logging.Formatter(
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
        '"name": "%(name)s", "message": "%(message)s"}'
    )

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    console.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    root.addHandler(console)

    file_handler = RotatingFileHandler(
        _LOG_DIR / "aios.log",
        maxBytes=max_bytes,
        backupCount=backup_count,
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(json_fmt)
    root.addHandler(file_handler)

    error_handler = RotatingFileHandler(
        _LOG_DIR / "error.log",
        maxBytes=max_bytes,
        backupCount=backup_count,
    )
    error_handler.setLevel(logging.WARNING)
    error_handler.setFormatter(json_fmt)
    root.addHandler(error_handler)

    _INITIALIZED = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def get_log_dir() -> Optional[Path]:
    return _LOG_DIR
