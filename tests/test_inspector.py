"""Tests for baihe_autogui_inspect.core.inspector; pure Python, no Qt required."""

from __future__ import annotations

from unittest.mock import MagicMock, PropertyMock, patch

from baihe_autogui_inspect.core.inspector import (
    NodeInfo,
    available_backends,
    element_rectangle,
    element_signature,
    get_props,
    load_children,
    make_node,
    node_label,
    prepare_anchor,
    prepare_path,
    same_element,
    validate_backend,
)


def _make_element(name="TestName", ctrl_type="Button", **kwargs):
    element = MagicMock()
    element.name = name
    element.control_type = ctrl_type
    element.control_id = 1
    element.class_name = "cls"
    element.enabled = True
    element.handle = 0
    element.process_id = 42
    element.rectangle = "(0,0,100,100)"
    element.rich_text = ""
    element.visible = True
    element.automation_id = "auto1"
    element.framework_id = "Win32"
    element.runtime_id = (1, 2)
    element.children.return_value = []
    element.iter_children.side_effect = lambda **_kwargs: iter(element.children.return_value)
    for key, value in kwargs.items():
        setattr(element, key, value)
    return element


def test_node_label_uia():
    element = _make_element(name="Foo", ctrl_type="Button")
    label = node_label(element, "uia")
    assert "Button" in label
    assert "Foo" in label


def test_node_label_win32():
    element = _make_element(name="Bar")
    label = node_label(element, "win32")
    assert "Bar" in label
    assert "Button" not in label


def test_node_label_error():
    element = MagicMock()
    type(element).name = PropertyMock(side_effect=RuntimeError("boom"))
    label = node_label(element, "uia")
    assert "error" in label


def test_get_props_uia_has_automation_id():
    element = _make_element()
    props = get_props(element, "uia")
    keys = [row[0] for row in props]
    assert "automation_id" in keys
    assert "framework_id" in keys


def test_get_props_win32_no_automation_id():
    element = _make_element()
    props = get_props(element, "win32")
    keys = [row[0] for row in props]
    assert "automation_id" not in keys


def test_get_props_handles_exception():
    element = _make_element()
    type(element).control_id = PropertyMock(side_effect=RuntimeError("fail"))
    props = get_props(element, "win32")
    control_id_row = next(row for row in props if row[0] == "control_id")
    assert "error" in control_id_row[1]


def test_make_node_no_children():
    element = _make_element(name="Root")
    node = make_node(element, "uia")
    assert isinstance(node, NodeInfo)
    assert "Root" in node.label
    assert node.children == []
    assert node.children_loaded is False


def test_load_children_no_children():
    element = _make_element(name="Root")
    node = make_node(element, "uia")
    children = load_children(node)
    assert children == []
    assert node.children_loaded is True


def test_load_children_with_children():
    child_element = _make_element(name="Child")
    root_element = _make_element(name="Root")
    root_element.children.return_value = [child_element]
    node = make_node(root_element, "uia")
    children = load_children(node)
    assert len(children) == 1
    assert "Child" in children[0].label


def test_load_children_exception_is_tolerated():
    element = _make_element(name="Root")
    element.children.side_effect = RuntimeError("access denied")
    node = make_node(element, "uia")
    children = load_children(node)
    assert children == []
    assert node.children_loaded is True


def test_load_children_idempotent():
    element = _make_element(name="Root")
    node = make_node(element, "uia")
    load_children(node)
    load_children(node)
    assert element.children.call_count == 1


def test_load_children_force_refreshes_existing_snapshot():
    first_child = _make_element(name="First")
    second_child = _make_element(name="Second")
    element = _make_element(name="Root")
    element.children.return_value = [first_child]
    node = make_node(element, "uia")

    load_children(node)
    element.children.return_value = [first_child, second_child]

    children = load_children(node, force=True)

    assert [child.label for child in children] == [
        make_node(first_child, "uia").label,
        make_node(second_child, "uia").label,
    ]
    assert element.children.call_count == 2


def test_probe_has_children_uses_lightweight_iteration():
    child_element = _make_element(name="Child")
    root_element = _make_element(name="Root")
    root_element.children.return_value = [child_element]
    root_element.iter_children.side_effect = lambda **_kwargs: iter([child_element])

    node = make_node(root_element, "uia")

    assert node.has_children is True
    assert root_element.iter_children.call_count == 1
    assert root_element.children.call_count == 0


