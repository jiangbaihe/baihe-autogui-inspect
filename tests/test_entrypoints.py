from __future__ import annotations

import importlib


def test_package_main_module_exposes_main():
    module = importlib.import_module("baihe_autogui_inspect.__main__")
    assert callable(module.main)


def test_prepare_runtime_environment_sets_warning_filter_and_coinit(monkeypatch):
    module = importlib.import_module("baihe_autogui_inspect.main")
    calls: list[tuple[object, object]] = []

    monkeypatch.setattr(
        module.warnings,
        "simplefilter",
        lambda action, category: calls.append((action, category)),
    )
    monkeypatch.delattr(module.sys, "coinit_flags", raising=False)

    module._prepare_runtime_environment()

    assert calls == [("ignore", UserWarning)]
    assert module.sys.coinit_flags == 2


def test_main_returns_run_result(monkeypatch):
    module = importlib.import_module("baihe_autogui_inspect.main")
    monkeypatch.setattr(module, "run", lambda argv=None: 7)

    assert module.main(["baihe-inspect"]) == 7


def test_create_application_sets_application_name(qapp):
    del qapp
    module = importlib.import_module("baihe_autogui_inspect.main")

    app = module._create_application(["baihe-inspect"])

    assert app.applicationName() == module.APP_NAME


