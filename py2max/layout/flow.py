"""Signal flow-based layout manager for py2max patches.

This module provides FlowLayoutManager for intelligent signal flow-based layouts.
"""

from typing import Dict, List, Optional

from py2max.core.abstract import AbstractPatcher
from py2max.core.common import Rect

from .base import LayoutManager


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
        num_levels = max(len(groups), 1)

        # Calculate available width per level
        available_width = self.parent.width - 2 * pad
        level_width = available_width / num_levels if groups else self.parent.width

        for level, obj_ids in groups.items():
            # Calculate x position based on level (left-to-right flow)
            x_base = pad + (level * level_width * 0.8)  # 0.8 factor for better spacing

            # Calculate y positions for objects in this level
            num_objects = len(obj_ids)
            level_height = num_objects * (self.box_height + pad)

            # Ensure y_start doesn't go negative - clamp to pad minimum
            available_height = self.parent.height - 2 * pad
            if level_height > available_height:
                # Scale down spacing if too many objects
                spacing = available_height / max(num_objects, 1)
                y_start = pad
            else:
                spacing = self.box_height + pad
                y_start = max(pad, (self.parent.height - level_height) / 2)

            for i, obj_id in enumerate(obj_ids):
                x = x_base
                y = y_start + i * spacing

                # Ensure positions stay within bounds
                x = max(pad, min(x, self.parent.width - self.box_width - pad))
                y = max(pad, min(y, self.parent.height - self.box_height - pad))

                positions[obj_id] = Rect(x, y, self.box_width, self.box_height)

        return positions

    def _calculate_vertical_positions(self, groups: dict, pad: float) -> dict:
        """Calculate positions for vertical (top-to-bottom) flow."""
        positions = {}
        num_levels = max(len(groups), 1)

        # Calculate available height per level
        available_height = self.parent.height - 2 * pad
        level_height = available_height / num_levels if groups else self.parent.height

        for level, obj_ids in groups.items():
            # Calculate y position based on level (top-to-bottom flow)
            y_base = pad + (level * level_height * 0.8)  # 0.8 factor for better spacing

            # Calculate x positions for objects in this level
            num_objects = len(obj_ids)
            level_width = num_objects * (self.box_width + pad)

            # Ensure x_start doesn't go negative - clamp to pad minimum
            available_width = self.parent.width - 2 * pad
            if level_width > available_width:
                # Scale down spacing if too many objects
                spacing = available_width / max(num_objects, 1)
                x_start = pad
            else:
                spacing = self.box_width + pad
                x_start = max(pad, (self.parent.width - level_width) / 2)

            for i, obj_id in enumerate(obj_ids):
                y = y_base
                x = x_start + i * spacing

                # Ensure positions stay within bounds
                x = max(pad, min(x, self.parent.width - self.box_width - pad))
                y = max(pad, min(y, self.parent.height - self.box_height - pad))

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

        # Prevent any remaining overlaps after flow layout
        self.prevent_overlaps()

        # Clear cache so future positions use the optimized layout
        self._position_cache = positions