def test_prepare_anchor_loads_only_direct_children():
    grandchild_element = _make_element(name="Grandchild")
    child_element = _make_element(name="Child")
    child_element.children.return_value = [grandchild_element]
    root_element = _make_element(name="Root")
    root_element.children.return_value = [child_element]
    node = make_node(root_element, "uia")

    children = prepare_anchor(node)

    assert node.anchor_prepared is True
    assert len(children) == 1
    assert children[0].children_loaded is False
    assert children[0].has_children is True


def test_collect_top_level_integration():
    root_element = _make_element(name="Desktop")
    child_element = _make_element(name="Window1")

    mock_cls = MagicMock(return_value=root_element)
    mock_backend = MagicMock()
    mock_backend.element_info_class = mock_cls
    wrapper = MagicMock()
    wrapper.element_info = child_element

    with patch("baihe_autogui_inspect.core.inspector.Desktop") as mock_desktop, patch(
        "baihe_autogui_inspect.core.inspector.pw_backend"
    ) as mock_pw:
        mock_pw.registry.backends = {"uia": mock_backend}
        mock_desktop.return_value.windows.return_value = [wrapper]
        from baihe_autogui_inspect.core.inspector import collect_top_level

        root = collect_top_level("uia")

    assert isinstance(root, NodeInfo)
    assert root.anchor_prepared is True
    assert len(root.children) == 1
    assert "Window1" in root.children[0].label
    assert root.children[0].children_loaded is False


def test_collect_top_level_falls_back_to_root_children_when_desktop_windows_fails():
    root_element = _make_element(name="Desktop")
    child_element = _make_element(name="Window1")
    root_element.children.return_value = [child_element]

    mock_cls = MagicMock(return_value=root_element)
    mock_backend = MagicMock()
    mock_backend.element_info_class = mock_cls

    with patch("baihe_autogui_inspect.core.inspector.Desktop") as mock_desktop, patch(
        "baihe_autogui_inspect.core.inspector.pw_backend"
    ) as mock_pw:
        mock_pw.registry.backends = {"uia": mock_backend}
        mock_desktop.return_value.windows.side_effect = RuntimeError("boom")
        from baihe_autogui_inspect.core.inspector import collect_top_level

        root = collect_top_level("uia")

    assert isinstance(root, NodeInfo)
    assert root.anchor_prepared is True
    assert len(root.children) == 1
    assert "Window1" in root.children[0].label
    assert root_element.children.call_count == 1


def test_available_backends_are_sorted():
    with patch("baihe_autogui_inspect.core.inspector.pw_backend") as mock_pw:
        mock_pw.registry.backends = {"win32": object(), "uia": object()}
        assert available_backends() == ("uia", "win32")


def test_validate_backend_rejects_unknown_value():
    with patch("baihe_autogui_inspect.core.inspector.pw_backend") as mock_pw:
        mock_pw.registry.backends = {"uia": object()}
        try:
            validate_backend("unknown")
        except ValueError as exc:
            assert "unknown" in str(exc)
            assert "uia" in str(exc)
        else:
            raise AssertionError("validate_backend should reject unknown backends")


def test_same_element_uses_signature_fallback():
    class Element:
        def __init__(self, name: str, rectangle: str):
            self.handle = 10
            self.process_id = 20
            self.control_id = 30
            self.automation_id = "auto"
            self.runtime_id = (1, 2)
            self.class_name = "Button"
            self.control_type = "Button"
            self.name = name
            self.rectangle = rectangle

        def __eq__(self, other):
            raise RuntimeError("no direct equality")

    left = Element("", "(1,2,3,4)")
    right = Element("", "(1,2,3,4)")
    assert same_element(left, right)


def test_same_element_detects_different_controls():
    left = _make_element(name="", rectangle="(1,2,3,4)")
    right = _make_element(name="", rectangle="(5,6,7,8)")
    assert not same_element(left, right)


def test_make_node_populates_signature():
    element = _make_element(name="sig")
    node = make_node(element, "uia")
    assert node.signature


def test_element_signature_prefers_cached_node_signature():
    node = make_node(_make_element(name="cached"), "uia")
    node.signature = ("cached",)

    assert element_signature(node) == ("cached",)


def test_element_rectangle_reads_node_rectangle():
    node = make_node(_make_element(rectangle="(1,2,11,22)"), "uia")
    assert element_rectangle(node) == (1, 2, 11, 22)


def test_element_rectangle_rejects_invalid_bounds():
    node = make_node(_make_element(rectangle="(8,8,8,20)"), "uia")
    assert element_rectangle(node) is None


def test_element_rectangle_accepts_sequence():
    node = make_node(_make_element(rectangle=(1, 2, 11, 22)), "uia")
    assert element_rectangle(node) == (1, 2, 11, 22)


