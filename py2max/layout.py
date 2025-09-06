
from typing import Optional

from .abstract import AbstractLayoutManager, AbstractPatcher
from .maxref import MAXCLASS_DEFAULTS
from .common import Rect





# ---------------------------------------------------------------------------
# Layout Classes


class LayoutManager(AbstractLayoutManager):
    """Utility class to help with object layout.

    This is a basic horizontal layout manager.
    i.e. objects flow and wrap to the right.
    """

    DEFAULT_PAD = 1.5 * 32.0
    DEFAULT_BOX_WIDTH = 66.0
    DEFAULT_BOX_HEIGHT = 22.0
    DEFAULT_COMMENT_PAD = 2

    def __init__(
        self,
        parent: AbstractPatcher,
        pad: Optional[int] = None,
        box_width: Optional[int] = None,
        box_height: Optional[int] = None,
        comment_pad: Optional[int] = None,
    ):
        self.parent = parent
        self.pad = pad or self.DEFAULT_PAD
        self.box_width = box_width or self.DEFAULT_BOX_WIDTH
        self.box_height = box_height or self.DEFAULT_BOX_HEIGHT
        self.comment_pad = comment_pad or self.DEFAULT_COMMENT_PAD
        self.x_layout_counter = 0
        self.y_layout_counter = 0
        self.prior_rect = None
        self.mclass_rect = None

    def get_rect_from_maxclass(self, maxclass: str) -> Optional[Rect]:
        """retrieves default patching_rect from defaults dictionary."""
        try:
            return MAXCLASS_DEFAULTS[maxclass]["patching_rect"]
        except KeyError:
            return None

    def get_absolute_pos(self, rect: Rect) -> Rect:
        """returns an absolute position for the object"""
        x, y, w, h = rect

        pad = self.pad

        if x > 0.5 * self.parent.width:
            x1 = x - (w + pad)
            x = x1 - (x1 - self.parent.width) if x1 > self.parent.width else x1
        else:
            x1 = x + pad

        y1 = y - (h + pad)
        y = y1 - (y1 - self.parent.height) if y1 > self.parent.height else y1

        return Rect(x, y, w, h)

    def get_relative_pos(self, rect: Rect) -> Rect:
        """returns a relative position for the object"""

    def get_pos(self, maxclass: Optional[str] = None) -> Rect:
        """helper func providing very rough auto-layout of objects"""
        x = 0.0
        y = 0.0
        w = self.box_width  # 66.0
        h = self.box_height  # 22.0

        if maxclass:
            mclass_rect = self.get_rect_from_maxclass(maxclass)
            if mclass_rect and (mclass_rect.x or mclass_rect.y):
                if mclass_rect.x:
                    x = float(mclass_rect.x * self.parent.width)
                if mclass_rect.y:
                    y = float(mclass_rect.y * self.parent.height)

                _rect = Rect(x, y, mclass_rect.w, mclass_rect.h)
                return self.get_absolute_pos(_rect)

        _rect = Rect(x, y, w, h)
        return self.get_relative_pos(_rect)

    @property
    def patcher_rect(self) -> Rect:
        """return rect coordinates of the parent patcher"""
        return self.parent.rect

    def above(self, rect: Rect) -> Rect:
        """Return a position of a comment above the object"""
        x, y, w, h = rect
        return Rect(x, y - h, w, h)

    def below(self, rect: Rect) -> Rect:
        """Return a position of a comment below the object"""
        x, y, w, h = rect
        return Rect(x, y + h, w, h)

    def left(self, rect: Rect) -> Rect:
        """Return a position of a comment left of the object"""
        x, y, w, h = rect
        return Rect(x - (w + self.comment_pad), y, w, h)

    def right(self, rect: Rect) -> Rect:
        """Return a position of a comment right of the object"""
        x, y, w, h = rect
        return Rect(x + (w + self.comment_pad), y, w, h)


