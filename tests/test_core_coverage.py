"""Tests to achieve 100% coverage for py2max.core module."""

import pytest
from unittest.mock import Mock, patch
from py2max.core import Patcher, Box
from py2max.common import Rect


class TestCoreCoverage:
    """Test missing coverage in core.py module."""

    def test_find_by_text_start(self):
        """Test find method when text starts with search string."""
        p = Patcher()
        
        # Add objects with text that starts with search string
        obj1 = p.add_textbox("test message")
        obj2 = p.add_textbox("test another")
        obj3 = p.add_textbox("different")
        
        # Test finding by text start
        result = p.find("test")
        assert result is not None
        assert result.text.startswith("test")

    def test_find_not_found(self):
        """Test find method when no object is found."""
        p = Patcher()
        
        # Add objects that don't match
        p.add_textbox("different message")
        p.add_textbox("another message")
        
        # Test finding non-existent text
        result = p.find("nonexistent")
        assert result is None

    def test_find_box_by_text_start(self):
        """Test find_box method when text starts with search string."""
        p = Patcher()
        
        # Add boxes with text that starts with search string
        box1 = p.add_textbox("test message")
        box2 = p.add_textbox("test another")
        box3 = p.add_textbox("different")
        
        # Test finding by text start
        result = p.find_box("test")
        assert result is not None
        assert result.text.startswith("test")

    def test_find_box_not_found(self):
        """Test find_box method when no box is found."""
        p = Patcher()
        
        # Add boxes that don't match
        p.add_textbox("different message")
        p.add_textbox("another message")
        
        # Test finding non-existent text
        result = p.find_box("nonexistent")
        assert result is None

    def test_find_box_with_index_by_text_start(self):
        """Test find_box_with_index method when text starts with search string."""
        p = Patcher()
        
        # Add boxes with text that starts with search string
        box1 = p.add_textbox("test message")
        box2 = p.add_textbox("test another")
        box3 = p.add_textbox("different")
        
        # Test finding by text start
        result = p.find_box_with_index("test")
        assert result is not None
        index, box = result
        assert box.text.startswith("test")
        assert index >= 0

    def test_find_box_with_index_not_found(self):
        """Test find_box_with_index method when no box is found."""
        p = Patcher()
        
        # Add boxes that don't match
        p.add_textbox("different message")
        p.add_textbox("another message")
        
        # Test finding non-existent text
        result = p.find_box_with_index("nonexistent")
        assert result is None

    def test_add_comment_with_default_height_fallback(self):
        """Test add_comment when box height doesn't match default and no maxclass defaults."""
        p = Patcher()
        
        # Create a box with custom height
        box = p.add_textbox("test")
        # Manually set a different height
        box.patching_rect = Rect(0, 0, 100, 50)  # Different height
        
        # Mock the layout manager to have a different box_height
        p._layout_mgr.box_height = 22.0
        
        # Add comment - should use layout manager's box_height as fallback
        comment = p.add_comment("test comment", box)
        assert comment is not None

    def test_box_oid_property_with_id(self):
        """Test Box.oid property when id exists."""
        p = Patcher()
        box = p.add_textbox("test")
        
        # The id should be set and oid should extract the numeric part
        assert box.id is not None
        assert box.oid is not None
        assert isinstance(box.oid, int)

    def test_box_oid_property_without_id(self):
        """Test Box.oid property when id is None."""
        box = Box("test", patching_rect=Rect(0, 0, 100, 100))
        box.id = None
        
        assert box.oid is None

    def test_box_help_text(self):
        """Test Box.help_text method."""
        p = Patcher()
        box = p.add_textbox("test")
        
        # This should call the maxref.get_object_help method
        help_text = box.help_text()
        # The exact content depends on maxref implementation
        assert isinstance(help_text, str)

    def test_box_get_object_name_newobj_with_text(self):
        """Test Box._get_object_name for newobj with text."""
        box = Box("newobj", patching_rect=Rect(0, 0, 100, 100))
        box._kwds = {"text": "osc~ 440"}
        
        name = box._get_object_name()
        assert name == "osc~"

    def test_box_get_object_name_newobj_with_empty_text(self):
        """Test Box._get_object_name for newobj with empty text."""
        box = Box("newobj", patching_rect=Rect(0, 0, 100, 100))
        box._kwds = {"text": ""}
        
        name = box._get_object_name()
        assert name == "newobj"

    def test_box_get_object_name_newobj_with_whitespace_text(self):
        """Test Box._get_object_name for newobj with whitespace-only text."""
        box = Box("newobj", patching_rect=Rect(0, 0, 100, 100))
        box._kwds = {"text": "   "}
        
        name = box._get_object_name()
        assert name == "newobj"

    def test_box_get_object_name_regular_maxclass(self):
        """Test Box._get_object_name for regular maxclass."""
        box = Box("osc~", patching_rect=Rect(0, 0, 100, 100))
        
        name = box._get_object_name()
        assert name == "osc~"
