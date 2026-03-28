from __future__ import annotations

import time
from functools import partial

from loguru import logger
from PySide6.QtCore import QModelIndex, QObject, QPersistentModelIndex, QSignalBlocker, Signal
from PySide6.QtGui import QStandardItem
from PySide6.QtWidgets import QTreeView

from baihe_autogui_inspect.core.child_loader import ChildLoader
from baihe_autogui_inspect.core.inspector import NodeInfo
from baihe_autogui_inspect.core.worker import TreeLoader
from baihe_autogui_inspect.ui.models.tree_model import ControlTreeModel
from baihe_autogui_inspect.ui.qt_helpers import dispose_worker


class TreeController(QObject):
    """Coordinates tree loading, expansion, and current-node tracking."""

    loading_state_changed = Signal(bool)
    status_message = Signal(str)
    timing_status = Signal(str, float, str, bool)
    current_node_changed = Signal(object)

    def __init__(self, tree_view: QTreeView, parent=None):
        super().__init__(parent)
        self._tree_view = tree_view
        self._loader: TreeLoader | None = None
        self._tree_model: ControlTreeModel | None = None
        self._child_loaders: list[ChildLoader] = []
        self._load_generation = 0
        self._tree_load_started_at: float | None = None
        self._tree_view.expanded.connect(self._on_node_expanded)

    def has_model(self) -> bool:
        return self._tree_model is not None

    def current_index(self) -> QModelIndex:
        return self._tree_view.currentIndex()

    def current_node(self) -> NodeInfo | None:
        if self._tree_model is None:
            return None
        return self._tree_model.node_for_index(self._tree_view.currentIndex())

    def start_loading(
        self,
        backend: str,
        status_message: str,
        ancestry: list[NodeInfo] | None = None,
    ) -> None:
        self._load_generation += 1
        current_generation = self._load_generation

        self._stop_tree_loader()
        self._stop_child_loaders()

        logger.info(f"Starting tree load with backend='{backend}'")
        self._tree_load_started_at = time.perf_counter()
        self._set_loading_state(True)
        self._show_status(status_message)
        self._tree_model = None
        self._reset_view_model()
        self._emit_current_node_changed(None)

        self._loader = TreeLoader(backend, ancestry=ancestry, parent=self)
        self._connect_tree_loader(self._loader, current_generation)
        self._loader.start()

    def stop(self) -> None:
        self._stop_tree_loader()
        self._stop_child_loaders()

    def _on_tree_loaded(
        self,
        root: NodeInfo,
        path_signatures: list[tuple[str, ...]],
        generation: int,
    ) -> None:
        if generation != self._load_generation:
            logger.debug("Ignoring stale top-level tree result")
            return

        elapsed = self._elapsed_seconds(self._tree_load_started_at)
        logger.info(f"Tree loaded: {len(root.children)} top-level nodes")
        self._set_tree_model(root)
        if path_signatures:
            self._show_timing(
                "Locate picked element",
                elapsed,
                f"{len(root.children)} top-level windows",
                False,
            )
            self._select_path_by_signatures(path_signatures)
            self._show_status(
                f"Located picked element after loading {len(root.children)} top-level windows"
            )
        else:
            self._show_timing(
                "Load tree",
                elapsed,
                f"{len(root.children)} top-level windows",
                False,
            )
            self._show_status(f"Loaded {len(root.children)} top-level windows")
        self._finish_top_level_load()

    def _on_load_error(self, message: str, generation: int) -> None:
        if generation != self._load_generation:
            logger.debug("Ignoring stale tree load error")
            return

        logger.error(f"Tree load failed: {message}")
        elapsed = self._elapsed_seconds(self._tree_load_started_at)
        self._show_timing("Load failed", elapsed, message, True)
        self._show_status(message)
        self._finish_top_level_load()

    def _on_node_expanded(self, index: QModelIndex) -> None:
        self._load_node_children(index)

    def _load_node_children(self, index: QModelIndex) -> bool:
        if self._tree_model is None:
            return False
        if self._tree_model.is_anchor_ready(index) or self._tree_model.is_loading(index):
            return False

        node = self._tree_model.node_for_index(index)
        if node is None:
            return False

        logger.debug(f"Expanding '{node.label}' -> preparing anchor context")
        persistent = QPersistentModelIndex(index)
        model = self._tree_model
        generation = self._load_generation
        started_at = time.perf_counter()
        self._tree_model.set_loading(index, True)

        loader = ChildLoader(node, parent=self)
        self._child_loaders.append(loader)
        self._connect_child_loader(
            loader,
            persistent_index=persistent,
            model=model,
            load_generation=generation,
            started_at=started_at,
            node_label=node.label,
        )
        loader.start()
        return True

    def _connect_tree_loader(self, loader: TreeLoader, generation: int) -> None:
        loader.loaded.connect(partial(self._handle_tree_loaded, generation))  # type: ignore[attr-defined]
        loader.error.connect(partial(self._handle_tree_load_error, generation))  # type: ignore[attr-defined]

    def _handle_tree_loaded(
        self,
        generation: int,
        root: NodeInfo,
        path_signatures: list[tuple[str, ...]],
    ) -> None:
        self._on_tree_loaded(root, path_signatures, generation)

    def _handle_tree_load_error(self, generation: int, message: str) -> None:
        self._on_load_error(message, generation)

    def _connect_child_loader(
        self,
        loader: ChildLoader,
        *,
        persistent_index: QPersistentModelIndex,
        model: ControlTreeModel,
        load_generation: int,
        started_at: float,
        node_label: str,
    ) -> None:
        loader.loaded.connect(  # type: ignore[attr-defined]
            partial(
                self._handle_child_loader_done,
                loader,
                persistent_index,
                model,
                load_generation,
                started_at,
                node_label,
            )
        )
        loader.error.connect(  # type: ignore[attr-defined]
            partial(
                self._handle_child_loader_error,
                loader,
                persistent_index,
                model,
                load_generation,
            )
        )

    def _handle_child_loader_done(
        self,
        loader: ChildLoader,
        persistent_index: QPersistentModelIndex,
        model: ControlTreeModel,
        load_generation: int,
        started_at: float,
        node_label: str,
        children: list[NodeInfo],
    ) -> None:
        self._on_child_loader_done(
            loader,
            persistent_index,
            model,
            load_generation,
            started_at,
            node_label,
            children,
        )

    def _handle_child_loader_error(
        self,
        loader: ChildLoader,
        persistent_index: QPersistentModelIndex,
        model: ControlTreeModel,
        load_generation: int,
        message: str,
    ) -> None:
        self._on_child_loader_error(
            loader,
            persistent_index,
            model,
            load_generation,
            message,
        )

    def _remove_child_loader(self, loader: ChildLoader) -> None:
        if loader in self._child_loaders:
            self._child_loaders.remove(loader)

    @staticmethod
    def _persistent_model_index(
        model: ControlTreeModel,
        persistent_index: QPersistentModelIndex,
    ) -> QModelIndex:
        return model.index(
            persistent_index.row(),
            persistent_index.column(),
            persistent_index.parent(),
        )

    def _on_child_loader_done(
        self,
        loader: ChildLoader,
        persistent_index: QPersistentModelIndex,
        model: ControlTreeModel,
        load_generation: int,
        started_at: float,
        node_label: str,
        children: list[NodeInfo],
    ) -> None:
        self._remove_child_loader(loader)
        if load_generation != self._load_generation or self._tree_model is not model:
            logger.debug("Ignoring stale child loader result")
            return
        if not persistent_index.isValid():
            return

        model_index = self._persistent_model_index(model, persistent_index)
        if not model_index.isValid():
            return

        model.sync_index(model_index)
        elapsed = self._elapsed_seconds(started_at)
        self._show_timing(
            "Expand node",
            elapsed,
            f"{node_label} ({len(children)} children)",
            False,
        )
        self._show_status(f"Expanded {node_label} with {len(children)} children")

    def _on_child_loader_error(
        self,
        loader: ChildLoader,
        persistent_index: QPersistentModelIndex,
        model: ControlTreeModel,
        load_generation: int,
        message: str,
    ) -> None:
        self._remove_child_loader(loader)
        if (
            load_generation == self._load_generation
            and self._tree_model is model
            and persistent_index.isValid()
        ):
            model_index = self._persistent_model_index(model, persistent_index)
            if model_index.isValid():
                model.set_loading(model_index, False)
        logger.error(f"ChildLoader: {message}")

    def _select_path_by_signatures(self, path_signatures: list[tuple[str, ...]]) -> None:
        if self._tree_model is None or not path_signatures:
            self._show_element_not_found()
            return

        parent_item = self._tree_model.invisibleRootItem()
        final_index = QModelIndex()

        self._tree_view.setUpdatesEnabled(False)
        try:
            for signature in path_signatures:
                found = self._find_child_item(parent_item, signature)
                if found is None:
                    self._show_element_not_found()
                    return

                final_index = found.index()
                self._tree_view.expand(final_index)
                parent_item = found
        finally:
            self._tree_view.setUpdatesEnabled(True)

        if final_index.isValid():
            self._set_current_index_silently(final_index)
            self._tree_view.scrollTo(final_index)
            self._emit_current_node()
        else:
            self._show_element_not_found()
            self._emit_current_node_changed(None)

    def _find_child_item(
        self,
        parent_item: QStandardItem,
        signature: tuple[str, ...],
    ) -> QStandardItem | None:
        if self._tree_model is None:
            return None
        for row in range(parent_item.rowCount()):
            child = parent_item.child(row)
            if child is None:
                continue
            node = self._tree_model.node_for_index(child.index())
            if node is not None and node.signature == signature:
                return child
        return None

    def _set_tree_model(self, root: NodeInfo) -> None:
        self._tree_model = ControlTreeModel(root, parent=self)
        self._tree_view.setModel(self._tree_model)
        selection_model = self._tree_view.selectionModel()
        if selection_model is not None:
            selection_model.currentChanged.connect(self._on_current_index_changed)

    def _reset_view_model(self) -> None:
        selection_model = self._tree_view.selectionModel()
        blocker = QSignalBlocker(selection_model) if selection_model is not None else None
        self._tree_view.setModel(None)  # type: ignore[arg-type]
        del blocker

    def _set_current_index_silently(self, index: QModelIndex) -> None:
        selection_model = self._tree_view.selectionModel()
        blocker = QSignalBlocker(selection_model) if selection_model is not None else None
        self._tree_view.setCurrentIndex(index)
        del blocker

    def _emit_current_node(self) -> None:
        self._emit_current_node_changed(self.current_node())

    def _on_current_index_changed(self, current: QModelIndex, previous: QModelIndex) -> None:
        del previous
        node = None
        if self._tree_model is not None and current.isValid():
            node = self._tree_model.node_for_index(current)
        self._emit_current_node_changed(node)

    def _finish_top_level_load(self) -> None:
        self._loader = None
        self._tree_load_started_at = None
        self._set_loading_state(False)

    def _show_element_not_found(self) -> None:
        self._show_status("Element not found in tree")

    def _set_loading_state(self, is_loading: bool) -> None:
        self.loading_state_changed.emit(is_loading)  # type: ignore[attr-defined]

    def _show_status(self, message: str) -> None:
        self.status_message.emit(message)  # type: ignore[attr-defined]

    def _show_timing(self, action: str, elapsed: float, detail: str, failed: bool) -> None:
        self.timing_status.emit(action, elapsed, detail, failed)  # type: ignore[attr-defined]

    def _emit_current_node_changed(self, node: NodeInfo | None) -> None:
        self.current_node_changed.emit(node)  # type: ignore[attr-defined]

    def _stop_tree_loader(self) -> None:
        self._loader = dispose_worker(self._loader)

    def _stop_child_loaders(self) -> None:
        loaders = self._child_loaders
        self._child_loaders = []
        for loader in loaders:
            dispose_worker(loader)

    @staticmethod
    def _elapsed_seconds(started_at: float | None) -> float:
        if started_at is None:
            return 0.0
        return max(0.0, time.perf_counter() - started_at)
