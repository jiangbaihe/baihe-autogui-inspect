from __future__ import annotations

from loguru import logger
from PySide6.QtCore import Signal

from baihe_autogui_inspect.core.inspector import NodeInfo, collect_top_level, prepare_path
from baihe_autogui_inspect.core.thread_base import WorkerThread


class TreeLoader(WorkerThread):
    """Background thread: collects root + top-level children, emits NodeInfo.

    Qt rule: never create QStandardItem/QAbstractItemModel inside QThread.run().
    We emit plain Python NodeInfo; the main thread builds Qt models from them.
    """

    loaded = Signal(object, object)  # (root: NodeInfo, path_signatures: list[tuple[str, ...]])
    _worker_name = "TreeLoader"

    def __init__(self, backend: str, ancestry: list[NodeInfo] | None = None, parent=None):
        super().__init__(parent)
        self.backend = backend
        self._ancestry = ancestry or []

    def _collect_tree(self) -> tuple[NodeInfo, list[tuple[str, ...]]]:
        root = collect_top_level(self.backend)
        return root, prepare_path(root, self._ancestry)

    def _run_impl(self) -> None:
        logger.info(f"TreeLoader started for backend='{self.backend}'")
        root, path_signatures = self._collect_tree()
        logger.info(f"TreeLoader finished: {len(root.children)} top-level nodes")
        self.loaded.emit(root, path_signatures)  # type: ignore[attr-defined]


