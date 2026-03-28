from __future__ import annotations

from baihe_autogui_inspect.core.pick_loader import _build_ancestry, _is_button_pressed, _parent_of


class _Element:
    def __init__(self, name: str, parent=None):
        self.name = name
        self.parent = parent


def test_build_ancestry_returns_root_to_target_chain():
    root = _Element("root")
    child = _Element("child", parent=root)
    leaf = _Element("leaf", parent=child)

    ancestry = _build_ancestry(leaf)

    assert ancestry == [root, child, leaf]


def test_build_ancestry_stops_on_parent_cycle():
    root = _Element("root")
    child = _Element("child", parent=root)
    leaf = _Element("leaf", parent=child)
    root.parent = child

    ancestry = _build_ancestry(leaf)

    assert ancestry == [root, child, leaf]


def test_parent_of_returns_none_when_parent_lookup_fails():
    class _BrokenElement:
        @property
        def parent(self):
            raise RuntimeError("boom")

    assert _parent_of(_BrokenElement()) is None


def test_is_button_pressed_checks_high_bit(monkeypatch):
    class _User32:
        @staticmethod
        def GetAsyncKeyState(button):
            return 0x8000 if button == 1 else 0

    monkeypatch.setitem(_is_button_pressed.__globals__, "_user32", _User32())

    assert _is_button_pressed(1) is True
    assert _is_button_pressed(2) is False


