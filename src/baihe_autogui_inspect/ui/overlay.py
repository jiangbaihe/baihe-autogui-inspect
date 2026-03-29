from __future__ import annotations

from typing import Tuple

from baihe_autogui.core.overlay import HighlightSpec
from baihe_autogui.core.overlay import overlay as autogui_overlay
from PySide6.QtCore import QObject, Qt
from PySide6.QtGui import QColor

Rect = Tuple[int, int, int, int]

SOFT_RED = "#f87171"
SOFT_GREEN = "#4ade80"
SOFT_YELLOW = "#facc15"


def _normalize_color(color: QColor | Qt.GlobalColor | str) -> str:
    qcolor = QColor(color)
    if not qcolor.isValid():
        raise ValueError("overlay color must be a valid QColor-compatible value")
    return qcolor.name()


class HighlightOverlay(QObject):
    """Thin Qt wrapper around the shared baihe-autogui Win32 overlay backend."""

    def __init__(
        self,
        parent=None,
        *,
        color: QColor | Qt.GlobalColor | str = SOFT_RED,
        thickness: int = 3,
    ):
        super().__init__(parent)
        self._rect: Rect | None = None
        self._color = _normalize_color(color)
        self._thickness = thickness
        self._highlight_id: str | None = None

    def set_rect(self, left: int, top: int, right: int, bottom: int) -> None:
        self._rect = (left, top, right, bottom)

    def show_rect(self, left: int, top: int, right: int, bottom: int) -> None:
        self.set_rect(left, top, right, bottom)
        self._refresh_rect()

    def clear_rect(self) -> None:
        self._rect = None

    def hide_rect(self) -> None:
        self.clear_rect()
        if self._highlight_id is None:
            return
        autogui_overlay.remove(self._highlight_id)
        self._highlight_id = None

    def deleteLater(self) -> None:  # type: ignore[override]
        self.hide_rect()
        super().deleteLater()

    def _refresh_rect(self) -> None:
        if self._rect is None:
            return
        left, top, right, bottom = self._rect
        if self._highlight_id is not None:
            autogui_overlay.remove(self._highlight_id)
        self._highlight_id = autogui_overlay.add(
            HighlightSpec(
                kind="region",
                region=(left, top, right - left, bottom - top),
                color=self._color,
                thickness=self._thickness,
            ),
            timeout=None,
        )
