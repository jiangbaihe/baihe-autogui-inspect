from importlib.metadata import version

from baihe_autogui_inspect import __version__
from baihe_autogui_inspect.main import APP_NAME, main


def main_check() -> None:
    assert APP_NAME == "Baihe AutoGUI Inspect"
    assert callable(main)
    assert __version__ == version("baihe-autogui-inspect")


if __name__ == "__main__":
    main_check()
