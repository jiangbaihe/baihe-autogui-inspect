from __future__ import annotations

from typing import cast

from loguru import logger
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


class PropertyTableModel(QAbstractTableModel):
    _HEADERS = ["Property", "Value"]
    _EDITABLE_COLUMNS = frozenset({1})

    def __init__(self, data: list[list[str]] | None, parent=None):
        super().__init__(parent)
        self._data = data or []
        logger.debug(f"PropertyTableModel created with {len(self._data)} rows")

    def set_rows(self, data: list[list[str]] | None) -> None:
        self.beginResetModel()
        self._data = data or []
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._data)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._HEADERS)

    def _has_cell(self, index: QModelIndex) -> bool:
        return (
            index.isValid()
            and index.row() < len(self._data)
            and index.column() < len(self._HEADERS)
        )

    def _cell_value(self, index: QModelIndex) -> str:
        return self._data[index.row()][index.column()]

    def _is_editable_cell(self, index: QModelIndex) -> bool:
        return self._has_cell(index) and index.column() in self._EDITABLE_COLUMNS

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not self._has_cell(index):
            return None
        if role in (Qt.DisplayRole, Qt.EditRole, Qt.ToolTipRole):
            return self._cell_value(index)
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not self._has_cell(index):
            return cast(Qt.ItemFlags, Qt.NoItemFlags)
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if self._is_editable_cell(index):
            flags |= Qt.ItemIsEditable
        return cast(Qt.ItemFlags, flags)

    def setData(self, index: QModelIndex, value, role: int = Qt.EditRole) -> bool:
        if role != Qt.EditRole or not self._is_editable_cell(index):
            return False
        logger.debug(
            "Discarding property-table edit at row={} column={} value={!r}",
            index.row(),
            index.column(),
            value,
        )
        return False

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._HEADERS[section]
        return super().headerData(section, orientation, role)
