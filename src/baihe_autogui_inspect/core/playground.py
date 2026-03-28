from __future__ import annotations

from typing import Any

from PySide6.QtCore import Signal
from pywinauto import Desktop

from baihe_autogui_inspect.core.inspector import NodeInfo, same_element
from baihe_autogui_inspect.core.thread_base import WorkerThread

_DESKTOP_ROOT_CONTROL_TYPES = {"Pane"}
_LABEL_BACKENDS = {"uia", "atspi"}
_EMPTY_VALUES = {"", "None"}


def _safe_attr(element_info, name: str):
    try:
        return getattr(element_info, name)
    except Exception:
        return None


def _safe_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    if not text or text in _EMPTY_VALUES or text.startswith("<error:"):
        return None
    return text


def _safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except Exception:
        return None


def _parent_of(element_info):
    try:
        return element_info.parent
    except Exception:
        return None


def _element_ancestry(element_info) -> list:
    chain = []
    current = element_info
    seen = set()
    while current is not None:
        current_id = id(current)
        if current_id in seen:
            break
        seen.add(current_id)
        chain.append(current)
        current = _parent_of(current)
    return list(reversed(chain))


def _locator_elements(node: NodeInfo) -> list:
    ancestry = _element_ancestry(node._element_info)
    if len(ancestry) > 1:
        root_control_type = _safe_text(_safe_attr(ancestry[0], "control_type"))
        if root_control_type in _DESKTOP_ROOT_CONTROL_TYPES:
            return ancestry[1:]
    return ancestry


def _child_index(parent, child) -> int | None:
    if parent is None:
        return None
    try:
        siblings = list(parent.children())
    except Exception:
        return None
    for index, sibling in enumerate(siblings):
        if same_element(sibling, child):
            return index
    return None


def _locator_entries(element_info, backend: str, *, parent=None) -> list[tuple[str, object]]:
    entries: list[tuple[str, object]] = [("visible_only", False)]

    title = _safe_text(_safe_attr(element_info, "name"))
    auto_id = _safe_text(_safe_attr(element_info, "automation_id"))
    control_type = _safe_text(_safe_attr(element_info, "control_type"))
    class_name = _safe_text(_safe_attr(element_info, "class_name"))
    control_id = _safe_int(_safe_attr(element_info, "control_id"))

    if title is not None:
        entries.append(("title", title))
    if backend == "uia" and auto_id is not None:
        entries.append(("auto_id", auto_id))
    if backend in _LABEL_BACKENDS and control_type is not None:
        entries.append(("control_type", control_type))
    if class_name is not None:
        entries.append(("class_name", class_name))
    if control_id not in (None, 0):
        entries.append(("control_id", control_id))

    if entries:
        return entries

    ctrl_index = _child_index(parent, element_info)
    if ctrl_index is not None:
        return [("ctrl_index", ctrl_index)]

    handle = _safe_int(_safe_attr(element_info, "handle"))
    if handle not in (None, 0):
        return [("handle", handle)]
    return [("title", _safe_text(_safe_attr(element_info, "name")) or "")]


def _format_call(prefix: str, entries: list[tuple[str, object]], *, indent: str) -> list[str]:
    if len(entries) == 1:
        key, value = entries[0]
        return [f"{indent}{prefix}({key}={value!r})"]

    lines = [f"{indent}{prefix}("]
    lines.extend(f"{indent}    {key}={value!r}," for key, value in entries)
    lines.append(f"{indent})")
    return lines


def build_locator_code(node: NodeInfo) -> str:
    elements = _locator_elements(node)
    if not elements:
        raise ValueError("Selected node has no locator ancestry")

    lines = [
        "from pywinauto import Desktop",
        "",
        f"desktop = Desktop(backend={node._backend!r})",
        "target = (",
    ]

    for index, element in enumerate(elements):
        parent = elements[index - 1] if index > 0 else None
        method = "window" if index == 0 else "child_window"
        prefix = f"desktop.{method}" if index == 0 else f".{method}"
        lines.extend(
            _format_call(
                prefix,
                _locator_entries(element, node._backend, parent=parent),
                indent="    ",
            )
        )

    lines.extend(["    .wrapper_object()", ")"])
    return "\n".join(lines)


def run_locator_code(code: str):
    namespace = {"Desktop": Desktop}
    exec(code, namespace, namespace)
    if "target" not in namespace:
        raise ValueError("Locator code must assign the resolved control to 'target'")
    target = namespace["target"]
    if hasattr(target, "wrapper_object"):
        return target.wrapper_object()
    return target


class PlaygroundRunner(WorkerThread):
    resolved = Signal(object)
    _worker_name = "PlaygroundRunner"

    def __init__(self, code: str, parent=None):
        super().__init__(parent)
        self._code = code

    def _run_impl(self) -> None:
        self.resolved.emit(run_locator_code(self._code))  # type: ignore[attr-defined]
