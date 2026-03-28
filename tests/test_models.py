"""Tests for Qt models; requires a QApplication instance."""

from __future__ import annotations

from unittest.mock import MagicMock

from PySide6.QtCore import QModelIndex, Qt

from baihe_autogui_inspect.core.inspector import NodeInfo, make_node
from baihe_autogui_inspect.ui.models.table_model import PropertyTableModel
from baihe_autogui_inspect.ui.models.tree_model import ControlTreeModel


def _node(
    label: str,
    children=None,
    has_children: bool | None = None,
    anchor_prepared: bool = False,
) -> NodeInfo:
    """Create a NodeInfo with a dummy element_info for testing."""
    element = MagicMock()
    element.children.return_value = []
    node = make_node(element, "uia")
    node.label = label
    node.props = []
    node.anchor_prepared = anchor_prepared
    if has_children is not None:
        node.has_children = has_children
    if children is not None:
        node.children = children
        node.children_loaded = True
        node.has_children = bool(children)
    return node


class TestPropertyTableModel:
    def test_empty(self, qapp):
        model = PropertyTableModel(None)
        assert model.rowCount() == 0
        assert model.columnCount() == 2

    def test_row_and_column_count(self, qapp):
        data = [["name", "Foo"], ["enabled", "True"]]
        model = PropertyTableModel(data)
        assert model.rowCount() == 2
        assert model.columnCount() == 2

    def test_data(self, qapp):
        data = [["name", "Foo"]]
        model = PropertyTableModel(data)
        assert model.data(model.index(0, 0), Qt.DisplayRole) == "name"
        assert model.data(model.index(0, 1), Qt.DisplayRole) == "Foo"

    def test_header(self, qapp):
        model = PropertyTableModel([["a", "b"]])
        assert model.headerData(0, Qt.Horizontal, Qt.DisplayRole) == "Property"
        assert model.headerData(1, Qt.Horizontal, Qt.DisplayRole) == "Value"

    def test_invalid_index_returns_none(self, qapp):
        model = PropertyTableModel([["a", "b"]])
        assert model.data(QModelIndex(), Qt.DisplayRole) is None

    def test_value_available_as_tooltip(self, qapp):
        model = PropertyTableModel([["name", "Foo"]])
        assert model.data(model.index(0, 1), Qt.ToolTipRole) == "Foo"

    def test_cells_are_not_editable(self, qapp):
        model = PropertyTableModel([["name", "Foo"]])
        assert not (model.flags(model.index(0, 0)) & Qt.ItemIsEditable)
        assert model.flags(model.index(0, 1)) & Qt.ItemIsEditable

    def test_edits_are_discarded(self, qapp):
        model = PropertyTableModel([["name", "Foo"]])

        assert model.setData(model.index(0, 1), "Bar", Qt.EditRole) is False
        assert model.data(model.index(0, 1), Qt.DisplayRole) == "Foo"

    def test_invalid_cell_has_no_flags(self, qapp):
        model = PropertyTableModel([["name", "Foo"]])
        assert model.flags(QModelIndex()) == Qt.NoItemFlags

    def test_set_rows_replaces_existing_data(self, qapp):
        model = PropertyTableModel([["name", "Foo"]])

        model.set_rows([["enabled", "True"], ["class_name", "Button"]])

        assert model.rowCount() == 2
        assert model.data(model.index(0, 0), Qt.DisplayRole) == "enabled"
        assert model.data(model.index(1, 1), Qt.DisplayRole) == "Button"


class TestControlTreeModel:
    def test_top_level_count(self, qapp):
        root = _node("root", children=[_node("win1"), _node("win2")])
        model = ControlTreeModel(root)
        assert model.rowCount() == 2

    def test_top_level_label(self, qapp):
        root = _node("root", children=[_node("Taskbar")])
        model = ControlTreeModel(root)
        assert model.data(model.index(0, 0), Qt.DisplayRole) == "Taskbar"

    def test_placeholder_child(self, qapp):
        root = _node("root", children=[_node("win1", has_children=True)])
        model = ControlTreeModel(root)
        top_index = model.index(0, 0)
        assert model.rowCount(top_index) == 1
        assert "Loading" in model.data(model.index(0, 0, top_index), Qt.DisplayRole)

    def test_sync_index_updates_children(self, qapp):
        root = _node("root", children=[_node("win1")])
        model = ControlTreeModel(root)
        top_index = model.index(0, 0)
        real_children = [_node("child_a"), _node("child_b")]
        node = model.node_for_index(top_index)
        assert node is not None
        node.children = real_children
        node.children_loaded = True
        node.anchor_prepared = True
        model.sync_index(top_index)
        assert model.rowCount(top_index) == 2
        assert model.data(model.index(0, 0, top_index), Qt.DisplayRole) == "child_a"

    def test_node_for_index(self, qapp):
        child = _node("MyWindow")
        root = _node("root", children=[child])
        model = ControlTreeModel(root)
        node = model.node_for_index(model.index(0, 0))
        assert node is not None
        assert node.label == "MyWindow"

    def test_items_not_editable(self, qapp):
        root = _node("root", children=[_node("w")])
        model = ControlTreeModel(root)
        assert not (model.flags(model.index(0, 0)) & Qt.ItemIsEditable)

    def test_preloaded_children_skip_placeholder(self, qapp):
        grandchild = _node("leaf")
        child = _node("parent", children=[grandchild])
        root = _node("root", children=[child])
        model = ControlTreeModel(root)
        top_index = model.index(0, 0)
        assert model.rowCount(top_index) == 1
        assert model.data(model.index(0, 0, top_index), Qt.DisplayRole) == "leaf"

    def test_anchor_ready_tracks_node_state(self, qapp):
        child = _node("parent", children=[_node("leaf")], anchor_prepared=True)
        root = _node("root", children=[child])
        model = ControlTreeModel(root)
        top_index = model.index(0, 0)
        assert model.is_anchor_ready(top_index)

    def test_loading_flag_round_trip(self, qapp):
        root = _node("root", children=[_node("win1")])
        model = ControlTreeModel(root)
        top_index = model.index(0, 0)
        assert not model.is_loading(top_index)
        model.set_loading(top_index, True)
        assert model.is_loading(top_index)
        model.set_loading(top_index, False)
        assert not model.is_loading(top_index)

    def test_leaf_node_has_no_placeholder(self, qapp):
        root = _node("root", children=[_node("leaf", has_children=False)])
        model = ControlTreeModel(root)
        top_index = model.index(0, 0)
        assert model.rowCount(top_index) == 0
