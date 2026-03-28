from __future__ import annotations

from PySide6.QtCore import QObject, QTimer
from PySide6.QtGui import QColor

from baihe_autogui_inspect.core.inspector import element_rectangle
from baihe_autogui_inspect.ui.overlay import HighlightOverlay


class FlashHighlighter(QObject):
    """Shows a temporary green outline for a successfully resolved control."""

    def __init__(self, parent=None, *, duration_ms: int = 1000, blink_interval_ms: int = 150):
        super().__init__(parent)
        self._duration_ms = duration_ms
        self._blink_interval_ms = blink_interval_ms
        self._overlay: HighlightOverlay | None = None
        self._rect: tuple[int, int, int, int] | None = None
        self._remaining_steps = 0
        self._visible = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance_flash)

    def duration_ms(self) -> int:
        return self._duration_ms

    def flash(self, value) -> bool:
        rect = element_rectangle(value)
        if rect is None:
            self.clear()
            return False

        if self._overlay is None:
            self._overlay = HighlightOverlay(color=QColor("#22c55e"))
        self._rect = rect
        self._remaining_steps = max(1, self._duration_ms // self._blink_interval_ms)
        self._visible = False
        self._timer.start(self._blink_interval_ms)
        self._advance_flash()
        return True

    def _advance_flash(self) -> None:
        if self._overlay is None or self._rect is None:
            self.clear()
            return

        if self._visible:
            self._overlay.hide_rect()
        else:
            self._overlay.show_rect(*self._rect)
        self._visible = not self._visible
        self._remaining_steps -= 1
        if self._remaining_steps <= 0:
            self.clear()

    def clear(self) -> None:
        self._timer.stop()
        self._rect = None
        self._remaining_steps = 0
        self._visible = False
        if self._overlay is None:
            return
        self._overlay.hide_rect()
