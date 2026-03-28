from __future__ import annotations

import pytest

from baihe_autogui_inspect.core.inspector import make_node
from baihe_autogui_inspect.core.playground import build_locator_code, run_locator_code


class _Element:
    def __init__(
        self,
        name: str,
        *,
        parent=None,
        control_type: str = "Button",
        automation_id: str = "auto",
        class_name: str = "cls",
        control_id: int = 1,
    ):
        self.name = name
        self.parent = parent
        self.control_type = control_type
        self.automation_id = automation_id
        self.class_name = class_name
        self.control_id = control_id
        self.enabled = True
        self.handle = 0
        self.process_id = 42
        self.rectangle = "(0,0,10,10)"
        self.rich_text = ""
        self.visible = True
        self.framework_id = "Win32"
        self.runtime_id = (1, 2)
        self._children: list[_Element] = []
        if parent is not None:
            parent._children.append(self)

    def children(self):
        return list(self._children)

    def iter_children(self):
        return iter(self._children)


def test_build_locator_code_generates_window_chain():
    desktop = _Element("Desktop", control_type="Pane", automation_id="", class_name="Desktop")
    window = _Element(
        "Calculator",
        parent=desktop,
        control_type="Window",
        automation_id="",
        class_name="CalcFrame",
        control_id=0,
    )
    button = _Element(
        "7",
        parent=window,
        control_type="Button",
        automation_id="num7Button",
        class_name="Button",
    )

    code = build_locator_code(make_node(button, "uia"))

    assert "desktop = Desktop(backend='uia')" in code
    assert "desktop.window(" in code
    assert "visible_only=False" in code
    assert "title='Calculator'" in code
    assert ".child_window(" in code
    assert "auto_id='num7Button'" in code
    assert ".wrapper_object()" in code


def test_run_locator_code_returns_target_value():
    assert run_locator_code("target = 123") == 123


def test_run_locator_code_uses_wrapper_object():
    class _Spec:
        def wrapper_object(self):
            return "wrapped"

    assert (
        run_locator_code("target = type('Spec', (), {'wrapper_object': lambda self: 'wrapped'})()")
        == "wrapped"
    )


def test_run_locator_code_requires_target_assignment():
    with pytest.raises(ValueError):
        run_locator_code("value = 123")
