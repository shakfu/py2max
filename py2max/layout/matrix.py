"""Matrix/columnar layout manager for py2max patches.

This module provides MatrixLayoutManager for matrix and columnar-based layouts.
"""

from typing import Any, Dict, List, Optional, Set

from py2max.core.abstract import AbstractPatcher
from py2max.core.common import Rect
from py2max.maxref import category

from .base import LayoutManager


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
        self._signal_chains: List[
            List[str]
        ] = []  # Each inner list is a connected signal chain (used in row mode)
        self._chain_assignments: Dict[
            str, int
        ] = {}  # object_id -> chain_index (used in row mode)
        self._column_assignments: Dict[
            str, int
        ] = {}  # object_id -> column/category assignment (used in both modes)

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
        reverse_connections: Dict[
            str, List[str]
        ] = {}  # obj_id -> [objects_connecting_to_this]

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
            chain: List[str] = []
            current: Optional[str] = start_obj
            chain_visited: set[str] = set()

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
                    next_current: Optional[str] = None
                    for next_obj in next_objects:
                        if next_obj in self.parent._objects:
                            next_obj_category = self._classify_object(
                                self.parent._objects[next_obj]
                            )
                            if next_obj_category >= 2:  # Processors or outputs
                                next_current = next_obj
                                break
                    current = next_current or next_objects[0]
                else:
                    current = None

            return chain

        # Start from objects with no inputs (sources) or minimal inputs
        sources = [
            obj_id for obj_id, inputs in reverse_connections.items() if len(inputs) <= 1
        ]

        # If no clear sources, start from input/control objects
        if not sources:
            sources = [
                obj_id
                for obj_id, obj in self.parent._objects.items()
                if self._classify_object(obj) == 0
            ]  # Input/Control objects

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
        positions: Dict[str, tuple[int, float]] = {}

        # Group objects by signal chain and category
        for chain_idx, chain in enumerate(self._signal_chains):
            # Within each chain, group by category (row)
            chain_by_category: Dict[int, List[str]] = {
                i: [] for i in range(self.num_rows)
            }

            for obj_id in chain:
                if obj_id in self.parent._objects:
                    obj = self.parent._objects[obj_id]
                    obj_category = self._classify_object(obj)
                    obj_category = min(obj_category, self.num_rows - 1)  # Ensure valid row
                    chain_by_category[obj_category].append(obj_id)
                    self._chain_assignments[obj_id] = chain_idx

            # Assign positions within this chain (column)
            for cat, obj_ids in chain_by_category.items():
                for i, obj_id in enumerate(obj_ids):
                    # If multiple objects of same category in one chain, spread them slightly
                    col_offset = chain_idx + (
                        i * 0.1
                    )  # Small offset for multiple objects
                    positions[obj_id] = (cat, col_offset)

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
            column_width = (
                self.parent.width
                - self.pad * 2
                - self.dimension_spacing * (self.num_dimensions - 1)
            ) / self.num_dimensions
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
                y = min(
                    max(y, self.pad), self.parent.height - self.box_height - self.pad
                )

                obj.patching_rect = Rect(x, y, self.box_width, self.box_height)

    def get_signal_chain_info(self) -> Dict[str, Any]:
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
        column_objects: Dict[int, List[str]] = {
            i: [] for i in range(self.num_dimensions)
        }

        for obj_id, column in self._column_assignments.items():
            column = min(column, self.num_dimensions - 1)  # Ensure valid column
            column_objects[column].append(obj_id)

        # Calculate column dimensions
        column_width = (
            self.parent.width
            - self.pad * 2
            - self.dimension_spacing * (self.num_dimensions - 1)
        ) / self.num_dimensions

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
            objects_per_column = max(
                1,
                int(
                    (self.parent.height - 2 * self.pad)
                    / (self.box_height + self.pad // 2)
                ),
            )

            for i, obj_id in enumerate(objects_in_column):
                if obj_id in self.parent._objects:
                    obj = self.parent._objects[obj_id]

                    # Calculate position within column
                    sub_column = i // objects_per_column  # Horizontal replication index
                    row_in_sub_column = i % objects_per_column

                    # Calculate x position (with horizontal replication)
                    sub_column_width = column_width / max(
                        1, (len(objects_in_column) - 1) // objects_per_column + 1
                    )
                    x = column_x + sub_column * sub_column_width

                    # Calculate y position (top-down flow)
                    y = self.pad + row_in_sub_column * (self.box_height + self.pad // 2)

                    # Ensure bounds
                    x = min(
                        max(x, self.pad), self.parent.width - self.box_width - self.pad
                    )
                    y = min(
                        max(y, self.pad),
                        self.parent.height - self.box_height - self.pad,
                    )

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
        connections: Dict[str, Set[str]] = {}
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
        sources = [
            obj_id
            for obj_id in obj_ids
            if not any(
                obj_id in connections.get(other_id, set()) for other_id in obj_ids
            )
        ]

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
        if any(
            out_word in object_name.lower()
            for out_word in ["out", "dac", "record", "write", "send", "print", "meter"]
        ):
            return 3  # Outputs

        # Input-like patterns
        if any(
            input_word in object_name.lower()
            for input_word in [
                "adc",
                "in",
                "inlet",
                "receive",
                "midiin",
                "notein",
                "ctlin",
                "bendin",
                "pgmin",
                "touchin",
            ]
        ):
            return 0  # Inputs/Controls

        # UI/control-like patterns
        if any(
            ctrl_word in object_name.lower()
            for ctrl_word in ["button", "slider", "dial", "knob", "fader", "param"]
        ):
            return 0  # Controls

        # Audio objects (end with ~) are likely processors unless clearly generators
        if object_name.endswith("~"):
            # Look for generator patterns
            if any(
                gen_word in object_name.lower()
                for gen_word in ["osc", "cycle", "saw", "noise", "play", "sample"]
            ):
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
