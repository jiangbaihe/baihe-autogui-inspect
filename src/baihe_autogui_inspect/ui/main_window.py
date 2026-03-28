from __future__ import annotations

from loguru import logger
from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QLabel,
    QMainWindow,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTableView,
    QToolBar,
    QTreeView,
    QVBoxLayout,
    QWidget,
)
from pywinauto import backend as pw_backend

from baihe_autogui_inspect.core.inspector import NodeInfo
from baihe_autogui_inspect.core.pick_loader import PickLoader
from baihe_autogui_inspect.core.playground import PlaygroundRunner, build_locator_code
from baihe_autogui_inspect.ui.flash_highlighter import FlashHighlighter
from baihe_autogui_inspect.ui.node_details import NodeDetailsPresenter
from baihe_autogui_inspect.ui.pick_mode import PickModeController
from baihe_autogui_inspect.ui.playground_panel import PlaygroundPanel
from baihe_autogui_inspect.ui.qt_helpers import dispose_worker, show_window_foreground
from baihe_autogui_inspect.ui.selection_highlighter import SelectionHighlighter
from baihe_autogui_inspect.ui.timing_presenter import TimingPresenter
from baihe_autogui_inspect.ui.tree_controller import TreeController


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Baihe AutoGUI Inspect")
        self.resize(1200, 800)

        self._pick_loader: PickLoader | None = None
        self._playground_runner: PlaygroundRunner | None = None

        self._setup_ui()
        self._tree_controller = TreeController(self.treeView, parent=self)
        self._pick_mode = PickModeController(self, self.pickButton, self.status_bar, parent=self)
        self._selection_highlighter = SelectionHighlighter(parent=self)
        self._flash_highlighter = FlashHighlighter(parent=self)
        self._connect_signals()
        self._start_loading(self.backendCombo.currentText())

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        self.toolBar = QToolBar("Controls")
        self.toolBar.setMovable(False)
        self.toolBar.layout().setSpacing(6)
        self.toolBar.layout().setContentsMargins(6, 4, 6, 4)
        self.addToolBar(self.toolBar)

        self.backendLabel = QLabel("Backend:")
        self.backendCombo = QComboBox()
        self.backendCombo.setMaxVisibleItems(5)
        for name in pw_backend.registry.backends:
            self.backendCombo.addItem(name)
        self.backendCombo.setCurrentText("uia")

        self.refreshButton = QPushButton("Refresh")
        self.pickButton = QPushButton("Pick Element")
        self.pickButton.setCheckable(True)
        self.pickButton.setToolTip(
            "Click to enter pick mode, then click any UI element to locate it in the tree"
        )

        self.toolBar.addWidget(self.backendLabel)
        self.toolBar.addWidget(self.backendCombo)
        self.toolBar.addWidget(self.refreshButton)
        self.toolBar.addWidget(self.pickButton)

        self.treeView = QTreeView()
        self.treeView.setHeaderHidden(True)
        self.treeView.setAnimated(True)
        self.treeView.setAlternatingRowColors(True)

        self.tableView = QTableView()
        self.tableView.setWordWrap(True)
        self.tableView.setAlternatingRowColors(True)
        self.tableView.setSelectionBehavior(QTableView.SelectRows)
        self.tableView.horizontalHeader().setStretchLastSection(True)
        self.tableView.verticalHeader().setVisible(False)

        self.playgroundPanel = PlaygroundPanel()

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.treeView)
        self.splitter.addWidget(self.tableView)
        self.splitter.addWidget(self.playgroundPanel)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setStretchFactor(2, 1)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.addWidget(self.splitter)

        self.central_widget = QWidget()
        self.central_widget.setLayout(self.verticalLayout)
        self.setCentralWidget(self.central_widget)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.timingLabel = QLabel("Last action: -")
        self.status_bar.addPermanentWidget(self.timingLabel)
        self._node_details = NodeDetailsPresenter(self.tableView, self.status_bar)
        self._timing = TimingPresenter(self.timingLabel)

    def _connect_signals(self) -> None:
        app = QApplication.instance()
        if app is not None:
            app.applicationStateChanged.connect(self._on_application_state_changed)
        self.backendCombo.currentTextChanged.connect(self._start_loading)
        self.refreshButton.clicked.connect(self._reload_current_backend)
        self.pickButton.toggled.connect(self._on_pick_toggled)
        self._pick_mode.pick_requested.connect(self._start_pick)  # type: ignore[attr-defined]
        self.playgroundPanel.run_requested.connect(self._run_playground_code)  # type: ignore[attr-defined]

        self._tree_controller.loading_state_changed.connect(self._set_loading_state)  # type: ignore[attr-defined]
        self._tree_controller.status_message.connect(self._show_status)  # type: ignore[attr-defined]
        self._tree_controller.timing_status.connect(self._apply_timing_status)  # type: ignore[attr-defined]
        self._tree_controller.current_node_changed.connect(self._on_current_node_changed)  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # Tree loading
    # ------------------------------------------------------------------

    def _start_loading(self, backend: str) -> None:
        self._begin_tree_load(backend, "Loading...")

    def _reload_current_backend(self) -> None:
        self._start_loading(self.backendCombo.currentText())

    def _begin_tree_load(
        self,
        backend: str,
        status_message: str,
        ancestry: list[NodeInfo] | None = None,
    ) -> None:
        self._stop_pick_loader()
        self._stop_playground_runner()
        self._cancel_pick_mode()
        self._clear_current_node_ui()
        self._tree_controller.start_loading(backend, status_message, ancestry=ancestry)

    # ------------------------------------------------------------------
    # Pick mode
    # ------------------------------------------------------------------

    def _on_pick_toggled(self, checked: bool) -> None:
        if checked:
            self._enter_pick_mode()
            return
        self._cancel_pick_mode()

    def _enter_pick_mode(self) -> None:
        self._clear_selection_highlight()
        self._pick_mode.start(self.backendCombo.currentText())

    def _cancel_pick_mode(self) -> None:
        if not self._pick_mode.cancel():
            return
        self._sync_selection_highlight()

    def _start_pick(self, x: int, y: int) -> None:
        self._stop_pick_loader()

        backend = self.backendCombo.currentText()
        logger.debug(f"Starting pick at ({x}, {y}) backend={backend!r}")
        self._show_status(f"Picking element at ({x}, {y})...")
        self._pick_loader = PickLoader(x, y, backend, parent=self)
        self._pick_loader.picked.connect(self._on_pick_finished)  # type: ignore[attr-defined]
        self._pick_loader.error.connect(self._on_pick_error)  # type: ignore[attr-defined]
        self._pick_loader.start()

    def _on_pick_finished(self, ancestry: list[NodeInfo]) -> None:
        self._pick_loader = None
        show_window_foreground(self)
        if len(ancestry) <= 1:
            self._show_status("Element not found in tree")
            return

        self._begin_tree_load(
            self.backendCombo.currentText(),
            "Refreshing tree for picked element...",
            ancestry=ancestry,
        )

    def _on_pick_error(self, message: str) -> None:
        self._pick_loader = None
        show_window_foreground(self)
        logger.warning(f"Pick error: {message}")
        self._show_status(f"Pick failed: {message}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _set_loading_state(self, is_loading: bool) -> None:
        enabled = not is_loading
        self.backendCombo.setEnabled(enabled)
        self.refreshButton.setEnabled(enabled)
        self.pickButton.setEnabled(enabled and self._tree_controller.has_model())
        self.treeView.setEnabled(enabled)
        self.tableView.setEnabled(enabled)
        self.playgroundPanel.setEnabled(enabled)

    def _stop_pick_loader(self) -> None:
        self._pick_loader = dispose_worker(self._pick_loader)

    def _clear_property_table(self) -> None:
        self._node_details.clear()

    def _clear_playground(self) -> None:
        self.playgroundPanel.clear()

    def _clear_current_node_ui(self) -> None:
        self._clear_property_table()
        self._clear_playground()
        self._clear_selection_highlight()
        self._flash_highlighter.clear()

    def _show_status(self, message: str) -> None:
        self.status_bar.showMessage(message)

    def _selection_highlight_allowed(self) -> bool:
        if self._pick_mode.is_active():
            return False
        if not self.isVisible() or self.isMinimized():
            return False
        app = QApplication.instance()
        if app is None:
            return True
        return bool(app.applicationState() == Qt.ApplicationState.ApplicationActive)

    def _on_current_node_changed(self, node: NodeInfo | None) -> None:
        if node is None:
            self._clear_current_node_ui()
            return
        logger.debug(f"Node clicked: {node.label!r}")
        self._node_details.show_node(node)
        self._show_playground_code(node)
        self._refresh_selection_highlight()

    def _show_playground_code(self, node: NodeInfo) -> None:
        try:
            code = build_locator_code(node)
        except Exception as exc:
            logger.warning(f"Playground code generation failed: {exc}")
            self.playgroundPanel.clear()
            self.playgroundPanel.set_status(f"Could not generate locator code: {exc}")
            return
        self.playgroundPanel.set_code(code)

    def _refresh_selection_highlight(self) -> None:
        self._selection_highlighter.sync(
            self._tree_controller.current_node(),
            allowed=self._selection_highlight_allowed(),
        )

    def _clear_selection_highlight(self) -> None:
        self._selection_highlighter.clear()

    def _sync_selection_highlight(self) -> None:
        if self._selection_highlight_allowed():
            self._refresh_selection_highlight()
            return
        self._clear_selection_highlight()

    def _apply_timing_status(
        self,
        action: str,
        elapsed: float,
        detail: str,
        failed: bool,
    ) -> None:
        self._timing.show(action, elapsed, detail, failed=failed)

    def _run_playground_code(self, code: str) -> None:
        source = code.strip()
        if not source:
            self.playgroundPanel.set_status("There is no locator code to run.")
            return

        self._stop_playground_runner()
        self.playgroundPanel.set_running(True)
        self.playgroundPanel.set_status("Running locator code...")
        self._show_status("Running generated locator code...")
        self._playground_runner = PlaygroundRunner(source, parent=self)
        self._playground_runner.resolved.connect(self._on_playground_resolved)  # type: ignore[attr-defined]
        self._playground_runner.error.connect(self._on_playground_error)  # type: ignore[attr-defined]
        self._playground_runner.start()

    def _on_playground_resolved(self, target) -> None:
        self._playground_runner = None
        self.playgroundPanel.set_running(False)
        flashed = self._flash_highlighter.flash(getattr(target, "element_info", target))
        if flashed:
            self._clear_selection_highlight()
            self.hide()
            message = "Locator code matched a control and flashed it on screen."
            QTimer.singleShot(
                self._flash_highlighter.duration_ms(), self._restore_window_foreground
            )
        else:
            message = "Locator code matched a control, but no visible rectangle was available."
        self.playgroundPanel.set_status(message)
        self._show_status(message)

    def _on_playground_error(self, message: str) -> None:
        self._playground_runner = None
        self.playgroundPanel.set_running(False)
        self.playgroundPanel.set_status(f"Locator code failed: {message}")
        self._show_status(f"Locator code failed: {message}")

    def _on_application_state_changed(self, state: Qt.ApplicationState) -> None:
        if state == Qt.ApplicationState.ApplicationActive:
            self._sync_selection_highlight()
            return
        self._clear_selection_highlight()

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() in (QEvent.Type.ActivationChange, QEvent.Type.WindowStateChange):
            self._sync_selection_highlight()

    def hideEvent(self, event) -> None:
        self._clear_selection_highlight()
        super().hideEvent(event)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._sync_selection_highlight()

    def closeEvent(self, event) -> None:
        self._pick_mode.shutdown()
        self._clear_selection_highlight()
        self._flash_highlighter.clear()
        self._stop_pick_loader()
        self._stop_playground_runner()
        self._tree_controller.stop()
        super().closeEvent(event)

    def _stop_playground_runner(self) -> None:
        self._playground_runner = dispose_worker(self._playground_runner)

    def _restore_window_foreground(self) -> None:
        show_window_foreground(self)
