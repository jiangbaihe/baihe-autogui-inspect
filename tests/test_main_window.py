from __future__ import annotations

from baihe_autogui_inspect.ui.main_window import MainWindow


def test_main_window_initializes_without_attribute_errors(qapp, monkeypatch):
    monkeypatch.setattr(MainWindow, "_start_loading", lambda self, backend: None)

    window = MainWindow()

    assert window.tableView.model() is not None
    assert window.splitter.count() == 3


def test_selection_highlight_allowed_when_window_active():
    window = MainWindow.__new__(MainWindow)
    window._pick_mode = type("PickModeStub", (), {"is_active": lambda self: False})()
    window.isVisible = lambda: True
    window.isMinimized = lambda: False

    original_qapplication = MainWindow._selection_highlight_allowed.__globals__["QApplication"]
    original_qt = MainWindow._selection_highlight_allowed.__globals__["Qt"]

    class AppStub:
        @staticmethod
        def instance():
            return AppStub()

        def applicationState(self):
            return original_qt.ApplicationState.ApplicationActive

    MainWindow._selection_highlight_allowed.__globals__["QApplication"] = AppStub
    try:
        assert window._selection_highlight_allowed() is True
    finally:
        MainWindow._selection_highlight_allowed.__globals__["QApplication"] = original_qapplication


def test_selection_highlight_disallowed_when_app_inactive():
    window = MainWindow.__new__(MainWindow)
    window._pick_mode = type("PickModeStub", (), {"is_active": lambda self: False})()
    window.isVisible = lambda: True
    window.isMinimized = lambda: False

    original_qapplication = MainWindow._selection_highlight_allowed.__globals__["QApplication"]
    original_qt = MainWindow._selection_highlight_allowed.__globals__["Qt"]

    class AppStub:
        @staticmethod
        def instance():
            return AppStub()

        def applicationState(self):
            return original_qt.ApplicationState.ApplicationInactive

    MainWindow._selection_highlight_allowed.__globals__["QApplication"] = AppStub
    try:
        assert window._selection_highlight_allowed() is False
    finally:
        MainWindow._selection_highlight_allowed.__globals__["QApplication"] = original_qapplication


def test_selection_highlight_disallowed_during_pick_mode():
    window = MainWindow.__new__(MainWindow)
    window._pick_mode = type("PickModeStub", (), {"is_active": lambda self: True})()
    window.isVisible = lambda: True
    window.isMinimized = lambda: False

    assert window._selection_highlight_allowed() is False


def test_enter_pick_mode_delegates_to_controller():
    window = MainWindow.__new__(MainWindow)
    calls: list[str] = []
    window._clear_selection_highlight = lambda: calls.append("clear")
    window.backendCombo = type("BackendComboStub", (), {"currentText": lambda self: "uia"})()
    window._pick_mode = type(
        "PickModeStub",
        (),
        {"start": lambda self, backend: calls.append(f"start:{backend}")},
    )()

    window._enter_pick_mode()

    assert calls == ["clear", "start:uia"]


def test_cancel_pick_mode_refreshes_highlight_when_controller_cancels():
    window = MainWindow.__new__(MainWindow)
    calls: list[str] = []
    window._pick_mode = type("PickModeStub", (), {"cancel": lambda self: True})()
    window._sync_selection_highlight = lambda: calls.append("sync")

    window._cancel_pick_mode()

    assert calls == ["sync"]


def test_set_loading_state_clears_highlight_while_loading():
    window = MainWindow.__new__(MainWindow)
    calls: list[str] = []
    window.backendCombo = type(
        "WidgetStub", (), {"setEnabled": lambda self, value: calls.append(("backend", value))}
    )()
    window.refreshButton = type(
        "WidgetStub", (), {"setEnabled": lambda self, value: calls.append(("refresh", value))}
    )()
    window.pickButton = type(
        "WidgetStub", (), {"setEnabled": lambda self, value: calls.append(("pick", value))}
    )()
    window.treeView = type(
        "WidgetStub", (), {"setEnabled": lambda self, value: calls.append(("tree", value))}
    )()
    window.tableView = type(
        "WidgetStub", (), {"setEnabled": lambda self, value: calls.append(("table", value))}
    )()
    window.playgroundPanel = type(
        "WidgetStub",
        (),
        {"setEnabled": lambda self, value: calls.append(("playground", value))},
    )()
    window._tree_controller = type("TreeControllerStub", (), {"has_model": lambda self: True})()
    window._clear_selection_highlight = lambda: calls.append("clear")
    window._refresh_selection_highlight = lambda: calls.append("refresh")

    window._set_loading_state(True)

    assert calls == [
        ("backend", False),
        ("refresh", False),
        ("pick", False),
        ("tree", False),
        ("table", False),
        ("playground", False),
    ]


def test_sync_selection_highlight_refreshes_when_allowed():
    window = MainWindow.__new__(MainWindow)
    calls: list[str] = []
    window._selection_highlight_allowed = lambda: True
    window._refresh_selection_highlight = lambda: calls.append("refresh")
    window._clear_selection_highlight = lambda: calls.append("clear")

    window._sync_selection_highlight()

    assert calls == ["refresh"]


