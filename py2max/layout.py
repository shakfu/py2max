"""Layout management for py2max patches.

This module provides various layout managers for automatic positioning of
Max objects in patches:

- LayoutManager: Basic horizontal layout (deprecated)
- GridLayoutManager: Grid-based layout with clustering
- FlowLayoutManager: Signal flow-based hierarchical layout
"""

from typing import Optional, Dict, List

from .abstract import AbstractLayoutManager, AbstractPatcher
from .maxref import MAXCLASS_DEFAULTS
from .common import Rect
from . import category



# ---------------------------------------------------------------------------
# Layout Classes


class LayoutManager(AbstractLayoutManager):
    """Basic horizontal layout manager.

    Provides simple left-to-right object positioning with wrapping.
    This is a legacy layout manager; consider using GridLayoutManager
    for new projects.

    Args:
        parent: The parent patcher object.
        pad: Padding between objects (default: 48.0).
        box_width: Default object width (default: 66.0).
        box_height: Default object height (default: 22.0).
        comment_pad: Padding for comments (default: 2).
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
        """Retrieve default rectangle for a Max object class.

        Args:
            maxclass: The Max object class name.

        Returns:
            Default Rect for the object class, or None if not found.
        """
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
        # Default implementation returns the same rect
        return rect

    def get_pos(self, maxclass: Optional[str] = None) -> Rect:
        """Get the next position for object placement.

        Calculates the next position for an object based on the current
        layout state and optional object class defaults.

        Args:
            maxclass: Optional Max object class for size defaults.

        Returns:
            Rect specifying the position and size for the next object.
        """
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
        self.cluster_connected = (
            cluster_connected  # Whether to cluster connected objects
        )

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
        connections: Dict[str, set] = {}  # {obj_id: set(connected_obj_ids)}

        # Initialize all objects with empty connection sets
        for obj_id in self.parent._objects:
            connections[obj_id] = set()

        # Build bidirectional connection graph
        for line in self.parent._lines:
            src_id, dst_id = line.src, line.dst
            # Skip if either ID is None
            if src_id is None or dst_id is None:
                continue
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
                cluster: set[str] = set()
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
            objects_per_row = max(1, int(cluster_width // (self.box_width + pad // 2)))

            for obj_idx, obj_id in enumerate(cluster_objects_list):
                if obj_id in self.parent._objects:
                    obj = self.parent._objects[obj_id]
                    if hasattr(obj, "patching_rect"):
                        # Calculate position within cluster (horizontal flow)
                        obj_col = obj_idx % objects_per_row
                        obj_row = obj_idx // objects_per_row

                        x = cluster_x_base + obj_col * (self.box_width + pad // 2)
                        y = cluster_y_base + obj_row * (self.box_height + pad // 2)

                        # Ensure bounds (stay within cluster area)
                        x = min(
                            max(x, cluster_x_base),
                            cluster_x_base + cluster_width - self.box_width - pad,
                        )
                        y = min(
                            max(y, cluster_y_base),
                            cluster_y_base + cluster_height - self.box_height - pad,
                        )

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
            objects_per_col = max(
                1, int(cluster_height // (self.box_height + pad // 2))
            )

            for obj_idx, obj_id in enumerate(cluster_objects_list):
                if obj_id in self.parent._objects:
                    obj = self.parent._objects[obj_id]
                    if hasattr(obj, "patching_rect"):
                        # Calculate position within cluster (vertical flow)
                        obj_row = obj_idx % objects_per_col
                        obj_col = obj_idx // objects_per_col

                        x = cluster_x_base + obj_col * (self.box_width + pad // 2)
                        y = cluster_y_base + obj_row * (self.box_height + pad // 2)

                        # Ensure bounds (stay within cluster area)
                        x = min(
                            max(x, cluster_x_base),
                            cluster_x_base + cluster_width - self.box_width - pad,
                        )
                        y = min(
                            max(y, cluster_y_base),
                            cluster_y_base + cluster_height - self.box_height - pad,
                        )

                        # Ensure overall patcher bounds
                        x = min(max(x, pad), self.parent.width - self.box_width - pad)
                        y = min(max(y, pad), self.parent.height - self.box_height - pad)

                        obj.patching_rect = Rect(x, y, self.box_width, self.box_height)

    def _subdivide_large_cluster(self, cluster: set) -> list[set]:
        """Subdivide a large cluster into smaller logical groups based on object types."""
        # Group objects by type
        type_groups: Dict[str, set[str]] = {}

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
        super().__init__(
            parent, pad, box_width, box_height, comment_pad, flow_direction="horizontal"
        )


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
        super().__init__(
            parent, pad, box_width, box_height, comment_pad, flow_direction="vertical"
        )


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
        self._object_positions: Dict[str, Rect] = {}  # Cache for calculated positions
        self._flow_levels: Dict[str, int] = {}  # Track hierarchical flow levels
        self._position_cache: Dict[
            str, Rect
        ] = {}  # Cache positions to avoid recalculation
        self.flow_direction = flow_direction  # "horizontal" or "vertical"

    def _analyze_connections(self) -> dict:
        """Analyze patchline connections to build a flow graph."""
        connections: Dict[
            str, Dict[str, List[str]]
        ] = {}  # {obj_id: {'inputs': [obj_ids], 'outputs': [obj_ids]}}

        for line in self.parent._lines:
            src_id, dst_id = line.src, line.dst

            # Skip if either ID is None
            if src_id is None or dst_id is None:
                continue

            # Initialize connection tracking
            if src_id not in connections:
                connections[src_id] = {"inputs": [], "outputs": []}
            if dst_id not in connections:
                connections[dst_id] = {"inputs": [], "outputs": []}

            # Track connections
            connections[src_id]["outputs"].append(dst_id)
            connections[dst_id]["inputs"].append(src_id)

        return connections

    def _calculate_flow_levels(self, connections: dict) -> dict:
        """Calculate hierarchical flow levels for objects based on signal chain depth."""
        levels = {}
        visited = set()

        # Find source objects (no inputs)
        sources = [obj_id for obj_id, conn in connections.items() if not conn["inputs"]]

        if not sources:
            # If no clear sources, find objects with minimal inputs
            min_inputs = (
                min(len(conn["inputs"]) for conn in connections.values())
                if connections
                else 0
            )
            sources = [
                obj_id
                for obj_id, conn in connections.items()
                if len(conn["inputs"]) == min_inputs
            ]

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
                        for output_id in connections[obj_id]["outputs"]:
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
        groups: Dict[int, List[str]] = {}
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

    def _calculate_horizontal_positions(self, groups: dict, pad: float) -> dict:
        """Calculate positions for horizontal (left-to-right) flow."""
        positions = {}
        level_width = (
            self.parent.width / max(len(groups), 1) if groups else self.parent.width
        )

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

    def _calculate_vertical_positions(self, groups: dict, pad: float) -> dict:
        """Calculate positions for vertical (top-to-bottom) flow."""
        positions = {}
        level_height = (
            self.parent.height / max(len(groups), 1) if groups else self.parent.height
        )

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

        return self._position_cache.get(
            obj_id, Rect(self.pad, self.pad, self.box_width, self.box_height)
        )

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
        existing_positions = [
            (obj.patching_rect.x, obj.patching_rect.y)
            for obj in self.parent._boxes
            if hasattr(obj, "patching_rect")
        ]

        if existing_positions:
            if self.flow_direction == "vertical":
                # Find the bottommost object and place new object below it
                max_y = max(pos[1] for pos in existing_positions)
                avg_x = sum(pos[0] for pos in existing_positions) / len(
                    existing_positions
                )

                y = max_y + self.box_height + pad
                x = avg_x

                # Wrap if we exceed height
                if y + h + pad > self.parent.height:
                    y = pad
                    x = max(pos[0] for pos in existing_positions) + self.box_width + pad
            else:
                # Find the rightmost object and place new object to its right
                max_x = max(pos[0] for pos in existing_positions)
                avg_y = sum(pos[1] for pos in existing_positions) / len(
                    existing_positions
                )

                x = max_x + self.box_width + pad
                y = avg_y

                # Wrap if we exceed width
                if x + w + pad > self.parent.width:
                    x = pad
                    y = (
                        max(pos[1] for pos in existing_positions)
                        + self.box_height
                        + pad
                    )
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


class MatrixLayoutManager(LayoutManager):
    """Unified matrix/columnar layout manager with configurable flow direction.

    This layout manager can organize objects in two different patterns based on flow_direction:

    When flow_direction="column" (Columnar Layout):
    ```
    Column 0: Controls/Inputs  | Column 1: Generators | Column 2: Processors | Column 3: Outputs
    [control0]                 | [gen0]               | [proc0]              | [output0]
    [input0]                   | [gen1]               | [proc1]              | [output1]
    [control1]                 | [gen2]               | [proc2]              | [output2]
    ```

    When flow_direction="row" (Matrix Layout):
    ```
    Row 0 (Inputs/Controls): [input0/control0] [input1/control1] [input2/control2] ...
    Row 1 (Generators):     [gen0]             [gen1]             [gen2]             ...
    Row 2 (Processors):     [proc0]            [proc1]            [proc2]            ...
    Row 3 (Outputs):        [output0]          [output1]          [output2]          ...
    ```

    In column mode, objects are grouped by functional category into vertical columns.
    In row mode, signal chains form columns while functional categories form rows.

    Args:
        parent: The parent patcher object.
        pad: Padding between objects (default: 48.0).
        box_width: Default object width (default: 66.0).
        box_height: Default object height (default: 22.0).
        comment_pad: Padding for comments (default: 2).
        flow_direction: Layout direction - "column" or "row" (default: "row").
        num_dimensions: Number of columns (in column mode) or rows (in row mode) (default: 4).
        dimension_spacing: Extra spacing between dimensions (default: 100.0).
    """

    def __init__(
        self,
        parent: AbstractPatcher,
        pad: Optional[int] = None,
        box_width: Optional[int] = None,
        box_height: Optional[int] = None,
        comment_pad: Optional[int] = None,
        flow_direction: str = "row",
        num_dimensions: int = 4,
        dimension_spacing: float = 100.0,
        # Legacy parameters for backward compatibility
        num_rows: Optional[int] = None,
        row_spacing: Optional[float] = None,
        column_spacing: Optional[float] = None,
    ):
        # Handle legacy parameters
        if num_rows is not None:
            num_dimensions = num_rows
        if row_spacing is not None:
            dimension_spacing = row_spacing
        elif column_spacing is not None:
            dimension_spacing = column_spacing

        # Initialize parent layout manager
        super().__init__(parent, pad, box_width, box_height, comment_pad)

        self.flow_direction = flow_direction
        self.num_dimensions = num_dimensions
        self.dimension_spacing = dimension_spacing

        # Legacy properties for backward compatibility
        self.num_rows = num_dimensions

        # Layout-specific properties
        self._signal_chains: List[List[str]] = []  # Each inner list is a connected signal chain (used in row mode)
        self._chain_assignments: Dict[str, int] = {}  # object_id -> chain_index (used in row mode)
        self._column_assignments: Dict[str, int] = {}  # object_id -> column/category assignment (used in both modes)

    @property
    def column_spacing(self) -> float:
        """Get column spacing (legacy property)."""
        return self.dimension_spacing

    @column_spacing.setter
    def column_spacing(self, value: float):
        """Set column spacing and update dimension_spacing (legacy property)."""
        self.dimension_spacing = value

    @property
    def row_spacing(self) -> float:
        """Get row spacing (legacy property)."""
        return self.dimension_spacing

    @row_spacing.setter
    def row_spacing(self, value: float):
        """Set row spacing and update dimension_spacing (legacy property)."""
        self.dimension_spacing = value

    def _analyze_signal_chains(self) -> List[List[str]]:
        """Analyze connections to identify separate signal chains.

        Returns:
            List of signal chains, where each chain is a list of connected object IDs.
        """
        # Build directed connection graph
        connections: Dict[str, List[str]] = {}  # obj_id -> [connected_obj_ids]
        reverse_connections: Dict[str, List[str]] = {}  # obj_id -> [objects_connecting_to_this]

        for obj_id in self.parent._objects:
            connections[obj_id] = []
            reverse_connections[obj_id] = []

        for line in self.parent._lines:
            src_id, dst_id = line.src, line.dst
            if src_id and dst_id and src_id in connections and dst_id in connections:
                connections[src_id].append(dst_id)
                reverse_connections[dst_id].append(src_id)

        # Find signal chains by tracing from sources to sinks
        visited = set()
        chains = []

        def trace_chain(start_obj: str) -> List[str]:
            """Trace a signal chain from a starting object."""
            chain = []
            current = start_obj
            chain_visited = set()

            while current and current not in chain_visited:
                if current in visited:
                    break
                chain.append(current)
                chain_visited.add(current)
                visited.add(current)

                # Find next object in chain (prefer single output connections)
                next_objects = connections.get(current, [])
                if len(next_objects) == 1:
                    current = next_objects[0]
                elif len(next_objects) > 1:
                    # Multiple outputs - choose based on object type priority
                    # Prefer continuing to processors/outputs over controls
                    next_current = None
                    for next_obj in next_objects:
                        if next_obj in self.parent._objects:
                            next_obj_category = self._classify_object(self.parent._objects[next_obj])
                            if next_obj_category >= 2:  # Processors or outputs
                                next_current = next_obj
                                break
                    current = next_current or next_objects[0]
                else:
                    current = None

            return chain

        # Start from objects with no inputs (sources) or minimal inputs
        sources = [obj_id for obj_id, inputs in reverse_connections.items() if len(inputs) <= 1]

        # If no clear sources, start from input/control objects
        if not sources:
            sources = [obj_id for obj_id, obj in self.parent._objects.items()
                      if self._classify_object(obj) == 0]  # Input/Control objects

        # Trace chains from sources
        for source in sources:
            if source not in visited:
                chain = trace_chain(source)
                if chain:
                    chains.append(chain)

        # Handle remaining unvisited objects (disconnected or in cycles)
        remaining = [obj_id for obj_id in self.parent._objects if obj_id not in visited]
        for obj_id in remaining:
            if obj_id not in visited:
                chain = trace_chain(obj_id)
                if chain:
                    chains.append(chain)
                else:
                    # Single disconnected object - create a chain with just this object
                    chains.append([obj_id])
                    visited.add(obj_id)

        return chains

    def _assign_objects_to_matrix_positions(self) -> Dict[str, tuple]:
        """Assign each object to a (row, column) position in the matrix.

        Returns:
            Dictionary mapping object_id -> (row, column) tuple.
        """
        positions = {}

        # Group objects by signal chain and category
        for chain_idx, chain in enumerate(self._signal_chains):
            # Within each chain, group by category (row)
            chain_by_category: Dict[int, List[str]] = {i: [] for i in range(self.num_rows)}

            for obj_id in chain:
                if obj_id in self.parent._objects:
                    obj = self.parent._objects[obj_id]
                    category = self._classify_object(obj)
                    category = min(category, self.num_rows - 1)  # Ensure valid row
                    chain_by_category[category].append(obj_id)
                    self._chain_assignments[obj_id] = chain_idx

            # Assign positions within this chain (column)
            for category, obj_ids in chain_by_category.items():
                for i, obj_id in enumerate(obj_ids):
                    # If multiple objects of same category in one chain, spread them slightly
                    col_offset = chain_idx + (i * 0.1)  # Small offset for multiple objects
                    positions[obj_id] = (category, col_offset)

        return positions

    def get_relative_pos(self, rect: Rect) -> Rect:
        """Returns a position based on flow_direction setting."""
        x, y, w, h = rect

        # For initial positioning during object creation, use simple grid
        # Real positioning happens in optimize_layout()
        num_created = len(self.parent._objects)

        if self.flow_direction == "column":
            # Columnar layout: cycle through columns first
            column = num_created % self.num_dimensions
            row = num_created // self.num_dimensions

            # Calculate column-based position
            column_width = (self.parent.width - self.pad * 2 - self.dimension_spacing * (self.num_dimensions - 1)) / self.num_dimensions
            x = self.pad + column * (column_width + self.dimension_spacing)
            y = self.pad + row * (self.box_height + self.pad // 2)
        else:
            # Matrix layout: cycle through rows first
            row = num_created % self.num_dimensions
            col = num_created // self.num_dimensions

            x = self.pad + col * (self.box_width + self.dimension_spacing)
            y = self.pad + row * (self.box_height + self.dimension_spacing)

        return Rect(x, y, w, h)

    def optimize_layout(self):
        """Optimize the layout based on flow_direction setting."""
        if len(self.parent._objects) < 1:
            return

        if self.flow_direction == "column":
            # Use columnar layout (functional categories as columns)
            self._optimize_columnar_layout()
        else:
            # Use matrix layout (signal chains as columns, categories as rows)
            self._optimize_matrix_layout()

    def _optimize_matrix_layout(self):
        """Optimize the layout by organizing objects into a signal chain matrix."""
        # Step 1: Classify all objects into categories
        for obj_id, obj in self.parent._objects.items():
            if obj_id not in self._column_assignments:
                self._column_assignments[obj_id] = self._classify_object(obj)

        # Step 2: Analyze signal chains
        self._signal_chains = self._analyze_signal_chains()

        # Step 3: Assign matrix positions
        matrix_positions = self._assign_objects_to_matrix_positions()

        # Step 4: Apply matrix layout
        self._apply_matrix_layout(matrix_positions)

    def _optimize_columnar_layout(self):
        """Optimize the layout by organizing objects into functional columns."""
        # Step 1: Classify all objects into columns
        for obj_id, obj in self.parent._objects.items():
            if obj_id not in self._column_assignments:
                self._column_assignments[obj_id] = self._classify_object(obj)

        # Step 2: Refine assignments based on signal flow
        self._refine_column_assignments_by_flow()

        # Step 3: Apply columnar layout
        self._apply_columnar_layout()

    def _apply_matrix_layout(self, positions: Dict[str, tuple]):
        """Apply the matrix layout to all objects.

        Args:
            positions: Dictionary mapping object_id -> (row, column) tuple.
        """
        if not positions:
            return

        # Calculate grid dimensions
        max_row = max(pos[0] for pos in positions.values()) if positions else 0
        max_col = max(pos[1] for pos in positions.values()) if positions else 0

        # Calculate spacing to fit in patcher window
        available_width = self.parent.width - 2 * self.pad
        available_height = self.parent.height - 2 * self.pad

        if max_col > 0:
            col_spacing = min(self.column_spacing, available_width / (max_col + 1))
        else:
            col_spacing = self.column_spacing

        if max_row > 0:
            row_spacing = min(self.row_spacing, available_height / (max_row + 1))
        else:
            row_spacing = self.row_spacing

        # Position each object
        for obj_id, (row, col) in positions.items():
            if obj_id in self.parent._objects:
                obj = self.parent._objects[obj_id]

                # Calculate position
                x = self.pad + col * col_spacing
                y = self.pad + row * row_spacing

                # Ensure bounds
                x = min(max(x, self.pad), self.parent.width - self.box_width - self.pad)
                y = min(max(y, self.pad), self.parent.height - self.box_height - self.pad)

                obj.patching_rect = Rect(x, y, self.box_width, self.box_height)

    def get_signal_chain_info(self) -> Dict[str, any]:
        """Get information about detected signal chains.

        Returns:
            Dictionary with signal chain analysis results.
        """
        return {
            "num_chains": len(self._signal_chains),
            "chains": self._signal_chains,
            "chain_assignments": self._chain_assignments,
            "matrix_size": (self.num_rows, len(self._signal_chains)),
        }

    def _apply_columnar_layout(self):
        """Apply the columnar layout to all objects."""
        # Group objects by column
        column_objects: Dict[int, List[str]] = {i: [] for i in range(self.num_dimensions)}

        for obj_id, column in self._column_assignments.items():
            column = min(column, self.num_dimensions - 1)  # Ensure valid column
            column_objects[column].append(obj_id)

        # Calculate column dimensions
        column_width = (self.parent.width - self.pad * 2 - self.dimension_spacing * (self.num_dimensions - 1)) / self.num_dimensions

        # Position objects within each column
        for column_idx in range(self.num_dimensions):
            objects_in_column = column_objects[column_idx]
            if not objects_in_column:
                continue

            # Calculate column base x position
            column_x = self.pad + column_idx * (column_width + self.dimension_spacing)

            # Sort objects within column by their connections to maintain flow
            objects_in_column = self._sort_objects_in_column(objects_in_column)

            # Handle horizontal replication if column has too many objects
            objects_per_column = max(1, int((self.parent.height - 2 * self.pad) / (self.box_height + self.pad // 2)))

            for i, obj_id in enumerate(objects_in_column):
                if obj_id in self.parent._objects:
                    obj = self.parent._objects[obj_id]

                    # Calculate position within column
                    sub_column = i // objects_per_column  # Horizontal replication index
                    row_in_sub_column = i % objects_per_column

                    # Calculate x position (with horizontal replication)
                    sub_column_width = column_width / max(1, (len(objects_in_column) - 1) // objects_per_column + 1)
                    x = column_x + sub_column * sub_column_width

                    # Calculate y position (top-down flow)
                    y = self.pad + row_in_sub_column * (self.box_height + self.pad // 2)

                    # Ensure bounds
                    x = min(max(x, self.pad), self.parent.width - self.box_width - self.pad)
                    y = min(max(y, self.pad), self.parent.height - self.box_height - self.pad)

                    obj.patching_rect = Rect(x, y, self.box_width, self.box_height)

    def _sort_objects_in_column(self, obj_ids: List[str]) -> List[str]:
        """Sort objects within a column to maintain logical flow order.

        Args:
            obj_ids: List of object IDs to sort.

        Returns:
            Sorted list of object IDs based on connection flow.
        """
        if not obj_ids:
            return []

        # Build simplified connection graph for this column
        connections = {}
        for obj_id in obj_ids:
            connections[obj_id] = set()

        for line in self.parent._lines:
            src, dst = line.src, line.dst
            if src in obj_ids and dst in obj_ids:
                connections[src].add(dst)

        # Topologically sort using DFS to maintain signal flow order
        visited = set()
        result = []

        def dfs(obj_id):
            if obj_id in visited:
                return
            visited.add(obj_id)

            # Visit connected objects first (deeper in signal chain)
            for connected_id in sorted(connections.get(obj_id, [])):
                dfs(connected_id)

            # Add current object after its dependencies
            result.append(obj_id)

        # Start DFS from objects with no incoming connections (sources)
        sources = [obj_id for obj_id in obj_ids
                  if not any(obj_id in connections.get(other_id, set()) for other_id in obj_ids)]

        if not sources:
            sources = obj_ids  # If no clear sources, use all objects

        for source in sources:
            dfs(source)

        # Add any remaining objects (shouldn't happen with proper DFS)
        for obj_id in obj_ids:
            if obj_id not in result:
                result.append(obj_id)

        return result

    def _classify_object(self, obj) -> int:
        """Classify an object and assign it to the appropriate column/row.

        Args:
            obj: The Box object to classify.

        Returns:
            Category index (0-3) for the object.
        """
        # Get the actual object name for classification
        if obj.maxclass == "newobj":
            text = obj._kwds.get("text", "")
            if text:
                object_name = text.split()[0] if text.split() else obj.maxclass
            else:
                object_name = obj.maxclass
        else:
            object_name = obj.maxclass

        # Check each category in order
        # Check for input objects first (they take priority over controls)
        if object_name in category.INPUT_OBJECTS:
            return 0  # Controls/Inputs category
        elif object_name in category.CONTROL_OBJECTS:
            return 0  # Controls category
        elif object_name in category.GENERATOR_OBJECTS:
            return 1  # Generators category
        elif object_name in category.PROCESSOR_OBJECTS:
            return 2  # Processors category
        elif object_name in category.OUTPUT_OBJECTS:
            return 3  # Outputs category
        else:
            # For unknown objects, try to infer from connections or name patterns
            return self._infer_column_from_context(obj, object_name)

    def _infer_column_from_context(self, obj, object_name: str) -> int:
        """Infer category assignment from object name patterns and context.

        Args:
            obj: The Box object.
            object_name: The object's name/type.

        Returns:
            Category index (0-3) for the object.
        """
        # Check specific patterns first (regardless of ~ suffix)

        # Output-like patterns (check first because they can end with ~)
        if any(out_word in object_name.lower() for out_word in
               ['out', 'dac', 'record', 'write', 'send', 'print', 'meter']):
            return 3  # Outputs

        # Input-like patterns
        if any(input_word in object_name.lower() for input_word in
               ['adc', 'in', 'inlet', 'receive', 'midiin', 'notein', 'ctlin', 'bendin', 'pgmin', 'touchin']):
            return 0  # Inputs/Controls

        # UI/control-like patterns
        if any(ctrl_word in object_name.lower() for ctrl_word in
               ['button', 'slider', 'dial', 'knob', 'fader', 'param']):
            return 0  # Controls

        # Audio objects (end with ~) are likely processors unless clearly generators
        if object_name.endswith('~'):
            # Look for generator patterns
            if any(gen_word in object_name.lower() for gen_word in
                   ['osc', 'cycle', 'saw', 'noise', 'play', 'sample']):
                return 1  # Generators
            else:
                return 2  # Processors (default for audio objects)

        # Default to processors category for unknown objects
        return 2

    def _analyze_signal_flow(self) -> Dict[str, set]:
        """Analyze signal flow to refine column assignments.

        Returns:
            Dictionary mapping object IDs to their connected object IDs.
        """
        connections: Dict[str, set] = {}

        # Initialize all objects with empty connection sets
        for obj_id in self.parent._objects:
            connections[obj_id] = set()

        # Build connection graph
        for line in self.parent._lines:
            src_id, dst_id = line.src, line.dst
            if src_id and dst_id and src_id in connections and dst_id in connections:
                connections[src_id].add(dst_id)
                connections[dst_id].add(src_id)

        return connections

    def _refine_column_assignments_by_flow(self):
        """Refine column assignments based on signal flow analysis."""
        # For now, disable flow refinement to keep objects in their initial classifications
        # The initial classification should be sufficient for most cases

        # This method can be expanded later to handle more complex refinement scenarios
        # where the initial classification might be wrong based by actual connections
        pass


