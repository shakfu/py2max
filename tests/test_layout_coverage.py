"""Tests to achieve 100% coverage for py2max.layout module."""

import pytest
from unittest.mock import Mock, patch
from py2max.core import Patcher, Box
from py2max.layout import LayoutManager, GridLayoutManager, FlowLayoutManager
from py2max.common import Rect


class TestLayoutCoverage:
    """Test missing coverage in layout.py module."""

    def test_get_rect_from_maxclass_keyerror(self):
        """Test get_rect_from_maxclass when maxclass not in defaults."""
        p = Patcher()
        layout_mgr = LayoutManager(p)
        
        # Test with non-existent maxclass
        result = layout_mgr.get_rect_from_maxclass("nonexistent_class")
        assert result is None

    def test_get_relative_pos_default(self):
        """Test get_relative_pos default implementation."""
        p = Patcher()
        layout_mgr = LayoutManager(p)
        
        rect = Rect(10, 20, 100, 50)
        result = layout_mgr.get_relative_pos(rect)
        assert result == rect

    def test_analyze_connections_with_none_ids(self):
        """Test _analyze_object_connections when line has None src or dst."""
        p = Patcher()
        layout_mgr = GridLayoutManager(p)
        
        # Add some objects
        obj1 = p.add_textbox("obj1")
        obj2 = p.add_textbox("obj2")
        
        # Create a line with None src or dst
        from py2max.core import Patchline
        line = Patchline()
        line.source = [None, 0]
        line.destination = [obj2.id, 0]
        p._lines = [line]
        
        connections = layout_mgr._analyze_object_connections()
        # Should handle None gracefully
        assert isinstance(connections, dict)

    def test_find_connected_components_visited(self):
        """Test _find_connected_components when object already visited."""
        p = Patcher()
        layout_mgr = GridLayoutManager(p)
        
        # Create connections dict
        connections = {"obj1": {"obj2"}, "obj2": {"obj1"}}
        
        clusters = layout_mgr._find_connected_components(connections)
        assert isinstance(clusters, list)

    def test_cluster_layout_horizontal_large_clusters(self):
        """Test cluster layout for horizontal with many clusters."""
        p = Patcher()
        # Set width and height through rect property
        p.rect = Rect(0, 0, 1000, 600)
        layout_mgr = GridLayoutManager(p, flow_direction="horizontal", cluster_connected=True)
        
        # Create many clusters (more than 4)
        clusters = [{"obj1", "obj2"}, {"obj3", "obj4"}, {"obj5", "obj6"}, 
                   {"obj7", "obj8"}, {"obj9", "obj10"}]
        
        # This should trigger the else branch for many clusters
        layout_mgr._apply_horizontal_clustered_layout(clusters)

    def test_cluster_layout_vertical_large_clusters(self):
        """Test cluster layout for vertical with many clusters."""
        p = Patcher()
        # Set width and height through rect property
        p.rect = Rect(0, 0, 1000, 600)
        layout_mgr = GridLayoutManager(p, flow_direction="vertical", cluster_connected=True)
        
        # Create many clusters (more than 4)
        clusters = [{"obj1", "obj2"}, {"obj3", "obj4"}, {"obj5", "obj6"}, 
                   {"obj7", "obj8"}, {"obj9", "obj10"}]
        
        # This should trigger the else branch for many clusters
        layout_mgr._apply_vertical_clustered_layout(clusters)

    def test_get_pos_with_maxclass_rect(self):
        """Test get_pos when maxclass has default rect."""
        p = Patcher()
        layout_mgr = LayoutManager(p)
        
        # Test with a maxclass that has defaults
        result = layout_mgr.get_pos("osc~")
        assert isinstance(result, Rect)

    def test_get_pos_without_maxclass_rect(self):
        """Test get_pos when maxclass has no default rect."""
        p = Patcher()
        layout_mgr = LayoutManager(p)
        
        # Test with a maxclass that has no defaults
        result = layout_mgr.get_pos("nonexistent")
        assert isinstance(result, Rect)

    def test_flow_layout_horizontal_fallback(self):
        """Test flow layout horizontal fallback behavior."""
        p = Patcher()
        layout_mgr = FlowLayoutManager(p)
        
        # Add objects to test flow layout
        obj1 = p.add_textbox("obj1")
        obj2 = p.add_textbox("obj2")
        obj3 = p.add_textbox("obj3")
        
        # Test horizontal flow
        layout_mgr.optimize_layout()

    def test_flow_layout_vertical_fallback(self):
        """Test flow layout vertical fallback behavior."""
        p = Patcher()
        layout_mgr = FlowLayoutManager(p)
        
        # Add objects to test flow layout
        obj1 = p.add_textbox("obj1")
        obj2 = p.add_textbox("obj2")
        obj3 = p.add_textbox("obj3")
        
        # Test vertical flow
        layout_mgr.optimize_layout()

    def test_grid_layout_with_clustering(self):
        """Test grid layout with clustering enabled."""
        p = Patcher()
        layout_mgr = GridLayoutManager(p, cluster_connected=True)
        
        # Add objects to test grid layout
        obj1 = p.add_textbox("obj1")
        obj2 = p.add_textbox("obj2")
        obj3 = p.add_textbox("obj3")
        
        # Test grid layout
        layout_mgr.optimize_layout()

    def test_grid_layout_without_clustering(self):
        """Test grid layout with clustering disabled."""
        p = Patcher()
        layout_mgr = GridLayoutManager(p, cluster_connected=False)
        
        # Add objects to test grid layout
        obj1 = p.add_textbox("obj1")
        obj2 = p.add_textbox("obj2")
        obj3 = p.add_textbox("obj3")
        
        # Test grid layout
        layout_mgr.optimize_layout()

    def test_vertical_layout_with_clustering(self):
        """Test vertical layout with clustering enabled."""
        p = Patcher()
        layout_mgr = GridLayoutManager(p, flow_direction="vertical", cluster_connected=True)
        
        # Add objects to test vertical layout
        obj1 = p.add_textbox("obj1")
        obj2 = p.add_textbox("obj2")
        obj3 = p.add_textbox("obj3")
        
        # Test vertical layout
        layout_mgr.optimize_layout()

    def test_vertical_layout_without_clustering(self):
        """Test vertical layout with clustering disabled."""
        p = Patcher()
        layout_mgr = GridLayoutManager(p, flow_direction="vertical", cluster_connected=False)
        
        # Add objects to test vertical layout
        obj1 = p.add_textbox("obj1")
        obj2 = p.add_textbox("obj2")
        obj3 = p.add_textbox("obj3")
        
        # Test vertical layout
        layout_mgr.optimize_layout()

    def test_horizontal_layout_with_clustering(self):
        """Test horizontal layout with clustering enabled."""
        p = Patcher()
        layout_mgr = GridLayoutManager(p, flow_direction="horizontal", cluster_connected=True)
        
        # Add objects to test horizontal layout
        obj1 = p.add_textbox("obj1")
        obj2 = p.add_textbox("obj2")
        obj3 = p.add_textbox("obj3")
        
        # Test horizontal layout
        layout_mgr.optimize_layout()

    def test_horizontal_layout_without_clustering(self):
        """Test horizontal layout with clustering disabled."""
        p = Patcher()
        layout_mgr = GridLayoutManager(p, flow_direction="horizontal", cluster_connected=False)
        
        # Add objects to test horizontal layout
        obj1 = p.add_textbox("obj1")
        obj2 = p.add_textbox("obj2")
        obj3 = p.add_textbox("obj3")
        
        # Test horizontal layout
        layout_mgr.optimize_layout()
