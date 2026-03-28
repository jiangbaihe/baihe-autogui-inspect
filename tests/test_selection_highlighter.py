from __future__ import annotations

from baihe_autogui_inspect.ui.selection_highlighter import SelectionHighlighter


def test_sync_shows_overlay_for_allowed_node(monkeypatch):
    calls: list[str] = []

    class OverlayStub:
        def __init__(self, color):
            calls.append(f"overlay:{color.name()}")

        def show_rect(self, *rect):
            calls.append(f"show:{rect}")

        def hide_rect(self):
            calls.append("hide")

    monkeypatch.setitem(
        SelectionHighlighter.sync.__globals__,
        "HighlightOverlay",
        OverlayStub,
    )
    monkeypatch.setitem(
        SelectionHighlighter.sync.__globals__,
        "element_rectangle",
        lambda node: (1, 2, 11, 22),
    )

    highlighter = SelectionHighlighter()
    highlighter.sync(object(), allowed=True)

    assert calls == ["overlay:#facc15", "show:(1, 2, 11, 22)"]


def test_sync_clears_overlay_when_disallowed(monkeypatch):
    calls: list[str] = []

    class OverlayStub:
        def __init__(self, color):
            del color

        def show_rect(self, *rect):
            calls.append(f"show:{rect}")

        def hide_rect(self):
            calls.append("hide")

    monkeypatch.setitem(
        SelectionHighlighter.sync.__globals__,
        "HighlightOverlay",
        OverlayStub,
    )
    monkeypatch.setitem(
        SelectionHighlighter.sync.__globals__,
        "element_rectangle",
        lambda node: (1, 2, 11, 22),
    )

    highlighter = SelectionHighlighter()
    highlighter.sync(object(), allowed=True)
    highlighter.sync(object(), allowed=False)

    assert calls == ["show:(1, 2, 11, 22)", "hide"]


