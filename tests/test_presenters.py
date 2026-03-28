from __future__ import annotations

from PySide6.QtWidgets import QAbstractItemView, QLabel, QStatusBar, QTableView

from baihe_autogui_inspect.core.inspector import make_node
from baihe_autogui_inspect.ui.node_details import NodeDetailsPresenter
from baihe_autogui_inspect.ui.timing_presenter import TimingPresenter
from tests.helpers import UiElementStub


def test_node_details_presenter_populates_table_and_status(qapp):
    table = QTableView()
    status_bar = QStatusBar()
    presenter = NodeDetailsPresenter(table, status_bar)
    node = make_node(UiElementStub("child"), "uia")
    initial_model = table.model()

    presenter.show_node(node)

    assert table.model() is initial_model
    assert table.model().rowCount() == len(node.props)
    assert status_bar.currentMessage() == node.label
    assert table.editTriggers() == QAbstractItemView.DoubleClicked


def test_node_details_presenter_clear_reuses_same_model(qapp):
    table = QTableView()
    status_bar = QStatusBar()
    presenter = NodeDetailsPresenter(table, status_bar)
    node = make_node(UiElementStub("child"), "uia")

    presenter.show_node(node)
    model = table.model()
    presenter.clear()

    assert table.model() is model
    assert model.rowCount() == 0


def test_timing_presenter_formats_failed_state(qapp):
    label = QLabel()
    presenter = TimingPresenter(label)

    presenter.show("Load failed", 1.23, "boom", failed=True)

    assert "Load failed: 1.23s | failed | boom" == label.text()
    assert "#b91c1c" in label.styleSheet()