def test_element_rectangle_accepts_attr_object():
    rectangle = type("RectStub", (), {"left": 1, "top": 2, "right": 11, "bottom": 22})()
    node = make_node(_make_element(rectangle=rectangle), "uia")

    assert element_rectangle(node) == (1, 2, 11, 22)


def test_probe_has_children_falls_back_to_children_collection():
    child_element = _make_element(name="Child")
    root_element = _make_element(name="Root")
    root_element.iter_children.side_effect = RuntimeError("iter unavailable")
    root_element.children.return_value = [child_element]

    node = make_node(root_element, "uia")

    assert node.has_children is True
    assert root_element.children.call_count == 1


def test_prepare_path_merges_path_into_root():
    root = _make_element(name="Desktop", ctrl_type="Pane")
    sibling_element = _make_element(name="Sibling", ctrl_type="Group")
    target_tree_element = _make_element(name="", ctrl_type="Tree")
    target_group_element = _make_element(name="", ctrl_type="Group")
    target_group_element.children.return_value = [target_tree_element]
    window = _make_element(name="Window", ctrl_type="Window")
    window.children.return_value = [sibling_element, target_group_element]
    root_node = make_node(root, "uia")
    root_node.children = [make_node(window, "uia")]
    root_node.children_loaded = True

    group = make_node(target_group_element, "uia")
    tree = make_node(target_tree_element, "uia")
    signatures = prepare_path(root_node, [root_node, root_node.children[0], group, tree])

    assert len(signatures) == 3
    assert root_node.children[0].anchor_prepared is True
    assert any(
        child.label == make_node(sibling_element, "uia").label
        for child in root_node.children[0].children
    )
    matched_group = next(
        child for child in root_node.children[0].children if child.label == group.label
    )
    assert matched_group.children[0].label == tree.label


def test_prepare_path_keeps_parent_siblings_when_target_missing():
    root = _make_element(name="Desktop", ctrl_type="Pane")
    sibling_element = _make_element(name="Sibling", ctrl_type="Group")
    window = _make_element(name="Window", ctrl_type="Window")
    window.children.return_value = [sibling_element]

    root_node = make_node(root, "uia")
    root_node.children = [make_node(window, "uia")]
    root_node.children_loaded = True

    missing_group = make_node(_make_element(name="Missing", ctrl_type="Group"), "uia")
    signatures = prepare_path(root_node, [root_node, root_node.children[0], missing_group])

    assert len(signatures) == 2
    assert any(
        child.label == make_node(sibling_element, "uia").label
        for child in root_node.children[0].children
    )
    assert any(child.label == missing_group.label for child in root_node.children[0].children)


def test_prepare_path_refreshes_all_ancestor_siblings():
    root = _make_element(name="Desktop", ctrl_type="Pane")
    window_sibling = _make_element(name="WindowSibling", ctrl_type="Window")
    group_sibling = _make_element(name="GroupSibling", ctrl_type="Group")
    tree_sibling = _make_element(name="TreeSibling", ctrl_type="Tree")
    target_tree_element = _make_element(name="TargetTree", ctrl_type="Tree")
    target_group_element = _make_element(name="TargetGroup", ctrl_type="Group")
    target_group_element.children.return_value = [tree_sibling, target_tree_element]
    target_window_element = _make_element(name="TargetWindow", ctrl_type="Window")
    target_window_element.children.return_value = [group_sibling, target_group_element]

    root_node = make_node(root, "uia")
    partial_window = make_node(target_window_element, "uia")
    partial_group = make_node(target_group_element, "uia")
    partial_window.children = [partial_group]
    partial_window.children_loaded = True
    partial_group.children = [make_node(target_tree_element, "uia")]
    partial_group.children_loaded = True
    root_node.children = [make_node(window_sibling, "uia"), partial_window]
    root_node.children_loaded = True

    target_tree = make_node(target_tree_element, "uia")
    signatures = prepare_path(root_node, [root_node, partial_window, partial_group, target_tree])

    assert len(signatures) == 3

    refreshed_window = next(
        child for child in root_node.children if child.label == partial_window.label
    )
    assert any(
        child.label == make_node(group_sibling, "uia").label for child in refreshed_window.children
    )

    refreshed_group = next(
        child for child in refreshed_window.children if child.label == partial_group.label
    )
    assert any(
        child.label == make_node(tree_sibling, "uia").label for child in refreshed_group.children
    )
    assert any(child.label == target_tree.label for child in refreshed_group.children)
