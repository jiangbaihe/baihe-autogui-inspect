from __future__ import annotations

from loguru import logger
from PySide6.QtCore import Signal

from baihe_autogui_inspect.core.inspector import NodeInfo, prepare_anchor
from baihe_autogui_inspect.core.thread_base import WorkerThread


class ChildLoader(WorkerThread):
    """Prepare one anchor node in background, then call back."""

    loaded = Signal(object)  # children: list[NodeInfo]
    _worker_name = "ChildLoader"

    def __init__(self, node: NodeInfo, parent=None):
        super().__init__(parent)
        self._node = node

    def _prepare_children(self) -> list[NodeInfo]:
        return prepare_anchor(self._node)

    def _run_impl(self) -> None:
        logger.debug(f"ChildLoader: preparing anchor '{self._node.label}'")
        children = self._prepare_children()
        self.loaded.emit(children)  # type: ignore[attr-defined]
