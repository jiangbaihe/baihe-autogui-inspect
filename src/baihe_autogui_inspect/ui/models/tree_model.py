from __future__ import annotations

from typing import Optional, cast

from loguru import logger
from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel

from baihe_autogui_inspect.core.inspector import NodeInfo

# Item data roles
NODE_ROLE = Qt.UserRole + 1  # stores NodeInfo
LOADING_ROLE = Qt.UserRole + 2  # bool: a background load is already in flight
ANCHOR_READY_ROLE = Qt.UserRole + 3  # bool: anchor prepared for this visible level
_PLACEHOLDER_TEXT = "Loading..."


def _placeholder_item() -> QStandardItem:
    item = QStandardItem(_PLACEHOLDER_TEXT)
    item.setEditable(False)
    return item


def _append_child_items(parent_item: QStandardItem, children: list[NodeInfo]) -> None:
    for child in children:
        parent_item.appendRow(_make_item(child))


def _sync_item_children(item: QStandardItem, node: NodeInfo) -> None:
    item.removeRows(0, item.rowCount())
    if node.children_loaded:
        _append_child_items(item, node.children)
        return
    if node.has_children:
        item.appendRow(_placeholder_item())


def _make_item(node: NodeInfo) -> QStandardItem:
    item = QStandardItem(node.label)
    item.setEditable(False)
    item.setData(node, NODE_ROLE)
    item.setData(False, LOADING_ROLE)
    item.setData(node.anchor_prepared, ANCHOR_READY_ROLE)
    _sync_item_children(item, node)
    return item


class ControlTreeModel(QStandardItemModel):
    """
    Anchor-based lazy tree model.

    The hidden root is prepared up front. Visible nodes can later become new
    anchors, at which point their direct children are loaded while deeper
    levels remain lazy.
    """

    def __init__(self, root: NodeInfo, parent=None):
        super().__init__(parent)
        logger.debug(
            f"Building ControlTreeModel root='{root.label}' "
            f"with {len(root.children)} top-level items"
        )
        for child in root.children:
            self.invisibleRootItem().appendRow(_make_item(child))
        logger.debug("ControlTreeModel ready")

    def _item(self, index: QModelIndex) -> QStandardItem | None:
        return self.itemFromIndex(index)

    @staticmethod
    def _item_data(item: QStandardItem | None, role: int, default=None):
        if item is None:
            return default
        return item.data(role)

    def sync_index(self, index: QModelIndex) -> None:
        """Sync one model item from its attached NodeInfo snapshot."""
        item = self._item(index)
        if item is None:
            return
        node = cast(Optional[NodeInfo], item.data(NODE_ROLE))
        if node is None:
            return
        _sync_item_children(item, node)
        item.setData(False, LOADING_ROLE)
        item.setData(node.anchor_prepared, ANCHOR_READY_ROLE)
        logger.debug(f"sync_index: {len(node.children)} children -> '{item.text()}'")

    def node_for_index(self, index: QModelIndex) -> NodeInfo | None:
        return cast(Optional[NodeInfo], self._item_data(self._item(index), NODE_ROLE))

    def is_loading(self, index: QModelIndex) -> bool:
        return bool(self._item_data(self._item(index), LOADING_ROLE, False))

    def is_anchor_ready(self, index: QModelIndex) -> bool:
        return bool(self._item_data(self._item(index), ANCHOR_READY_ROLE, True))

    def set_loading(self, index: QModelIndex, loading: bool) -> None:
        item = self._item(index)
        if item is not None:
            item.setData(loading, LOADING_ROLE)


