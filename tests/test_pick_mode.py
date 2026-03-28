from __future__ import annotations

from PySide6.QtWidgets import QPushButton

from baihe_autogui_inspect.ui.pick_mode import PickModeController


def test_start_hides_window_and_starts_tracking():
    calls: list[str] = []
    messages: list[str] = []

    window = type(
        "WindowStub",
        (),
        {
            "hide": lambda self: calls.append("hide"),
            "show": lambda self: calls.append("show"),
            "raise_": lambda self: calls.append("raise"),
            "activateWindow": lambda self: calls.append("activate"),
        },
    )()
    pick_button = type(
        "ButtonStub",
        (),
        {
            "blockSignals": lambda self, value: calls.append(f"block:{value}"),
            "setChecked": lambda self, value: calls.append(f"checked:{value}"),
        },
    )()
    status_bar = type(
        "StatusBarStub",
        (),
        {"showMessage": lambda self, message: messages.append(message)},
    )()
    controller = PickModeController(window, pick_button, status_bar)

    timer_calls: list[str] = []
    controller._timer = type(
        "TimerStub",
        (),
        {
            "isActive": lambda self: False,
            "start": lambda self: timer_calls.append("timer_start"),
            "stop": lambda self: timer_calls.append("timer_stop"),
        },
    )()

    overlay_calls: list[str] = []
    tracker_calls: list[str] = []

    class OverlayStub:
        def __init__(self, color):
            overlay_calls.append(f"overlay:{color.name()}")

        def deleteLater(self):
            overlay_calls.append("overlay_delete")

        def show_rect(self, *args):
            overlay_calls.append(f"show_rect:{args}")

        def hide_rect(self):
            overlay_calls.append("hide_rect")

    class SignalStub:
        def connect(self, callback):
            tracker_calls.append(callback.__name__)

    class TrackerStub:
        def __init__(self, backend, parent=None):
            tracker_calls.append(f"tracker:{backend}:{parent is controller}")
            self.hovered = SignalStub()
            self.cleared = SignalStub()

        def start(self):
            tracker_calls.append("tracker_start")

        def stop(self):
            tracker_calls.append("tracker_stop")

        def wait(self, timeout):
            tracker_calls.append(f"tracker_wait:{timeout}")

        def isRunning(self):
            return False

        def deleteLater(self):
            tracker_calls.append("tracker_delete")

    original_overlay = PickModeController.start.__globals__["HighlightOverlay"]
    original_tracker = PickModeController.start.__globals__["HoverTracker"]
    original_crosshair = PickModeController.start.__globals__["set_global_crosshair"]
    PickModeController.start.__globals__["HighlightOverlay"] = OverlayStub
    PickModeController.start.__globals__["HoverTracker"] = TrackerStub
    PickModeController.start.__globals__["set_global_crosshair"] = lambda: calls.append("crosshair")

    try:
        assert controller.start("uia") is True
    finally:
        PickModeController.start.__globals__["HighlightOverlay"] = original_overlay
        PickModeController.start.__globals__["HoverTracker"] = original_tracker
        PickModeController.start.__globals__["set_global_crosshair"] = original_crosshair

    assert calls == ["crosshair", "hide"]
    assert messages == ["Pick mode: click any UI element on the desktop to locate it"]
    assert timer_calls == ["timer_start"]
    assert overlay_calls == ["overlay:#ff0000"]
    assert tracker_calls == ["tracker:uia:True", "show_rect", "hide_rect", "tracker_start"]


def test_cancel_shows_window_and_resets_button(qapp):
    calls: list[str] = []

    window = type(
        "WindowStub",
        (),
        {
            "hide": lambda self: calls.append("hide"),
            "show": lambda self: calls.append("show"),
            "raise_": lambda self: calls.append("raise"),
            "activateWindow": lambda self: calls.append("activate"),
        },
    )()
    pick_button = QPushButton()
    pick_button.setCheckable(True)
    pick_button.setChecked(True)
    status_bar = type("StatusBarStub", (), {"showMessage": lambda self, message: None})()
    controller = PickModeController(window, pick_button, status_bar)

    controller._timer = type(
        "TimerStub",
        (),
        {
            "isActive": lambda self: False,
            "start": lambda self: None,
            "stop": lambda self: calls.append("timer_stop"),
        },
    )()
    controller._overlay = type(
        "OverlayStub",
        (),
        {
            "hide_rect": lambda self: calls.append("overlay_hide_rect"),
            "deleteLater": lambda self: calls.append("overlay_delete"),
        },
    )()
    controller._hover_tracker = type(
        "TrackerStub",
        (),
        {
            "stop": lambda self: calls.append("tracker_stop"),
            "wait": lambda self, timeout: calls.append(f"tracker_wait:{timeout}"),
            "isRunning": lambda self: False,
            "deleteLater": lambda self: calls.append("tracker_delete"),
        },
    )()

    original_restore = PickModeController.finish_tracking.__globals__["restore_system_cursors"]
    PickModeController.finish_tracking.__globals__["restore_system_cursors"] = lambda: calls.append(
        "restore"
    )

    try:
        assert controller.cancel() is True
    finally:
        PickModeController.finish_tracking.__globals__["restore_system_cursors"] = original_restore

    assert calls == [
        "timer_stop",
        "restore",
        "overlay_hide_rect",
        "overlay_delete",
        "tracker_stop",
        "tracker_wait:2000",
        "tracker_delete",
        "show",
        "raise",
        "activate",
    ]
    assert pick_button.isChecked() is False
