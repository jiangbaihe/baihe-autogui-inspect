from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Tuple

from loguru import logger
from pywinauto import Desktop
from pywinauto import backend as pw_backend

Rect = Tuple[int, int, int, int]
_RECT_PATTERN = re.compile(r"-?\d+")
_LABEL_BACKENDS = {"uia", "atspi"}
_BASE_PROP_NAMES = (
    "control_id",
    "class_name",
    "enabled",
    "handle",
    "name",
    "process_id",
    "rectangle",
    "rich_text",
    "visible",
)
_BACKEND_PROP_NAMES = {
    "uia": ("automation_id", "control_type", "framework_id", "runtime_id"),
    "atspi": ("control_type", "runtime_id"),
}
_SIGNATURE_PROP_NAMES = (
    "handle",
    "process_id",
    "control_id",
    "automation_id",
    "runtime_id",
    "class_name",
    "control_type",
    "name",
    "rectangle",
)


@dataclass
class NodeInfo:
    """Pure-Python snapshot of one UI element node."""

    label: str
    props: list[list[str]]
    # Raw element_info kept for on-demand child loading
    _element_info: Any = field(repr=False, compare=False)
    _backend: str = field(repr=False, compare=False)
    signature: tuple[str, ...] = field(repr=False, compare=False, default_factory=tuple)
    has_children: bool = False
    children_loaded: bool = False
    anchor_prepared: bool = False
    children: list[NodeInfo] = field(default_factory=list)


def _safe(fn) -> str:
    try:
        return str(fn())
    except Exception as exc:
        return f"<error: {exc}>"


def _safe_attr(element_info, name: str) -> str:
    return _safe(lambda: getattr(element_info, name))


def _prop_row(element_info, name: str) -> list[str]:
    return [name, _safe_attr(element_info, name)]


def _prop_rows(element_info, names: tuple[str, ...]) -> list[list[str]]:
    return [_prop_row(element_info, name) for name in names]


def _element_signature(element_info) -> tuple[str, ...]:
    return tuple(_safe_attr(element_info, name) for name in _SIGNATURE_PROP_NAMES)


def _element_info_from(value: Any):
    if isinstance(value, NodeInfo):
        return value._element_info
    return value


def available_backends() -> tuple[str, ...]:
    return tuple(sorted(str(name) for name in pw_backend.registry.backends))


def validate_backend(backend: str) -> None:
    if backend not in pw_backend.registry.backends:
        supported = ", ".join(available_backends())
        raise ValueError(f"Unsupported backend '{backend}'. Available backends: {supported}")


def same_element(left, right) -> bool:
    try:
        if left == right:
            return True
    except Exception:
        pass
    return element_signature(left) == element_signature(right)


def element_signature(value) -> tuple[str, ...]:
    if isinstance(value, NodeInfo) and value.signature:
        return value.signature
    return _element_signature(_element_info_from(value))


def node_label(element_info, backend: str) -> str:
    try:
        name = str(element_info.name)
        ctrl = str(element_info.control_type) if backend in _LABEL_BACKENDS else ""
        return f'{ctrl} "{name}"' if ctrl else f'"{name}"'
    except Exception as exc:
        return f"<error: {exc}>"


def get_props(element_info, backend: str) -> list[list[str]]:
    props = _prop_rows(element_info, _BASE_PROP_NAMES)
    props.extend(_prop_rows(element_info, _BACKEND_PROP_NAMES.get(backend, ())))
    return props


def _normalize_rect_values(values: tuple[int, int, int, int]) -> Rect | None:
    left, top, right, bottom = values
    if right <= left or bottom <= top:
        return None
    return left, top, right, bottom


def _rectangle_from_attrs(rectangle: Any) -> Rect | None:
    try:
        values = (
            int(rectangle.left),
            int(rectangle.top),
            int(rectangle.right),
            int(rectangle.bottom),
        )
    except Exception:
        return None
    return _normalize_rect_values(values)


def _rectangle_from_sequence(rectangle: Any) -> Rect | None:
    if not isinstance(rectangle, (tuple, list)) or len(rectangle) < 4:
        return None
    try:
        values = (
            int(rectangle[0]),
            int(rectangle[1]),
            int(rectangle[2]),
            int(rectangle[3]),
        )
    except Exception:
        return None
    return _normalize_rect_values(values)


def _rectangle_from_string(rectangle: Any) -> Rect | None:
    matches = _RECT_PATTERN.findall(str(rectangle))
    if len(matches) < 4:
        return None
    values = (
        int(matches[0]),
        int(matches[1]),
        int(matches[2]),
        int(matches[3]),
    )
    return _normalize_rect_values(values)


