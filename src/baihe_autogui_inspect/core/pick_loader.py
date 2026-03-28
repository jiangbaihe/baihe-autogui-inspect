from __future__ import annotations

import ctypes
from typing import Any

from loguru import logger
from PySide6.QtCore import Signal
from pywinauto import Desktop

from baihe_autogui_inspect.core.inspector import make_node
from baihe_autogui_inspect.core.thread_base import WorkerThread

# System cursor helpers
_IDC_CROSS = 32515
_LEFT_MOUSE_BUTTON = 0x01
_RIGHT_MOUSE_BUTTON = 0x02
_KEY_PRESSED_MASK = 0x8000
_SPI_SETCURSORS = 0x0057
_user32 = ctypes.windll.user32

# Replace all common cursor types so the crosshair shows everywhere.
_CURSOR_IDS = [
    32512,  # OCR_NORMAL   - arrow
    32513,  # OCR_IBEAM    - text
    32516,  # OCR_UP       - up arrow
    32642,  # OCR_SIZENWSE
    32643,  # OCR_SIZENESW
    32644,  # OCR_SIZEWE
    32645,  # OCR_SIZENS
    32646,  # OCR_SIZEALL
    32648,  # OCR_NO
    32649,  # OCR_HAND
    32650,  # OCR_APPSTARTING
]


def set_global_crosshair() -> None:
    """Replace all common system cursors with a crosshair."""
    hcross = _user32.LoadCursorW(0, _IDC_CROSS)
    for cursor_id in _CURSOR_IDS:
        # SetSystemCursor takes ownership of the handle, so copy each time.
        hcopy = _user32.CopyImage(hcross, 2, 0, 0, 0x4)
        _user32.SetSystemCursor(hcopy, cursor_id)


def restore_system_cursors() -> None:
    """Restore all system cursors to their defaults."""
    _user32.SystemParametersInfoW(_SPI_SETCURSORS, 0, None, 0)


def _parent_of(element_info: Any):
    try:
        return element_info.parent
    except Exception:
        return None


def _build_ancestry(element_info) -> list:
    """Walk the parent chain from element up to root, return root-to-target."""
    chain = []
    current = element_info
    seen = set()
    while current is not None:
        current_id = id(current)
        if current_id in seen:
            break
        seen.add(current_id)
        chain.append(current)
        current = _parent_of(current)
    return list(reversed(chain))


def _node_ancestry(element_info, backend: str) -> list:
    return [make_node(item, backend) for item in _build_ancestry(element_info)]


class PickLoader(WorkerThread):
    """Resolve the UI element at a given screen coordinate in the background."""

    picked: Signal = Signal(object)  # ancestry: list[NodeInfo]
    _worker_name = "PickLoader"

    def __init__(self, x: int, y: int, backend: str, parent=None):
        super().__init__(parent)
        self._x = x
        self._y = y
        self._backend = backend

    def _pick_ancestry(self):
        desktop = Desktop(backend=self._backend)
        wrapper = desktop.from_point(self._x, self._y)
        logger.debug(f"Picked: {wrapper.element_info.name!r}")
        return _node_ancestry(wrapper.element_info, self._backend)

    def _run_impl(self) -> None:
        logger.debug(f"Picking element at ({self._x}, {self._y}) backend={self._backend!r}")
        ancestry = self._pick_ancestry()
        logger.debug(f"Ancestry depth: {len(ancestry)}")
        self.picked.emit(ancestry)  # type: ignore[attr-defined]


def _is_button_pressed(button: int) -> bool:
    return bool(_user32.GetAsyncKeyState(button) & _KEY_PRESSED_MASK)


def is_mouse_pressed() -> bool:
    """Return True if the left mouse button is currently held down."""
    return _is_button_pressed(_LEFT_MOUSE_BUTTON)


def is_right_mouse_pressed() -> bool:
    """Return True if the right mouse button is currently held down."""
    return _is_button_pressed(_RIGHT_MOUSE_BUTTON)


class _POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


def get_cursor_pos() -> tuple[int, int]:
    point = _POINT()
    _user32.GetCursorPos(ctypes.byref(point))
    return point.x, point.y
