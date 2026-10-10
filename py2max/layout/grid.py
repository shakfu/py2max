"""Grid-based layout manager for py2max patches.

This module provides GridLayoutManager and legacy aliases for grid-based layouts.
"""

from typing import Any, Dict, List, Optional, Set

from py2max.core.abstract import AbstractPatcher
from py2max.core.common import Rect

from .base import LayoutManager, _is_anchor
from .graph import PatchGraph


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
        signal_order: bool = True,
    ):
        super().__init__(parent, pad, box_width, box_height, comment_pad)
        self.flow_direction = flow_direction  # "horizontal" or "vertical"
        self.cluster_connected = (
            cluster_connected  # Whether to cluster connected objects
        )
        self.signal_order = signal_order  # optimize_layout() sorts by signal

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

    def _full_layout(self) -> None:
        """Perform full layout optimization."""
        if not self.cluster_connected or len(self.parent._objects) < 2:
            if self.signal_order:
                self._reorder_by_signal()
            # Even without clustering, prevent overlaps
            self.prevent_overlaps()
            return

        # Analyze connections and create clusters of connected objects.
        clusters = PatchGraph(
            self.parent._lines, nodes=self.parent._objects
        ).connected_components()

        # Even single clusters can benefit from reorganization
        # Apply optimized positions to existing objects based on clusters
        self._apply_clustered_layout(clusters)

        # Prevent any remaining overlaps after clustering
        self.prevent_overlaps()

    def _signal_rank(self) -> Dict[str, int]:
        """Each box id's position in signal order (ties by creation order)."""
        ids = [b.id for b in self.parent._boxes if b.id]
        order = PatchGraph(self.parent._lines, nodes=ids).signal_order()
        return {box_id: i for i, box_id in enumerate(order)}

    def _reorder_by_signal(self) -> None:
        """Give the grid slots, in creation order, to boxes in signal order.

        Only boxes the layout placed take part; explicit and window-anchored
        rects stay. A patch built in signal order keeps every position.
        """
        parent = self.parent
        slots: Dict[str, Any] = getattr(parent, "_auto_slots", {})
        movable = [
            (b.id, b)
            for b in parent._boxes
            if b.id is not None and b.id in slots and not self._is_anchored(b.maxclass)
        ]
        if len(movable) < 2:
            return
        rank = self._signal_rank()
        ordered = sorted(movable, key=lambda m: rank[m[0]])
        if ordered == movable:
            return

        moving = {box_id for box_id, _ in movable}
        placed = [b.patching_rect for b in parent._boxes if b.id not in moving]
        for (_, box), (src_id, _) in zip(ordered, movable):
            x, y = slots[src_id]
            w, h = self.box_dims(box)
            rect = parent._clear_of_boxes(Rect(x, y, w, h), box.maxclass, placed)
            box.patching_rect = rect
            placed.append(rect)

    def _is_anchored(self, maxclass: str) -> bool:
        rect = self.get_rect_from_maxclass(maxclass)
        return bool(rect and (_is_anchor(rect.x) or _is_anchor(rect.y)))

    def _apply_clustered_layout(self, clusters: List[Set[str]]) -> None:
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

    def _apply_horizontal_clustered_layout(self, clusters: List[Set[str]]) -> None:
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

        # Use float division for consistent spacing
        cluster_width = (self.parent.width - 2 * pad) / max(cluster_cols, 1)
        cluster_height = (self.parent.height - 2 * pad) / max(cluster_rows, 1)

        # Consistent spacing between objects (use float)
        object_spacing = pad * 0.5

        # Position each cluster in its designated area
        rank = self._signal_rank() if self.signal_order else {}
        for cluster_idx, cluster_objects in enumerate(clusters):
            cluster_objects_list = sorted(
                cluster_objects, key=lambda i: (rank.get(i, 0), i)
            )

            # Calculate cluster's base position
            cluster_col = cluster_idx % cluster_cols
            cluster_row = cluster_idx // cluster_cols

            cluster_x_base = cluster_col * cluster_width + pad
            cluster_y_base = cluster_row * cluster_height + pad

            # Position objects within this cluster's designated area (horizontal priority)
            objects_per_row = max(
                1, int(cluster_width / (self.box_width + object_spacing))
            )

            for obj_idx, obj_id in enumerate(cluster_objects_list):
                if obj_id in self.parent._objects:
                    obj = self.parent._objects[obj_id]
                    if hasattr(obj, "patching_rect"):
                        # Calculate position within cluster (horizontal flow)
                        obj_col = obj_idx % objects_per_row
                        obj_row = obj_idx // objects_per_row

                        x = cluster_x_base + obj_col * (self.box_width + object_spacing)
                        y = cluster_y_base + obj_row * (
                            self.box_height + object_spacing
                        )

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

                        w, h = self.box_dims(obj)
                        obj.patching_rect = Rect(x, y, w, h)

    def _apply_vertical_clustered_layout(self, clusters: List[Set[str]]) -> None:
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

        # Use float division for consistent spacing
        cluster_width = (self.parent.width - 2 * pad) / max(cluster_cols, 1)
        cluster_height = (self.parent.height - 2 * pad) / max(cluster_rows, 1)

        # Consistent spacing between objects (use float)
        object_spacing = pad * 0.5

        # Position each cluster in its designated area
        rank = self._signal_rank() if self.signal_order else {}
        for cluster_idx, cluster_objects in enumerate(clusters):
            cluster_objects_list = sorted(
                cluster_objects, key=lambda i: (rank.get(i, 0), i)
            )

            # Calculate cluster's base position (fill vertically first)
            cluster_row = cluster_idx % cluster_rows
            cluster_col = cluster_idx // cluster_rows

            cluster_x_base = cluster_col * cluster_width + pad
            cluster_y_base = cluster_row * cluster_height + pad

            # Position objects within this cluster's designated area (vertical priority)
            objects_per_col = max(
                1, int(cluster_height / (self.box_height + object_spacing))
            )

            for obj_idx, obj_id in enumerate(cluster_objects_list):
                if obj_id in self.parent._objects:
                    obj = self.parent._objects[obj_id]
                    if hasattr(obj, "patching_rect"):
                        # Calculate position within cluster (vertical flow)
                        obj_row = obj_idx % objects_per_col
                        obj_col = obj_idx // objects_per_col

                        x = cluster_x_base + obj_col * (self.box_width + object_spacing)
                        y = cluster_y_base + obj_row * (
                            self.box_height + object_spacing
                        )

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

                        w, h = self.box_dims(obj)
                        obj.patching_rect = Rect(x, y, w, h)

    def _subdivide_large_cluster(self, cluster: Set[str]) -> List[Set[str]]:
        """Subdivide a large cluster into smaller logical groups based on object types."""
        # Group objects by type
        type_groups: Dict[str, Set[str]] = {}

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
        signal_order: bool = True,
    ):
        super().__init__(
            parent,
            pad,
            box_width,
            box_height,
            comment_pad,
            flow_direction="horizontal",
            signal_order=signal_order,
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
        signal_order: bool = True,
    ):
        super().__init__(
            parent,
            pad,
            box_width,
            box_height,
            comment_pad,
            flow_direction="vertical",
            signal_order=signal_order,
        )
