from __future__ import annotations

from loguru import logger
from PySide6.QtCore import QThread, Signal


class WorkerThread(QThread):
    """Small QThread base class that centralizes error reporting."""

    error = Signal(str)
    _worker_name = "WorkerThread"

    def run(self) -> None:
        try:
            self._run_impl()
        except Exception as exc:
            logger.exception(f"{self._worker_name} error: {exc}")
            self.error.emit(str(exc))  # type: ignore[attr-defined]

    def _run_impl(self) -> None:
        raise NotImplementedError


