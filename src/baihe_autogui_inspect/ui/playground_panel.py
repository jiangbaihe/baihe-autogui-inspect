from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget


class PlaygroundPanel(QWidget):
    run_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.titleLabel = QLabel("Playground")
        self.titleLabel.setStyleSheet("font-weight: 600;")

        self.helpLabel = QLabel(
            "Generate pywinauto locator code from the selected control, edit it if needed, "
            "and run it to verify the locator."
        )
        self.helpLabel.setWordWrap(True)

        self.codeEdit = QPlainTextEdit()
        self.codeEdit.setPlaceholderText("Select a control in the tree to generate locator code.")

        self.statusLabel = QLabel("Select a control to generate locator code.")
        self.statusLabel.setWordWrap(True)

        self.runButton = QPushButton("Run Locator Code")
        self.runButton.setEnabled(False)
        self.runButton.clicked.connect(self._emit_run_requested)

        layout = QVBoxLayout()
        layout.addWidget(self.titleLabel)
        layout.addWidget(self.helpLabel)
        layout.addWidget(self.codeEdit, 1)
        layout.addWidget(self.statusLabel)
        layout.addWidget(self.runButton)
        self.setLayout(layout)

    def _emit_run_requested(self) -> None:
        self.run_requested.emit(self.current_code())  # type: ignore[attr-defined]

    def current_code(self) -> str:
        return self.codeEdit.toPlainText()

    def set_code(self, code: str) -> None:
        self.codeEdit.setPlainText(code)
        self.runButton.setEnabled(bool(code.strip()))
        self.set_status("Locator code generated from the current tree selection.")

    def set_status(self, message: str) -> None:
        self.statusLabel.setText(message)

    def set_running(self, running: bool) -> None:
        self.codeEdit.setReadOnly(running)
        self.runButton.setEnabled((not running) and bool(self.current_code().strip()))
        self.runButton.setText("Running..." if running else "Run Locator Code")

    def clear(self) -> None:
        self.codeEdit.clear()
        self.codeEdit.setReadOnly(False)
        self.runButton.setEnabled(False)
        self.runButton.setText("Run Locator Code")
        self.set_status("Select a control to generate locator code.")
