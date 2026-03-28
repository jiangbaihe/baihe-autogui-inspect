from __future__ import annotations

from PySide6.QtCore import QRect

from baihe_autogui_inspect.ui.overlay import HighlightOverlay


def test_show_rect_updates_overlay_geometry(qapp, monkeypatch):
    del qapp
    geometry = QRect(10, 20, 300, 400)
    monkeypatch.setitem(
        HighlightOverlay._sync_geometry.__globals__,
        "_virtual_desktop_geometry",
        lambda: geometry,
    )

    overlay = HighlightOverlay()
    overlay.show_rect(15, 25, 35, 45)

    assert overlay.geometry() == geometry


def test_hide_rect_clears_current_rect(qapp):
    del qapp
    overlay = HighlightOverlay()
    overlay.set_rect(1, 2, 11, 22)

    overlay.hide_rect()

    assert overlay._local_rect() is None