def _normalize_rectangle(rectangle: Any) -> Rect | None:
    for parser in (_rectangle_from_attrs, _rectangle_from_sequence, _rectangle_from_string):
        parsed = parser(rectangle)
        if parsed is not None:
            return parsed
    return None


def element_rectangle(value: Any) -> Rect | None:
    element_info = _element_info_from(value)
    try:
        return _normalize_rectangle(element_info.rectangle)
    except Exception:
        return None


def _iter_has_items(items) -> bool:
    try:
        next(items)
        return True
    except StopIteration:
        return False


def _children_available(element_info) -> bool:
    children = element_info.children()
    if hasattr(children, "__len__"):
        return len(children) > 0
    return _iter_has_items(iter(children))


def probe_has_children(element_info) -> bool:
    """Lightweight child probe used to decide whether an expand arrow is needed."""
    try:
        return _iter_has_items(element_info.iter_children())
    except Exception as exc:
        logger.debug(f"Could not probe child elements with iter_children: {exc}")
    try:
        return _children_available(element_info)
    except Exception as exc:
        logger.debug(f"Could not probe child elements: {exc}")
        return False


def make_node(element_info, backend: str) -> NodeInfo:
    return NodeInfo(
        label=node_label(element_info, backend),
        props=get_props(element_info, backend),
        signature=_element_signature(element_info),
        _element_info=element_info,
        _backend=backend,
        has_children=probe_has_children(element_info),
    )


def _desktop_root_node(backend: str) -> NodeInfo:
    element_info = pw_backend.registry.backends[backend].element_info_class()
    return NodeInfo(
        label=node_label(element_info, backend),
        props=[],
        _element_info=element_info,
        _backend=backend,
        has_children=True,
    )


def _top_level_element_infos(backend: str) -> list[Any]:
    try:
        windows = Desktop(backend=backend).windows(top_level_only=True)
        return [window.element_info for window in windows]
    except Exception as exc:
        logger.warning(f"Desktop.windows() failed, falling back to root.children(): {exc}")
        element_info = pw_backend.registry.backends[backend].element_info_class()
        return list(element_info.children())


def _load_node_children(node: NodeInfo) -> list[NodeInfo]:
    child_elements = list(node._element_info.children())
    children = [make_node(child, node._backend) for child in child_elements]
    logger.debug(f"  -> {len(children)} children")
    return children


def load_children(node: NodeInfo, *, force: bool = False) -> list[NodeInfo]:
    """Load immediate children of node on demand (called from main thread or worker)."""
    if node.children_loaded and not force:
        return node.children
    logger.debug(f"Loading children of '{node.label}'")
    try:
        node.children = _load_node_children(node)
    except Exception as exc:
        logger.warning(f"Failed to load children of '{node.label}': {exc}")
        node.children = []
    node.has_children = bool(node.children)
    node.children_loaded = True
    return node.children


def prepare_anchor(node: NodeInfo, *, force: bool = False) -> list[NodeInfo]:
    """Prepare one anchor node.

    The anchor's direct children are loaded in full. Every newly created child
    is only probed for expandability, so deeper levels stay lazy while expand
    arrows remain accurate.
    """
    if node.anchor_prepared and not force:
        return node.children

    children = load_children(node, force=force)
    node.anchor_prepared = True
    return children


def _find_matching_child(children: list[NodeInfo], target: NodeInfo) -> NodeInfo | None:
    return next((child for child in children if same_element(child, target)), None)


def _match_or_append_child(children: list[NodeInfo], target: NodeInfo) -> NodeInfo:
    existing = _find_matching_child(children, target)
    if existing is not None:
        return existing
    children.append(target)
    return target


def prepare_path(root: NodeInfo, ancestry: list[NodeInfo]) -> list[tuple[str, ...]]:
    """Merge a picked ancestry path into the current tree using anchor semantics."""
    if len(ancestry) <= 1:
        return []

    current_children = root.children
    path_signatures: list[tuple[str, ...]] = []

    for target in ancestry[1:]:
        current = _match_or_append_child(current_children, target)
        path_signatures.append(current.signature)
        current_children = prepare_anchor(current, force=True)

    return path_signatures


def collect_top_level(backend: str) -> NodeInfo:
    """
    Collect the desktop root using the default root anchor semantics.

    The hidden desktop root fully loads the visible top-level windows and only
    probes those windows for expandability. Deeper levels stay lazy.
    """
    validate_backend(backend)
    logger.info(f"Collecting top-level tree with backend='{backend}'")
    root = _desktop_root_node(backend)
    root.children = [make_node(child, backend) for child in _top_level_element_infos(backend)]
    root.has_children = bool(root.children)
    root.children_loaded = True
    root.anchor_prepared = True
    logger.info(f"Top-level collection done: {len(root.children)} windows")
    return root


