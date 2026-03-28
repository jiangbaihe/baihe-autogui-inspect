from __future__ import annotations

from PySide6.QtWidgets import QAbstractItemView, QStatusBar, QTableView

from baihe_autogui_inspect.core.inspector import NodeInfo
from baihe_autogui_inspect.ui.models.table_model import PropertyTableModel


class NodeDetailsPresenter:
    """Owns how the selected node is rendered in the property panel."""

    def __init__(self, table_view: QTableView, status_bar: QStatusBar):
        self._table_view = table_view
        self._status_bar = status_bar
        self._model = PropertyTableModel([], parent=self._table_view)
        self._table_view.setModel(self._model)
        self._table_view.setEditTriggers(QAbstractItemView.DoubleClicked)

    def show_node(self, node: NodeInfo) -> None:
        self._status_bar.showMessage(node.label)
        self._model.set_rows(node.props)
        self._table_view.resizeColumnToContents(0)

    def clear(self) -> None:
        self._model.set_rows([])


