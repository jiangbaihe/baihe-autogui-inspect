from __future__ import annotations

from baihe_autogui_inspect.ui.flash_highlighter import FlashHighlighter


def test_flash_starts_green_blink_sequence(monkeypatch):
    calls: list[str] = []

    class OverlayStub:
        def __init__(self, color):
            calls.append(f"overlay:{color.name()}")

        def show_rect(self, *rect):
            calls.append(f"show:{rect}")

        def hide_rect(self):
            calls.append("hide")

    class TimerStub:
        def start(self, interval):
            calls.append(f"timer_start:{interval}")

        def stop(self):
            calls.append("timer_stop")

    monkeypatch.setitem(
        FlashHighlighter.flash.__globals__,
        "HighlightOverlay",
        OverlayStub,
    )
    monkeypatch.setitem(
        FlashHighlighter.flash.__globals__,
        "element_rectangle",
        lambda value: (1, 2, 11, 22),
    )

    highlighter = FlashHighlighter(duration_ms=300, blink_interval_ms=100)
    highlighter._timer = TimerStub()

    assert highlighter.flash(object()) is True
    assert calls == ["overlay:#22c55e", "timer_start:100", "show:(1, 2, 11, 22)"]


def test_advance_flash_clears_after_remaining_steps():
    calls: list[str] = []

    class OverlayStub:
        def show_rect(self, *rect):
            calls.append(f"show:{rect}")

        def hide_rect(self):
            calls.append("hide")

    class TimerStub:
        def stop(self):
            calls.append("timer_stop")

    highlighter = FlashHighlighter()
    highlighter._overlay = OverlayStub()
    highlighter._timer = TimerStub()
    highlighter._rect = (1, 2, 11, 22)
    highlighter._remaining_steps = 1
    highlighter._visible = False

    highlighter._advance_flash()

    assert calls == ["show:(1, 2, 11, 22)", "timer_stop", "hide"]


