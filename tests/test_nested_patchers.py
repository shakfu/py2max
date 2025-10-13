"""Tests for nested patcher (subpatcher) functionality in interactive editor."""

import asyncio
import json
from pathlib import Path
import tempfile
import pytest
from py2max import Patcher
from py2max.server import InteractiveWebSocketHandler, get_patcher_state_json


def test_get_patcher_state_with_subpatcher():
    """Test that patcher state includes subpatcher flag."""
    p = Patcher("test.maxpat")

    # Add a subpatcher box
    sub = p.add_subpatcher("p subpatch")

    # Add regular object
    osc = p.add_textbox("cycle~ 440")

    # Get state
    state = get_patcher_state_json(p)

    # Check state structure
    assert "boxes" in state
    assert "lines" in state
    assert "patcher_path" in state
    assert "patcher_title" in state

    # Check boxes
    boxes = state["boxes"]
    assert len(boxes) == 2

    # Find subpatcher box
    sub_box = next(b for b in boxes if b["id"] == sub.id)
    assert sub_box["has_subpatcher"] is True

    # Find regular box
    osc_box = next(b for b in boxes if b["id"] == osc.id)
    assert osc_box["has_subpatcher"] is False


def test_patcher_path_single_level():
    """Test patcher path for single-level patcher."""
    p = Patcher("test.maxpat", title="Main")
    state = get_patcher_state_json(p)

    assert state["patcher_path"] == ["Main"]


def test_patcher_path_nested():
    """Test patcher path for nested patchers."""
    # Create main patcher
    p = Patcher("test.maxpat", title="Main")

    # Add subpatcher
    sub_box = p.add_subpatcher("p level1")
    sub1 = sub_box.subpatcher
    sub1.title = "Level1"

    # Add nested subpatcher
    sub_box2 = sub1.add_subpatcher("p level2")
    sub2 = sub_box2.subpatcher
    sub2.title = "Level2"

    # Test path at each level
    state_main = get_patcher_state_json(p)
    assert state_main["patcher_path"] == ["Main"]

    state_sub1 = get_patcher_state_json(sub1)
    assert state_sub1["patcher_path"] == ["Main", "Level1"]

    state_sub2 = get_patcher_state_json(sub2)
    assert state_sub2["patcher_path"] == ["Main", "Level1", "Level2"]


def test_nested_patcher_parent_references():
    """Test that nested patchers maintain parent references."""
    p = Patcher("test.maxpat", title="Main")
    sub_box = p.add_subpatcher("p subpatch")
    sub = sub_box.subpatcher

    # Check parent reference
    assert hasattr(sub, "_parent")
    assert sub._parent is p


@pytest.mark.asyncio
async def test_handler_navigate_to_subpatcher():
    """Test WebSocket handler navigates to subpatcher correctly."""
    p = Patcher("test.maxpat", title="Main")

    # Add subpatcher
    sub_box = p.add_subpatcher("p subpatch")
    sub = sub_box.subpatcher
    sub.title = "Subpatch"

    # Add objects to both patchers
    p.add_textbox("cycle~ 440")
    sub.add_textbox("gain~")

    # Create handler
    handler = InteractiveWebSocketHandler(p)

    # Verify initially at root
    assert handler.patcher is p
    assert handler.root_patcher is p

    # Simulate navigation message
    await handler.handle_navigate_to_subpatcher({"box_id": sub_box.id})

    # Verify navigated to subpatcher
    assert handler.patcher is sub
    assert handler.root_patcher is p  # Root should remain unchanged


@pytest.mark.asyncio
async def test_handler_navigate_to_parent():
    """Test WebSocket handler navigates to parent correctly."""
    p = Patcher("test.maxpat", title="Main")
    sub_box = p.add_subpatcher("p subpatch")
    sub = sub_box.subpatcher

    # Create handler
    handler = InteractiveWebSocketHandler(p)

    # Navigate to subpatcher first
    await handler.handle_navigate_to_subpatcher({"box_id": sub_box.id})
    assert handler.patcher is sub

    # Navigate back to parent
    await handler.handle_navigate_to_parent()
    assert handler.patcher is p


