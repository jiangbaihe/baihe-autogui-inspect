from __future__ import annotations

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QPushButton, QStatusBar, QWidget

from baihe_autogui_inspect.core.hover_tracker import HoverTracker
from baihe_autogui_inspect.core.pick_loader import (
    get_cursor_pos,
    is_mouse_pressed,
    is_right_mouse_pressed,
    restore_system_cursors,
    set_global_crosshair,
)
from baihe_autogui_inspect.ui.overlay import SOFT_RED, HighlightOverlay
from baihe_autogui_inspect.ui.qt_helpers import set_checked_silently, show_window_foreground


class PickModeController(QObject):
    """Controls the transient desktop pick mode UI and input loop."""

    pick_requested = Signal(int, int)
    _poll_interval_ms = 50
    _tracker_shutdown_timeout_ms = 2000
    _pick_mode_message = "Pick mode: click any UI element on the desktop to locate it"

    def __init__(
        self,
        window: QWidget,
        pick_button: QPushButton,
        status_bar: QStatusBar,
        parent=None,
    ):
        super().__init__(parent)
        self._window = window
        self._pick_button = pick_button
        self._status_bar = status_bar
        self._hover_tracker: HoverTracker | None = None
        self._overlay: HighlightOverlay | None = None
        self._timer = QTimer(self)
        self._timer.setInterval(self._poll_interval_ms)
        self._timer.timeout.connect(self._poll)

    def is_active(self) -> bool:
        return self._timer.isActive()

    def start(self, backend: str) -> bool:
        if self.is_active():
            return False

        set_global_crosshair()
        self._show_status(self._pick_mode_message)
        self._window.hide()
        self._start_hover_tracking(backend)
        self._timer.start()
        return True

    def finish_tracking(self) -> bool:
        if not self._has_session():
            return False

        self._timer.stop()
        restore_system_cursors()
        self._dispose_overlay()
        self._dispose_tracker()
        self._reset_button()
        return True

    def cancel(self) -> bool:
        if not self.finish_tracking():
            return False
        self._show_window()
        return True

    def shutdown(self) -> None:
        self.finish_tracking()

    def _poll(self) -> None:
        if is_right_mouse_pressed():
            self.cancel()
            return
        if not is_mouse_pressed():
            return

        self._emit_pick_request()

    def _has_session(self) -> bool:
        return (
            self._timer.isActive() or self._hover_tracker is not None or self._overlay is not None
        )

    def _dispose_overlay(self) -> None:
        if self._overlay is None:
            return
        self._overlay.hide_rect()
        self._overlay.deleteLater()
        self._overlay = None

    def _dispose_tracker(self) -> None:
        tracker = self._hover_tracker
        self._hover_tracker = None
        if tracker is None:
            return
        tracker.stop()
        tracker.wait(self._tracker_shutdown_timeout_ms)
        if not tracker.isRunning():
            tracker.deleteLater()

    def _reset_button(self) -> None:
        set_checked_silently(self._pick_button, False)

    def _show_status(self, message: str) -> None:
        self._status_bar.showMessage(message)

    def _start_hover_tracking(self, backend: str) -> None:
        self._overlay = HighlightOverlay(color=QColor(SOFT_RED))
        self._hover_tracker = HoverTracker(backend, parent=self)
        self._hover_tracker.hovered.connect(self._overlay.show_rect)  # type: ignore[attr-defined]
        self._hover_tracker.cleared.connect(self._overlay.hide_rect)  # type: ignore[attr-defined]
        self._hover_tracker.start()

    def _emit_pick_request(self) -> None:
        x, y = get_cursor_pos()
        self.finish_tracking()
        self.pick_requested.emit(x, y)  # type: ignore[attr-defined]

    def _show_window(self) -> None:
        show_window_foreground(self._window)
