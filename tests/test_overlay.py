from __future__ import annotations

from baihe_autogui_inspect.ui.overlay import HighlightOverlay


def test_show_rect_adds_region_highlight(monkeypatch):
    calls: list[object] = []

    monkeypatch.setattr(
        "baihe_autogui_inspect.ui.overlay.autogui_overlay.add",
        lambda spec, timeout=None: calls.append((spec, timeout)) or "highlight-1",
    )
    monkeypatch.setattr(
        "baihe_autogui_inspect.ui.overlay.autogui_overlay.remove",
        lambda highlight_id: calls.append(highlight_id),
    )

    overlay = HighlightOverlay()
    overlay.show_rect(15, 25, 35, 45)

    spec, timeout = calls[0]
    assert spec.region == (15, 25, 20, 20)
    assert spec.color == "#f87171"
    assert spec.thickness == 3
    assert timeout is None


def test_hide_rect_clears_current_rect(monkeypatch):
    removed: list[str] = []
    monkeypatch.setattr(
        "baihe_autogui_inspect.ui.overlay.autogui_overlay.add",
        lambda spec, timeout=None: "highlight-1",
    )
    monkeypatch.setattr(
        "baihe_autogui_inspect.ui.overlay.autogui_overlay.remove",
        lambda highlight_id: removed.append(highlight_id),
    )

    overlay = HighlightOverlay()
    overlay.set_rect(1, 2, 11, 22)
    overlay.show_rect(1, 2, 11, 22)

    overlay.hide_rect()

    assert overlay._rect is None
    assert removed == ["highlight-1"]
