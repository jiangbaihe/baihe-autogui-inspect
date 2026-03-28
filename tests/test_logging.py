from __future__ import annotations

from pathlib import Path

from baihe_autogui_inspect.utils.logging import resolve_log_level, resolve_log_path, setup_logging


def test_resolve_log_level_prefers_explicit_value(monkeypatch):
    monkeypatch.setenv("BAIHE_AUTOGUI_INSPECT_LOG_LEVEL", "warning")
    assert resolve_log_level("info") == "INFO"


def test_resolve_log_level_falls_back_to_env(monkeypatch):
    monkeypatch.setenv("BAIHE_AUTOGUI_INSPECT_LOG_LEVEL", "warning")

    assert resolve_log_level() == "WARNING"


def test_resolve_log_path_uses_cwd_for_relative_paths(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    resolved = resolve_log_path("logs/app.log")
    assert resolved == tmp_path / "logs" / "app.log"


def test_resolve_log_path_preserves_absolute_paths(tmp_path):
    log_path = tmp_path / "logs" / "app.log"

    assert resolve_log_path(log_path) == log_path


def test_setup_logging_returns_created_log_path(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    log_path = setup_logging(level="info", log_file="logs/app.log")
    assert isinstance(log_path, Path)
    assert log_path == tmp_path / "logs" / "app.log"
    assert log_path.parent.exists()


