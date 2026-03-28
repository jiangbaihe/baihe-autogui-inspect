from __future__ import annotations

from loguru import logger
from PySide6.QtCore import QThread, Signal
from pywinauto import Desktop

from baihe_autogui_inspect.core.inspector import element_rectangle
from baihe_autogui_inspect.core.pick_loader import get_cursor_pos


class HoverTracker(QThread):
    """Continuously tracks the element under the mouse cursor."""

    hovered: Signal = Signal(int, int, int, int)  # left, top, right, bottom
    cleared: Signal = Signal()
    _poll_interval_ms = 150

    def __init__(self, backend: str, parent=None):
        super().__init__(parent)
        self._backend = backend

    def run(self) -> None:
        desktop = Desktop(backend=self._backend)
        last_rect: tuple[int, int, int, int] | None = None

        while not self.isInterruptionRequested():
            last_rect = self._poll_once(desktop, last_rect)
            self.msleep(self._poll_interval_ms)

    def stop(self) -> None:
        self.requestInterruption()

    def _poll_once(
        self,
        desktop,
        last_rect: tuple[int, int, int, int] | None,
    ) -> tuple[int, int, int, int] | None:
        try:
            current_rect = self._current_rect(desktop)
        except Exception as exc:
            logger.debug(f"HoverTracker: {exc}")
            return self._clear_last_rect(last_rect)

        if current_rect == last_rect:
            return last_rect
        self._emit_hovered(current_rect)
        return current_rect

    @staticmethod
    def _current_rect(desktop) -> tuple[int, int, int, int]:
        x, y = get_cursor_pos()
        wrapper = desktop.from_point(x, y)
        current_rect = element_rectangle(wrapper.element_info)
        if current_rect is None:
            raise ValueError("Element has no visible rectangle")
        return current_rect

    def _emit_hovered(self, rect: tuple[int, int, int, int]) -> None:
        self.hovered.emit(*rect)  # type: ignore[attr-defined]

    def _clear_last_rect(
        self,
        last_rect: tuple[int, int, int, int] | None,
    ) -> tuple[int, int, int, int] | None:
        if last_rect is not None:
            self.cleared.emit()  # type: ignore[attr-defined]
        return None


