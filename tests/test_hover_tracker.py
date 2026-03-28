from __future__ import annotations

from baihe_autogui_inspect.core.hover_tracker import HoverTracker


def test_poll_once_emits_when_rect_changes():
    tracker = HoverTracker("uia")
    calls: list[tuple[int, int, int, int]] = []
    tracker._current_rect = lambda desktop: (1, 2, 11, 22)  # type: ignore[method-assign]
    tracker._emit_hovered = lambda rect: calls.append(rect)  # type: ignore[method-assign]

    last_rect = tracker._poll_once(object(), None)

    assert calls == [(1, 2, 11, 22)]
    assert last_rect == (1, 2, 11, 22)


def test_poll_once_skips_emit_when_rect_unchanged():
    tracker = HoverTracker("uia")
    calls: list[tuple[int, int, int, int]] = []
    tracker._current_rect = lambda desktop: (1, 2, 11, 22)  # type: ignore[method-assign]
    tracker._emit_hovered = lambda rect: calls.append(rect)  # type: ignore[method-assign]

    last_rect = tracker._poll_once(object(), (1, 2, 11, 22))

    assert calls == []
    assert last_rect == (1, 2, 11, 22)


def test_poll_once_clears_when_current_rect_lookup_fails():
    tracker = HoverTracker("uia")
    calls: list[str] = []

    def _fail(desktop):
        del desktop
        raise RuntimeError("boom")

    tracker._current_rect = _fail  # type: ignore[method-assign]
    tracker._clear_last_rect = lambda rect: calls.append(f"clear:{rect}") or None  # type: ignore[method-assign]

    last_rect = tracker._poll_once(object(), (1, 2, 11, 22))

    assert calls == ["clear:(1, 2, 11, 22)"]
    assert last_rect is None


def test_clear_last_rect_emits_only_when_needed():
    tracker = HoverTracker("uia")
    calls: list[str] = []
    tracker.cleared.connect(lambda: calls.append("cleared"))

    assert tracker._clear_last_rect(None) is None
    assert calls == []

    assert tracker._clear_last_rect((1, 2, 11, 22)) is None
    assert calls == ["cleared"]