class GridLayoutManager(LayoutManager):
    """Utility class to help with object layout in a grid pattern.

    This layout manager supports both horizontal and vertical grid layouts:
    - Horizontal: objects fill from left to right and wrap to next row
    - Vertical: objects fill from top to bottom and wrap to next column
    """

    def __init__(
        self,
        parent: AbstractPatcher,
        pad: Optional[int] = None,
        box_width: Optional[int] = None,
        box_height: Optional[int] = None,
        comment_pad: Optional[int] = None,
        flow_direction: str = "horizontal",
        cluster_connected: bool = False,
    ):
        super().__init__(parent, pad, box_width, box_height, comment_pad)
        self.flow_direction = flow_direction  # "horizontal" or "vertical"
        self.cluster_connected = cluster_connected  # Whether to cluster connected objects

    def get_relative_pos(self, rect: Rect) -> Rect:
        """Returns a relative position for the object based on flow direction."""
        # Always use simple grid positioning during object creation
        # Clustering will be applied later via optimize_layout()
        if self.flow_direction == "vertical":
            return self._get_vertical_position(rect)
        else:
            return self._get_horizontal_position(rect)
    
    def _get_horizontal_position(self, rect: Rect) -> Rect:
        """Returns a relative horizontal position for the object.
        Objects fill from left to right and wrap horizontally.
        """
        x, y, w, h = rect
        pad = self.pad

        x_shift = 3 * pad * self.x_layout_counter
        y_shift = 1.5 * pad * self.y_layout_counter
        x = pad + x_shift

        self.x_layout_counter += 1
        if x + w + 2 * pad > self.parent.width:
            self.x_layout_counter = 0
            self.y_layout_counter += 1

        y = pad + y_shift
        return Rect(x, y, w, h)
    
    def _get_vertical_position(self, rect: Rect) -> Rect:
        """Returns a relative vertical position for the object.
        Objects fill from top to bottom and wrap vertically.
        """
        x, y, w, h = rect
        pad = self.pad

        x_shift = 3 * pad * self.x_layout_counter
        y_shift = 1.5 * pad * self.y_layout_counter
        y = pad + y_shift

        self.y_layout_counter += 1
        if y + h + 2 * pad > self.parent.height:
            self.x_layout_counter += 1
            self.y_layout_counter = 0

        x = pad + x_shift
        return Rect(x, y, w, h)
    
    def _analyze_object_connections(self) -> dict:
        """Analyze connections between objects to understand clustering patterns."""
        connections = {}  # {obj_id: set(connected_obj_ids)}
        
        # Initialize all objects with empty connection sets
        for obj_id in self.parent._objects:
            connections[obj_id] = set()
            
        # Build bidirectional connection graph
        for line in self.parent._lines:
            src_id, dst_id = line.src, line.dst
            if src_id in connections and dst_id in connections:
                connections[src_id].add(dst_id)
                connections[dst_id].add(src_id)
                
        return connections
    
    def _find_connected_components(self, connections: dict) -> list[set]:
        """Find clusters of connected objects using depth-first search."""
        visited = set()
        clusters = []
        
        def dfs(obj_id, current_cluster):
            if obj_id in visited:
                return
            visited.add(obj_id)
            current_cluster.add(obj_id)
            
            # Visit all connected objects
            for connected_id in connections.get(obj_id, set()):
                if connected_id not in visited:
                    dfs(connected_id, current_cluster)
        
        # Find all connected components
        for obj_id in connections:
            if obj_id not in visited:
                cluster = set()
                dfs(obj_id, cluster)
                if cluster:  # Only add non-empty clusters
                    clusters.append(cluster)
        
        return clusters
    
    
    def optimize_layout(self):
        """Optimize the layout to cluster connected objects together."""
        if not self.cluster_connected or len(self.parent._objects) < 2:
            return  # Nothing to optimize
            
        # Analyze connections and create clusters
        connections = self._analyze_object_connections()
        clusters = self._find_connected_components(connections)
        
        # Even single clusters can benefit from reorganization
        # Apply optimized positions to existing objects based on clusters
        self._apply_clustered_layout(clusters)
    
    def _apply_clustered_layout(self, clusters: list[set]):
        """Apply cluster-based positioning to all objects."""
        # pad = self.pad
        
        # If there's only one large cluster, try to create sub-clusters based on object types
        if len(clusters) == 1 and len(clusters[0]) > 6:
            clusters = self._subdivide_large_cluster(clusters[0])
        
        # Sort clusters by size (largest first) for better space utilization
        clusters = sorted(clusters, key=len, reverse=True)
        
        # Use flow_direction to determine cluster arrangement
        if self.flow_direction == "vertical":
            self._apply_vertical_clustered_layout(clusters)
        else:
            self._apply_horizontal_clustered_layout(clusters)
    
    def _apply_horizontal_clustered_layout(self, clusters: list[set]):
        """Apply horizontal cluster-based positioning (clusters arranged left-to-right)."""
        pad = self.pad
        num_clusters = len(clusters)
        
        # Calculate cluster layout for horizontal arrangement
        if num_clusters <= 2:
            cluster_cols = num_clusters
            cluster_rows = 1
        elif num_clusters <= 4:
            cluster_cols = 2
            cluster_rows = 2
        else:
            cluster_cols = min(3, num_clusters)
            cluster_rows = (num_clusters + cluster_cols - 1) // cluster_cols
        
        cluster_width = (self.parent.width - pad) // cluster_cols
        cluster_height = (self.parent.height - pad) // cluster_rows
        
        # Position each cluster in its designated area
        for cluster_idx, cluster_objects in enumerate(clusters):
            cluster_objects_list = sorted(list(cluster_objects))  # Consistent ordering
            
            # Calculate cluster's base position
            cluster_col = cluster_idx % cluster_cols
            cluster_row = cluster_idx // cluster_cols
            
            cluster_x_base = cluster_col * cluster_width + pad
            cluster_y_base = cluster_row * cluster_height + pad
            
            # Position objects within this cluster's designated area (horizontal priority)
            objects_per_row = max(1, int(cluster_width // (self.box_width + pad//2)))
            
            for obj_idx, obj_id in enumerate(cluster_objects_list):
                if obj_id in self.parent._objects:
                    obj = self.parent._objects[obj_id]
                    if hasattr(obj, 'patching_rect'):
                        # Calculate position within cluster (horizontal flow)
                        obj_col = obj_idx % objects_per_row
                        obj_row = obj_idx // objects_per_row
                        
                        x = cluster_x_base + obj_col * (self.box_width + pad//2)
                        y = cluster_y_base + obj_row * (self.box_height + pad//2)
                        
                        # Ensure bounds (stay within cluster area)
                        x = min(max(x, cluster_x_base), 
                               cluster_x_base + cluster_width - self.box_width - pad)
                        y = min(max(y, cluster_y_base),
                               cluster_y_base + cluster_height - self.box_height - pad)
                        
                        # Ensure overall patcher bounds
                        x = min(max(x, pad), self.parent.width - self.box_width - pad)
                        y = min(max(y, pad), self.parent.height - self.box_height - pad)
                        
                        obj.patching_rect = Rect(x, y, self.box_width, self.box_height)
    
    def _apply_vertical_clustered_layout(self, clusters: list[set]):
        """Apply vertical cluster-based positioning (clusters arranged top-to-bottom)."""
        pad = self.pad
        num_clusters = len(clusters)
        
        # Calculate cluster layout for vertical arrangement (prefer vertical stacking)
        if num_clusters <= 2:
            cluster_cols = 1
            cluster_rows = num_clusters
        elif num_clusters <= 4:
            cluster_cols = 2
            cluster_rows = 2  
        else:
            cluster_rows = min(3, num_clusters)
            cluster_cols = (num_clusters + cluster_rows - 1) // cluster_rows
        
        cluster_width = (self.parent.width - pad) // cluster_cols
        cluster_height = (self.parent.height - pad) // cluster_rows
        
        # Position each cluster in its designated area
        for cluster_idx, cluster_objects in enumerate(clusters):
            cluster_objects_list = sorted(list(cluster_objects))  # Consistent ordering
            
            # Calculate cluster's base position (fill vertically first)
            cluster_row = cluster_idx % cluster_rows
            cluster_col = cluster_idx // cluster_rows
            
            cluster_x_base = cluster_col * cluster_width + pad
            cluster_y_base = cluster_row * cluster_height + pad
            
            # Position objects within this cluster's designated area (vertical priority)
            objects_per_col = max(1, int(cluster_height // (self.box_height + pad//2)))
            
            for obj_idx, obj_id in enumerate(cluster_objects_list):
                if obj_id in self.parent._objects:
                    obj = self.parent._objects[obj_id]
                    if hasattr(obj, 'patching_rect'):
                        # Calculate position within cluster (vertical flow)
                        obj_row = obj_idx % objects_per_col
                        obj_col = obj_idx // objects_per_col
                        
                        x = cluster_x_base + obj_col * (self.box_width + pad//2)
                        y = cluster_y_base + obj_row * (self.box_height + pad//2)
                        
                        # Ensure bounds (stay within cluster area)
                        x = min(max(x, cluster_x_base), 
                               cluster_x_base + cluster_width - self.box_width - pad)
                        y = min(max(y, cluster_y_base),
                               cluster_y_base + cluster_height - self.box_height - pad)
                        
                        # Ensure overall patcher bounds
                        x = min(max(x, pad), self.parent.width - self.box_width - pad)
                        y = min(max(y, pad), self.parent.height - self.box_height - pad)
                        
                        obj.patching_rect = Rect(x, y, self.box_width, self.box_height)
    
    def _subdivide_large_cluster(self, cluster: set) -> list[set]:
        """Subdivide a large cluster into smaller logical groups based on object types."""
        # Group objects by type
        type_groups = {}
        
        for obj_id in cluster:
            obj = self.parent._objects.get(obj_id)
            if obj:
                # Group by maxclass
                obj_type = obj.maxclass
                if obj_type not in type_groups:
                    type_groups[obj_type] = set()
                type_groups[obj_type].add(obj_id)
        
        # Convert type groups to clusters, combining small ones
        subclusters = []
        small_cluster = set()
        
        for obj_type, obj_set in type_groups.items():
            if len(obj_set) >= 3:  # Large enough to be its own cluster
                subclusters.append(obj_set)
            else:  # Too small, add to combined cluster
                small_cluster.update(obj_set)
        
        # Add the small objects cluster if it exists
        if small_cluster:
            subclusters.append(small_cluster)
        
        # If we didn't create meaningful subdivisions, return original cluster
        return subclusters if len(subclusters) > 1 else [cluster]


# Legacy aliases for backward compatibility
class HorizontalLayoutManager(GridLayoutManager):
    """Legacy horizontal layout manager. Use GridLayoutManager with flow_direction="horizontal" instead."""
    
    def __init__(
        self,
        parent: AbstractPatcher,
        pad: Optional[int] = None,
        box_width: Optional[int] = None,
        box_height: Optional[int] = None,
        comment_pad: Optional[int] = None,
    ):
        super().__init__(parent, pad, box_width, box_height, comment_pad, flow_direction="horizontal")


class VerticalLayoutManager(GridLayoutManager):
    """Legacy vertical layout manager. Use GridLayoutManager with flow_direction="vertical" instead."""
    
    def __init__(
        self,
        parent: AbstractPatcher,
        pad: Optional[int] = None,
        box_width: Optional[int] = None,
        box_height: Optional[int] = None,
        comment_pad: Optional[int] = None,
    ):
        super().__init__(parent, pad, box_width, box_height, comment_pad, flow_direction="vertical")


class FlowLayoutManager(LayoutManager):
    """Advanced layout manager that analyzes signal flow topology.
    
    This layout manager:
    - Analyzes patchline connections to understand signal flow
    - Groups related objects based on connection patterns  
    - Uses hierarchical positioning with signal flow left-to-right or top-to-bottom
    - Minimizes line crossings and connection distances
    - Balances layout aesthetically while respecting functional relationships
    """

    def __init__(
        self,
        parent: AbstractPatcher,
        pad: Optional[int] = None,
        box_width: Optional[int] = None,
        box_height: Optional[int] = None,
        comment_pad: Optional[int] = None,
        flow_direction: str = "horizontal",
    ):
        super().__init__(parent, pad, box_width, box_height, comment_pad)
        self._object_positions = {}  # Cache for calculated positions
        self._flow_levels = {}  # Track hierarchical flow levels
        self._position_cache = {}  # Cache positions to avoid recalculation
        self.flow_direction = flow_direction  # "horizontal" or "vertical"
        
    def _analyze_connections(self) -> dict:
        """Analyze patchline connections to build a flow graph."""
        connections = {}  # {obj_id: {'inputs': [obj_ids], 'outputs': [obj_ids]}}
        
        for line in self.parent._lines:
            src_id, dst_id = line.src, line.dst
            
            # Initialize connection tracking
            if src_id not in connections:
                connections[src_id] = {'inputs': [], 'outputs': []}
            if dst_id not in connections:
                connections[dst_id] = {'inputs': [], 'outputs': []}
                
            # Track connections
            connections[src_id]['outputs'].append(dst_id)
            connections[dst_id]['inputs'].append(src_id)
            
        return connections
    
    def _calculate_flow_levels(self, connections: dict) -> dict:
        """Calculate hierarchical flow levels for objects based on signal chain depth."""
        levels = {}
        visited = set()
        
        # Find source objects (no inputs)
        sources = [obj_id for obj_id, conn in connections.items() 
                  if not conn['inputs']]
        
        if not sources:
            # If no clear sources, find objects with minimal inputs
            min_inputs = min(len(conn['inputs']) for conn in connections.values()) if connections else 0
            sources = [obj_id for obj_id, conn in connections.items() 
                      if len(conn['inputs']) == min_inputs]
        
        # Assign levels using BFS-like traversal
        current_level = 0
        current_objects = sources
        
        while current_objects:
            next_objects = []
            for obj_id in current_objects:
                if obj_id not in visited:
                    levels[obj_id] = current_level
                    visited.add(obj_id)
                    
                    # Add outputs to next level
                    if obj_id in connections:
                        for output_id in connections[obj_id]['outputs']:
                            if output_id not in visited:
                                next_objects.append(output_id)
            
            current_objects = list(set(next_objects))
            current_level += 1
            
        # Handle disconnected objects
        for obj_id in self.parent._objects:
            if obj_id not in levels:
                levels[obj_id] = current_level
                
        return levels
    
    def _group_by_level(self, levels: dict) -> dict:
        """Group objects by their flow level."""
        groups = {}
        for obj_id, level in levels.items():
            if level not in groups:
                groups[level] = []
            groups[level].append(obj_id)
        return groups
    
    def _calculate_positions(self) -> dict:
        """Calculate optimized positions for all objects."""
        connections = self._analyze_connections()
        levels = self._calculate_flow_levels(connections)
        groups = self._group_by_level(levels)
        
        # positions = {}
        pad = self.pad
        
        if self.flow_direction == "vertical":
            return self._calculate_vertical_positions(groups, pad)
        else:
            return self._calculate_horizontal_positions(groups, pad)
    
    def _calculate_horizontal_positions(self, groups: dict, pad: int) -> dict:
        """Calculate positions for horizontal (left-to-right) flow."""
        positions = {}
        level_width = self.parent.width / max(len(groups), 1) if groups else self.parent.width
        
        for level, obj_ids in groups.items():
            # Calculate x position based on level (left-to-right flow)
            x_base = pad + (level * level_width * 0.8)  # 0.8 factor for better spacing
            
            # Calculate y positions for objects in this level
            level_height = len(obj_ids) * (self.box_height + pad)
            y_start = (self.parent.height - level_height) / 2  # Center vertically
            
            for i, obj_id in enumerate(obj_ids):
                x = x_base
                y = max(pad, y_start + i * (self.box_height + pad))
                
                # Ensure positions stay within bounds
                x = min(x, self.parent.width - self.box_width - pad)
                y = min(y, self.parent.height - self.box_height - pad)
                
                positions[obj_id] = Rect(x, y, self.box_width, self.box_height)
        
        return positions
    
    def _calculate_vertical_positions(self, groups: dict, pad: int) -> dict:
        """Calculate positions for vertical (top-to-bottom) flow."""
        positions = {}
        level_height = self.parent.height / max(len(groups), 1) if groups else self.parent.height
        
        for level, obj_ids in groups.items():
            # Calculate y position based on level (top-to-bottom flow)
            y_base = pad + (level * level_height * 0.8)  # 0.8 factor for better spacing
            
            # Calculate x positions for objects in this level
            level_width = len(obj_ids) * (self.box_width + pad)
            x_start = (self.parent.width - level_width) / 2  # Center horizontally
            
            for i, obj_id in enumerate(obj_ids):
                y = y_base
                x = max(pad, x_start + i * (self.box_width + pad))
                
                # Ensure positions stay within bounds
                x = min(x, self.parent.width - self.box_width - pad)
                y = min(y, self.parent.height - self.box_height - pad)
                
                positions[obj_id] = Rect(x, y, self.box_width, self.box_height)
        
        return positions
    
    def _get_object_position(self, obj_id: str) -> Rect:
        """Get the calculated position for a specific object."""
        if not self._position_cache:
            self._position_cache = self._calculate_positions()
            
        return self._position_cache.get(obj_id, 
                                       Rect(self.pad, self.pad, self.box_width, self.box_height))
    
    def get_relative_pos(self, rect: Rect) -> Rect:
        """Returns a flow-optimized position for the object."""
        x, y, w, h = rect
        
        # If we don't have enough information yet, fall back to simple grid
        if len(self.parent._objects) <= 1:
            pad = self.pad
            x_shift = 3 * pad * self.x_layout_counter
            y_shift = 1.5 * pad * self.y_layout_counter
            x = pad + x_shift
            y = pad + y_shift
            
            self.x_layout_counter += 1
            if x + w + 2 * pad > self.parent.width:
                self.x_layout_counter = 0
                self.y_layout_counter += 1
            
            return Rect(x, y, w, h)
        
        # For objects added after initial layout, try to maintain flow
        # This is a simplified approach - in practice we'd want to recalculate
        # the entire layout when significant changes occur
        return self._get_next_flow_position(rect)
    
    def _get_next_flow_position(self, rect: Rect) -> Rect:
        """Calculate next position maintaining flow principles."""
        x, y, w, h = rect
        pad = self.pad
        
        # Try to find a good position based on existing objects
        existing_positions = [(obj.patching_rect.x, obj.patching_rect.y) 
                             for obj in self.parent._boxes 
                             if hasattr(obj, 'patching_rect')]
        
        if existing_positions:
            if self.flow_direction == "vertical":
                # Find the bottommost object and place new object below it
                max_y = max(pos[1] for pos in existing_positions)
                avg_x = sum(pos[0] for pos in existing_positions) / len(existing_positions)
                
                y = max_y + self.box_height + pad
                x = avg_x
                
                # Wrap if we exceed height
                if y + h + pad > self.parent.height:
                    y = pad
                    x = max(pos[0] for pos in existing_positions) + self.box_width + pad
            else:
                # Find the rightmost object and place new object to its right
                max_x = max(pos[0] for pos in existing_positions)
                avg_y = sum(pos[1] for pos in existing_positions) / len(existing_positions)
                
                x = max_x + self.box_width + pad
                y = avg_y
                
                # Wrap if we exceed width
                if x + w + pad > self.parent.width:
                    x = pad
                    y = max(pos[1] for pos in existing_positions) + self.box_height + pad
        else:
            # First object - place at standard starting position
            x = pad
            y = pad
            
        # Ensure positions stay within bounds
        x = min(max(x, pad), self.parent.width - w - pad)
        y = min(max(y, pad), self.parent.height - h - pad)
        
        return Rect(x, y, w, h)
    
    def optimize_layout(self):
        """Optimize the layout of all existing objects based on their connections."""
        if len(self.parent._objects) < 2:
            return  # Nothing to optimize
            
        positions = self._calculate_positions()
        
        # Apply optimized positions to existing objects
        for obj_id, position in positions.items():
            if obj_id in self.parent._objects:
                self.parent._objects[obj_id].patching_rect = position
                
        # Clear cache so future positions use the optimized layout
        self._position_cache = positions
