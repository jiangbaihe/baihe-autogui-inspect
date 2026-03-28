from __future__ import annotations

from PySide6.QtWidgets import QLabel


class TimingPresenter:
    """Formats timing feedback for the permanent status-bar label."""

    def __init__(self, label: QLabel):
        self._label = label

    def show(self, action: str, elapsed: float, detail: str = "", *, failed: bool = False) -> None:
        detail_text = f" | {detail}" if detail else ""
        slow_text = ""
        color = ""
        if failed:
            slow_text = " | failed"
            color = "#b91c1c"
        elif elapsed >= 3.0:
            slow_text = " | slow"
            color = "#b45309"
        elif elapsed >= 1.0:
            slow_text = " | noticeable"
            color = "#a16207"

        self._label.setText(f"{action}: {elapsed:.2f}s{slow_text}{detail_text}")
        self._label.setStyleSheet(f"color: {color};" if color else "")