@pytest.mark.asyncio
async def test_handler_navigate_to_root():
    """Test WebSocket handler navigates to root correctly."""
    p = Patcher("test.maxpat", title="Main")
    sub_box1 = p.add_subpatcher("p level1")
    sub1 = sub_box1.subpatcher
    sub_box2 = sub1.add_subpatcher("p level2")
    sub2 = sub_box2.subpatcher

    # Create handler
    handler = InteractiveWebSocketHandler(p)

    # Navigate deep
    await handler.handle_navigate_to_subpatcher({"box_id": sub_box1.id})
    await handler.handle_navigate_to_subpatcher({"box_id": sub_box2.id})
    assert handler.patcher is sub2

    # Navigate to root
    await handler.handle_navigate_to_root()
    assert handler.patcher is p


@pytest.mark.asyncio
async def test_handler_navigate_nonexistent_subpatcher():
    """Test that navigating to non-existent subpatcher doesn't crash."""
    p = Patcher("test.maxpat")
    handler = InteractiveWebSocketHandler(p)

    # Try to navigate to non-existent box
    await handler.handle_navigate_to_subpatcher({"box_id": "nonexistent"})

    # Should remain at current patcher
    assert handler.patcher is p


@pytest.mark.asyncio
async def test_handler_navigate_non_subpatcher_box():
    """Test that navigating to a box without subpatcher doesn't crash."""
    p = Patcher("test.maxpat")
    osc = p.add_textbox("cycle~ 440")  # Regular box, no subpatcher

    handler = InteractiveWebSocketHandler(p)

    # Try to navigate to regular box
    await handler.handle_navigate_to_subpatcher({"box_id": osc.id})

    # Should remain at current patcher
    assert handler.patcher is p


def test_subpatcher_with_objects():
    """Test subpatcher can contain objects."""
    p = Patcher("test.maxpat")
    sub_box = p.add_subpatcher("p synth")
    sub = sub_box.subpatcher

    # Add objects to subpatcher
    osc = sub.add_textbox("cycle~ 440")
    gain = sub.add_textbox("gain~")
    sub.add_line(osc, gain)

    # Get state
    state = get_patcher_state_json(sub)

    assert len(state["boxes"]) == 2
    assert len(state["lines"]) == 1


def test_save_preserves_nested_structure():
    """Test that saving preserves nested patcher structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "nested.maxpat"

        # Create nested structure
        p = Patcher(path, title="Main")
        sub_box = p.add_subpatcher("p effect")
        sub = sub_box.subpatcher
        sub.title = "Effect"
        sub.add_textbox("gain~")

        # Save
        p.save()

        # Load and verify
        p2 = Patcher.from_file(path)
        assert len(p2._boxes) == 1

        # Check subpatcher exists
        loaded_sub_box = p2._boxes[0]
        assert hasattr(loaded_sub_box, "subpatcher")
        assert loaded_sub_box.subpatcher is not None

        # Check subpatcher content
        loaded_sub = loaded_sub_box.subpatcher
        assert len(loaded_sub._boxes) == 1
        assert loaded_sub._boxes[0].text == "gain~"


def test_multiple_subpatchers():
    """Test multiple subpatchers in same patcher."""
    p = Patcher("test.maxpat")

    sub1_box = p.add_subpatcher("p osc")
    sub2_box = p.add_subpatcher("p filter")
    sub3_box = p.add_subpatcher("p env")

    # Add content to each
    sub1_box.subpatcher.add_textbox("cycle~ 440")
    sub2_box.subpatcher.add_textbox("lores~")
    sub3_box.subpatcher.add_textbox("adsr~")

    # Get state
    state = get_patcher_state_json(p)

    # All boxes should have subpatcher flag
    assert all(box["has_subpatcher"] for box in state["boxes"])
    assert len(state["boxes"]) == 3


def test_deeply_nested_patchers():
    """Test deeply nested patcher structure."""
    p = Patcher("test.maxpat", title="L0")

    current = p
    for i in range(5):
        sub_box = current.add_subpatcher(f"p level{i + 1}")
        current = sub_box.subpatcher
        current.title = f"L{i + 1}"
        current.add_textbox(f"obj{i}")

    # Check path at deepest level
    state = get_patcher_state_json(current)
    expected_path = ["L0", "L1", "L2", "L3", "L4", "L5"]
    assert state["patcher_path"] == expected_path


def test_patcher_state_no_title():
    """Test patcher state when patcher has no title."""
    p = Patcher("test.maxpat")  # No title
    state = get_patcher_state_json(p)

    # Should use 'Main' as default
    assert "Main" in state["patcher_path"]
