from __future__ import annotations

from PySide6.QtWidgets import QTreeView

from baihe_autogui_inspect.core.inspector import make_node
from baihe_autogui_inspect.ui.tree_controller import TreeController
from tests.helpers import UiElementStub


def test_current_node_tracks_tree_selection(qapp):
    tree_view = QTreeView()
    controller = TreeController(tree_view)
    root = make_node(UiElementStub("root"), "uia")
    child = make_node(UiElementStub("child"), "uia")
    root.children = [child]
    root.children_loaded = True

    controller._set_tree_model(root)
    tree_view.setCurrentIndex(controller._tree_model.index(0, 0))

    assert controller.current_node() is not None
    assert controller.current_node().label == child.label


