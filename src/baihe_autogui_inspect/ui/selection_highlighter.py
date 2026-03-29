from __future__ import annotations

from PySide6.QtCore import QObject
from PySide6.QtGui import QColor

from baihe_autogui_inspect.core.inspector import NodeInfo, element_rectangle
from baihe_autogui_inspect.ui.overlay import SOFT_YELLOW, HighlightOverlay


class SelectionHighlighter(QObject):
    """Shows a yellow outline for the currently selected tree node."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._overlay: HighlightOverlay | None = None

    def sync(self, node: NodeInfo | None, *, allowed: bool) -> None:
        if not allowed or node is None:
            self.clear()
            return

        rect = element_rectangle(node)
        if rect is None:
            self.clear()
            return

        if self._overlay is None:
            self._overlay = HighlightOverlay(color=QColor(SOFT_YELLOW))
        self._overlay.show_rect(*rect)

    def clear(self) -> None:
        if self._overlay is None:
            return
        self._overlay.hide_rect()
