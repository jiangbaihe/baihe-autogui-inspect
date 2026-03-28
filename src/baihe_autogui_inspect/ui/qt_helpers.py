from __future__ import annotations

from typing import Optional, Protocol, TypeVar

from PySide6.QtCore import QSignalBlocker


class _DisposableWorker(Protocol):
    def isRunning(self) -> bool: ...
    def wait(self, timeout: int) -> None: ...
    def deleteLater(self) -> None: ...


WorkerT = TypeVar("WorkerT", bound=_DisposableWorker)


def dispose_worker(worker: Optional[WorkerT]) -> Optional[WorkerT]:  # noqa: UP045
    if worker is None:
        return None
    if worker.isRunning():
        worker.wait(2000)
    if not worker.isRunning():
        worker.deleteLater()
    return None


def set_checked_silently(button, checked: bool) -> None:
    blocker = QSignalBlocker(button)
    button.setChecked(checked)
    del blocker


def show_window_foreground(window) -> None:
    window.show()
    window.raise_()
    window.activateWindow()


