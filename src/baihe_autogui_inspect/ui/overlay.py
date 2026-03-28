from __future__ import annotations

from typing import Tuple

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QApplication, QWidget

Rect = Tuple[int, int, int, int]


def _virtual_desktop_geometry():
    app = QApplication.instance()
    if app is None:
        return None
    screen = app.primaryScreen()
    if screen is None:
        return None
    return screen.virtualGeometry()


class HighlightOverlay(QWidget):
    """Transparent fullscreen window that draws a rectangle around a UI element."""

    def __init__(self, parent=None, *, color: QColor | Qt.GlobalColor | str = "#ff0000"):
        super().__init__(
            parent,
            Qt.FramelessWindowHint  # type: ignore[arg-type]
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.WindowTransparentForInput,
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._rect: tuple[int, int, int, int] | None = None
        self._color = QColor(color)
        self._sync_geometry()

    def _sync_geometry(self) -> None:
        geometry = _virtual_desktop_geometry()
        if geometry is not None:
            self.setGeometry(geometry)

    def set_rect(self, left: int, top: int, right: int, bottom: int) -> None:
        self._rect = (left, top, right, bottom)
        self.update()

    def show_rect(self, left: int, top: int, right: int, bottom: int) -> None:
        self._sync_geometry()
        self.set_rect(left, top, right, bottom)
        self.show()

    def clear_rect(self) -> None:
        self._rect = None
        self.update()

    def hide_rect(self) -> None:
        self.clear_rect()
        self.hide()

    def _local_rect(self) -> Rect | None:
        if self._rect is None:
            return None
        left, top, right, bottom = self._rect
        geometry = self.geometry()
        return (
            left - geometry.x(),
            top - geometry.y(),
            right - left,
            bottom - top,
        )

    def paintEvent(self, event) -> None:
        del event
        rect = self._local_rect()
        if rect is None:
            return
        painter = QPainter(self)
        pen = QPen(self._color, 3)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(*rect)
