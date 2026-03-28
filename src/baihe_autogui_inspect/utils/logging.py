from __future__ import annotations

import os
import sys
from pathlib import Path

from loguru import logger

DEFAULT_LOG_FILE = "baihe_autogui_inspect.log"
DEFAULT_LOG_LEVEL = "DEBUG"
LOG_LEVEL_ENV = "BAIHE_AUTOGUI_INSPECT_LOG_LEVEL"
LOG_FILE_ENV = "BAIHE_AUTOGUI_INSPECT_LOG_FILE"
CONSOLE_FORMAT = (
    "<green>{time:HH:mm:ss.SSS}</green> | <level>{level:<8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
FILE_FORMAT = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{line} - {message}"


def _resolve_setting(explicit_value, env_name: str, default_value):
    return explicit_value or os.getenv(env_name) or default_value


def resolve_log_level(level: str | None = None) -> str:
    """Resolve the effective log level from an explicit value or environment."""
    return str(_resolve_setting(level, LOG_LEVEL_ENV, DEFAULT_LOG_LEVEL)).upper()


def resolve_log_path(log_file: str | Path | None = None) -> Path:
    """Resolve the log file path and normalize relative paths against the current working directory."""
    raw_path = _resolve_setting(log_file, LOG_FILE_ENV, DEFAULT_LOG_FILE)
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path


def _configure_console_logging(level: str) -> None:
    logger.add(
        sys.stderr,
        level=level,
        format=CONSOLE_FORMAT,
        colorize=True,
        backtrace=False,
        diagnose=False,
    )


def _configure_file_logging(log_path: Path) -> None:
    logger.add(
        log_path,
        level="DEBUG",
        rotation="5 MB",
        retention=3,
        encoding="utf-8",
        format=FILE_FORMAT,
        backtrace=False,
        diagnose=False,
    )


def setup_logging(level: str | None = None, log_file: str | Path | None = None) -> Path:
    resolved_level = resolve_log_level(level)
    resolved_log_path = resolve_log_path(log_file)
    resolved_log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.remove()
    _configure_console_logging(resolved_level)
    _configure_file_logging(resolved_log_path)
    logger.debug(f"Logging initialized: level={resolved_level} file='{resolved_log_path}'")
    return resolved_log_path