def test_sync_selection_highlight_clears_when_disallowed():
    window = MainWindow.__new__(MainWindow)
    calls: list[str] = []
    window._selection_highlight_allowed = lambda: False
    window._refresh_selection_highlight = lambda: calls.append("refresh")
    window._clear_selection_highlight = lambda: calls.append("clear")

    window._sync_selection_highlight()

    assert calls == ["clear"]


def test_show_playground_code_updates_panel():
    window = MainWindow.__new__(MainWindow)
    calls: list[str] = []
    node = object()
    panel = type(
        "PlaygroundStub",
        (),
        {
            "set_code": lambda self, code: calls.append(f"code:{code}"),
            "clear": lambda self: calls.append("clear"),
            "set_status": lambda self, message: calls.append(f"status:{message}"),
        },
    )()
    window.playgroundPanel = panel

    original_generator = MainWindow._show_playground_code.__globals__["build_locator_code"]
    MainWindow._show_playground_code.__globals__["build_locator_code"] = (
        lambda current: f"code for {current}"
    )
    try:
        window._show_playground_code(node)
    finally:
        MainWindow._show_playground_code.__globals__["build_locator_code"] = original_generator

    assert calls == [f"code:code for {node}"]


def test_on_playground_resolved_flashes_and_updates_status():
    window = MainWindow.__new__(MainWindow)
    calls: list[str] = []
    window._playground_runner = object()
    window._clear_selection_highlight = lambda: calls.append("clear_highlight")
    window.hide = lambda: calls.append("hide")
    window._flash_highlighter = type(
        "FlashStub",
        (),
        {
            "flash": lambda self, value: True,
            "duration_ms": lambda self: 1000,
        },
    )()
    window.playgroundPanel = type(
        "PlaygroundStub",
        (),
        {
            "set_running": lambda self, running: calls.append(f"running:{running}"),
            "set_status": lambda self, message: calls.append(f"status:{message}"),
        },
    )()
    window._show_status = lambda message: calls.append(f"show:{message}")
    window._restore_window_foreground = lambda: calls.append("restore")

    original_qtimer = MainWindow._on_playground_resolved.__globals__["QTimer"]

    class TimerStub:
        @staticmethod
        def singleShot(delay, callback):
            calls.append(f"singleShot:{delay}")
            callback()

    MainWindow._on_playground_resolved.__globals__["QTimer"] = TimerStub

    target = type("TargetStub", (), {"element_info": object()})()
    try:
        window._on_playground_resolved(target)
    finally:
        MainWindow._on_playground_resolved.__globals__["QTimer"] = original_qtimer

    assert calls == [
        "running:False",
        "clear_highlight",
        "hide",
        "singleShot:1000",
        "restore",
        "status:Locator code matched a control and flashed it on screen.",
        "show:Locator code matched a control and flashed it on screen.",
    ]


def test_run_playground_code_starts_runner_without_hiding_window():
    window = MainWindow.__new__(MainWindow)
    calls: list[str] = []
    window._stop_playground_runner = lambda: calls.append("stop_runner")
    window.playgroundPanel = type(
        "PlaygroundStub",
        (),
        {
            "set_running": lambda self, running: calls.append(f"running:{running}"),
            "set_status": lambda self, message: calls.append(f"status:{message}"),
        },
    )()
    window._show_status = lambda message: calls.append(f"show:{message}")

    class RunnerStub:
        def __init__(self, code, parent=None):
            calls.append(f"runner:{code}:{parent is window}")
            self.resolved = type(
                "SignalStub", (), {"connect": lambda self, cb: calls.append("connect_resolved")}
            )()
            self.error = type(
                "SignalStub", (), {"connect": lambda self, cb: calls.append("connect_error")}
            )()

        def start(self):
            calls.append("runner_start")

    original_runner = MainWindow._run_playground_code.__globals__["PlaygroundRunner"]
    MainWindow._run_playground_code.__globals__["PlaygroundRunner"] = RunnerStub
    try:
        window._run_playground_code("target = 1")
    finally:
        MainWindow._run_playground_code.__globals__["PlaygroundRunner"] = original_runner

    assert calls == [
        "stop_runner",
        "running:True",
        "status:Running locator code...",
        "show:Running generated locator code...",
        "runner:target = 1:True",
        "connect_resolved",
        "connect_error",
        "runner_start",
    ]


def test_on_playground_error_updates_status_without_restoring_window():
    window = MainWindow.__new__(MainWindow)
    calls: list[str] = []
    window._playground_runner = object()
    window.playgroundPanel = type(
        "PlaygroundStub",
        (),
        {
            "set_running": lambda self, running: calls.append(f"running:{running}"),
            "set_status": lambda self, message: calls.append(f"status:{message}"),
        },
    )()
    window._show_status = lambda message: calls.append(f"show:{message}")

    window._on_playground_error("boom")

    assert calls == [
        "running:False",
        "status:Locator code failed: boom",
        "show:Locator code failed: boom",
    ]
