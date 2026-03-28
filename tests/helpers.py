from __future__ import annotations


class UiElementStub:
    def __init__(self, name: str, ctrl_type: str = "Button"):
        self.name = name
        self.control_type = ctrl_type
        self.control_id = 1
        self.class_name = "cls"
        self.enabled = True
        self.handle = 0
        self.process_id = 42
        self.rectangle = "(0,0,10,10)"
        self.rich_text = ""
        self.visible = True
        self.automation_id = "auto1"
        self.framework_id = "Win32"
        self.runtime_id = (1, 2)

    def children(self):
        return []

    def iter_children(self):
        return iter(())


