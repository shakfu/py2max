"""Tests for nested patcher (subpatcher) core functionality.

Server-side nested-patcher state/navigation tests live in the py2max-server
package (tests/test_nested_patchers.py there).
"""

from pathlib import Path
import tempfile
from py2max import Patcher


def test_nested_patcher_parent_references():
    """Test that nested patchers maintain parent references."""
    p = Patcher("test.maxpat", title="Main")
    sub_box = p.add_subpatcher("p subpatch")
    sub = sub_box.subpatcher

    # Check parent reference
    assert hasattr(sub, "_parent")
    assert sub._parent is p


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
