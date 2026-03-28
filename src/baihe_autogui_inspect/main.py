from __future__ import annotations

import sys
import warnings
from typing import Sequence


def _prepare_runtime_environment() -> None:
    warnings.simplefilter("ignore", UserWarning)
    sys.coinit_flags = 2  # type: ignore[attr-defined]


_prepare_runtime_environment()

from PySide6.QtWidgets import QApplication  # noqa: E402

from baihe_autogui_inspect.ui.main_window import MainWindow  # noqa: E402
from baihe_autogui_inspect.utils.logging import setup_logging  # noqa: E402

APP_NAME = "Baihe AutoGUI Inspect"


def _create_application(args: Sequence[str]) -> QApplication:
    app = QApplication.instance() or QApplication(list(args))
    app.setApplicationName(APP_NAME)
    return app


def run(argv: Sequence[str] | None = None) -> int:
    setup_logging()
    args = list(sys.argv if argv is None else argv)
    app = _create_application(args)
    window = MainWindow()
    window.show()
    return app.exec()


def main(argv: Sequence[str] | None = None) -> int:
    return run(argv)


if __name__ == "__main__":
    raise SystemExit(main())
