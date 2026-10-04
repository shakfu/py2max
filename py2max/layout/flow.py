"""Signal flow-based layout manager for py2max patches.

This module provides FlowLayoutManager for intelligent signal flow-based layouts.
"""

from typing import Dict, List, Optional, Set, Tuple

from py2max.core.abstract import AbstractPatcher
from py2max.core.common import Rect

from py2max.utils import object_name

from .base import LayoutManager
from .graph import PatchGraph


# objects that take audio or data out of a patch, laid out last
_PATCH_OUTPUTS = frozenset(
    {"dac~", "ezdac~", "mc.dac~", "mc.ezdac~", "outlet", "out~", "outport"}
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
        self._flow_levels: Dict[str, int] = {}  # Track hierarchical flow levels
        self.flow_direction = flow_direction  # "horizontal" or "vertical"

    def _analyze_connections(self) -> Dict[str, Dict[str, List[str]]]:
        """Analyze patchline connections to build a flow graph.

        Keys are the connected objects only (disconnected boxes are not seeded),
        in first-appearance order, matching the historical behaviour.
        """
        return PatchGraph(self.parent._lines).io_lists()

    def _calculate_flow_levels(
        self, connections: Dict[str, Dict[str, List[str]]]
    ) -> Dict[str, int]:
        """Level per object along the flow.

        Vertical flow uses longest-path levels: each object sits one below its
        deepest input, so every cord points down (feedback cycles are broken
        by ignoring the cords that close them). Patch outputs (``dac~``,
        ``outlet``, ...) with no outgoing cords then go on the last level.
        Horizontal flow keeps shortest-path levels: Max draws cords from a
        box's bottom edge to the next one's top, so in a left-to-right layout
        the extra levels doubled the crossings. Unconnected objects follow on
        a level of their own.
        """
        if self.flow_direction == "vertical":
            levels = self._longest_path_levels(connections)
        else:
            levels = self._shortest_path_levels(connections)

        last = max(levels.values(), default=0)
        if self.flow_direction == "vertical":
            for obj_id in levels:
                obj = self.parent._objects.get(obj_id)
                if (
                    obj is not None
                    and object_name(obj) in _PATCH_OUTPUTS
                    and not connections[obj_id]["outputs"]
                ):
                    levels[obj_id] = last

        for obj_id in self.parent._objects:
            if obj_id not in levels:
                levels[obj_id] = last + 1
        return levels

    def _longest_path_levels(
        self, connections: Dict[str, Dict[str, List[str]]]
    ) -> Dict[str, int]:
        back = self._back_edges(connections)
        indegree = {
            o: sum(1 for i in c["inputs"] if (i, o) not in back)
            for o, c in connections.items()
        }
        levels = {o: 0 for o, n in indegree.items() if n == 0}
        ready = sorted(levels)
        while ready:
            node = ready.pop()
            for out in connections[node]["outputs"]:
                if (node, out) in back:
                    continue
                levels[out] = max(levels.get(out, 0), levels[node] + 1)
                indegree[out] -= 1
                if indegree[out] == 0:
                    ready.append(out)
        return levels

    @staticmethod
    def _shortest_path_levels(
        connections: Dict[str, Dict[str, List[str]]],
    ) -> Dict[str, int]:
        sources = [o for o, c in connections.items() if not c["inputs"]]
        if not sources and connections:
            fewest = min(len(c["inputs"]) for c in connections.values())
            sources = [o for o, c in connections.items() if len(c["inputs"]) == fewest]
        levels: Dict[str, int] = {}
        frontier, level = sources, 0
        while frontier:
            nxt: List[str] = []
            for obj_id in frontier:
                if obj_id not in levels:
                    levels[obj_id] = level
                    nxt.extend(
                        o for o in connections[obj_id]["outputs"] if o not in levels
                    )
            frontier, level = sorted(set(nxt)), level + 1
        return levels

    @staticmethod
    def _back_edges(
        connections: Dict[str, Dict[str, List[str]]],
    ) -> Set[Tuple[str, str]]:
        """Cords that close a cycle, found by depth-first search."""
        back: Set[Tuple[str, str]] = set()
        state: Dict[str, int] = {}  # 1 on the current path, 2 finished
        for root in connections:
            if root in state:
                continue
            stack = [(root, iter(connections[root]["outputs"]))]
            state[root] = 1
            while stack:
                node, outs = stack[-1]
                nxt = next(outs, None)
                if nxt is None:
                    state[node] = 2
                    stack.pop()
                elif state.get(nxt) == 1:
                    back.add((node, nxt))
                elif nxt not in state and nxt in connections:
                    state[nxt] = 1
                    stack.append((nxt, iter(connections[nxt]["outputs"])))
        return back

    def _group_by_level(self, levels: Dict[str, int]) -> Dict[int, List[str]]:
        """Group objects by their flow level."""
        groups: Dict[int, List[str]] = {}
        for obj_id, level in levels.items():
            if level not in groups:
                groups[level] = []
            groups[level].append(obj_id)
        return groups

    def _minimize_crossings(
        self,
        groups: Dict[int, List[str]],
        connections: Dict[str, Dict[str, List[str]]],
        sweeps: int = 8,
    ) -> List[Dict[int, List[str]]]:
        """Candidate orderings of each level, for ``_full_layout`` to judge.

        Each connected component keeps a contiguous block within a level, so
        independent subgraphs do not interleave. Within that, barycenter sweeps
        alternate down (by inputs) and up (by outputs), placing each object at
        the mean relative position of its neighbours on any level. The ordering
        with the fewest estimated crossings is kept. The original single
        downward pass is included, so the chosen layout is never worse than it.
        """
        if len(groups) < 2:
            return [groups]

        levels = sorted(groups)
        component = self._components(connections)
        candidates = [self._barycenter_once(groups, connections)]
        # with components kept apart, and without
        for blocked in (True, False):
            group = component if blocked else {}
            seed = {
                lv: sorted(groups[lv], key=lambda o: (group.get(o, 0), o))
                for lv in levels
            }
            candidates.append(self._sweep(seed, levels, connections, group, sweeps)[0])
        return candidates

    def _barycenter_once(
        self,
        groups: Dict[int, List[str]],
        connections: Dict[str, Dict[str, List[str]]],
    ) -> Dict[int, List[str]]:
        """One downward barycenter pass by previous-level inputs (the original).

        For each level (after the first), objects are reordered based on
        the average position (barycenter) of their connected objects in
        the previous level. This tends to place connected objects near
        each other, reducing line crossings.

        Args:
            groups: Objects grouped by level
            connections: Connection graph from _analyze_connections()

        Returns:
            Reordered groups with minimized crossings
        """
        if len(groups) < 2:
            return groups

        sorted_levels = sorted(groups.keys())
        result: Dict[int, List[str]] = {}

        # First level stays as-is (sorted for consistency)
        first_level = sorted_levels[0]
        result[first_level] = sorted(groups[first_level])

        # Process subsequent levels
        for i, level in enumerate(sorted_levels[1:], 1):
            prev_level = sorted_levels[i - 1]
            prev_objects = result[prev_level]
            current_objects = groups[level]

            # Create position map for previous level objects
            prev_positions = {obj_id: idx for idx, obj_id in enumerate(prev_objects)}

            # Calculate barycenter for each object in current level
            barycenters: Dict[str, float] = {}
            for obj_id in current_objects:
                # Find all connections to previous level
                connected_positions = []

                # Check inputs (connections from previous level)
                if obj_id in connections:
                    for input_id in connections[obj_id]["inputs"]:
                        if input_id in prev_positions:
                            connected_positions.append(prev_positions[input_id])

                if connected_positions:
                    # Barycenter is the average position of connected objects
                    barycenters[obj_id] = sum(connected_positions) / len(
                        connected_positions
                    )
                else:
                    # No connections to previous level - use a large value to push to end
                    barycenters[obj_id] = float("inf")

            # Sort objects by their barycenter values
            sorted_objects = sorted(
                current_objects,
                key=lambda obj_id: (
                    barycenters[obj_id],
                    obj_id,
                ),  # obj_id as tiebreaker
            )
            result[level] = sorted_objects

        return result

    def _sweep(
        self,
        order: Dict[int, List[str]],
        levels: List[int],
        connections: Dict[str, Dict[str, List[str]]],
        component: Dict[str, int],
        sweeps: int,
    ) -> Tuple[Dict[int, List[str]], int]:
        """Barycenter sweeps from ``order``: the best ordering seen, and its cost."""
        best = {lv: list(ids) for lv, ids in order.items()}
        best_cost = self._count_crossings(best, levels, connections)

        for sweep in range(sweeps):
            down = sweep % 2 == 0
            neighbours = "inputs" if down else "outputs"
            for lv in levels[1:] if down else levels[-2::-1]:
                rel = {
                    o: idx / max(len(ids) - 1, 1)
                    for ids in order.values()
                    for idx, o in enumerate(ids)
                }
                current = {o: idx for idx, o in enumerate(order[lv])}

                def key(o: str) -> Tuple[int, float, int]:
                    near = [
                        rel[n]
                        for n in connections.get(o, {}).get(neighbours, [])
                        if n in rel
                    ]
                    bary = sum(near) / len(near) if near else rel[o]
                    return (component.get(o, 0), bary, current[o])

                order[lv] = sorted(order[lv], key=key)
            cost = self._count_crossings(order, levels, connections)
            if cost < best_cost:
                best, best_cost = {lv: list(ids) for lv, ids in order.items()}, cost
        return best, best_cost

    @staticmethod
    def _components(connections: Dict[str, Dict[str, List[str]]]) -> Dict[str, int]:
        """Connected-component index per object, numbered in first-seen order."""
        component: Dict[str, int] = {}
        for start in connections:
            if start in component:
                continue
            index, stack = len(set(component.values())), [start]
            while stack:
                node = stack.pop()
                if node in component:
                    continue
                component[node] = index
                conn = connections.get(node, {})
                stack.extend(conn.get("inputs", []) + conn.get("outputs", []))
        return component

    def _count_crossings(
        self,
        order: Dict[int, List[str]],
        levels: List[int],
        connections: Dict[str, Dict[str, List[str]]],
    ) -> int:
        """Cord crossings if objects were placed in ``order``.

        Uses the positions this manager would assign, and Max's cord geometry
        (outlet on the bottom edge to inlet on the top edge), so the count is
        right for both flow directions and for cords spanning several levels.
        """
        if self.flow_direction == "vertical":
            rects = self._calculate_vertical_positions(order, self.pad)
        else:
            rects = self._calculate_horizontal_positions(order, self.pad)
        segs = [
            (
                (rects[o][0] + rects[o][2] / 2, rects[o][1] + rects[o][3]),
                (rects[d][0] + rects[d][2] / 2, rects[d][1]),
                o,
                d,
            )
            for o in rects
            for d in connections.get(o, {}).get("outputs", [])
            if d in rects
        ]
        return _count_segment_crossings(segs)

    def _candidate_positions(self) -> List[Dict[str, Rect]]:
        """Positions for each candidate ordering of the flow levels."""
        connections = self._analyze_connections()
        levels = self._calculate_flow_levels(connections)
        groups = self._group_by_level(levels)
        place = (
            self._calculate_vertical_positions
            if self.flow_direction == "vertical"
            else self._calculate_horizontal_positions
        )
        return [
            place(order, self.pad)
            for order in self._minimize_crossings(groups, connections)
        ]

    def _calculate_horizontal_positions(
        self, groups: Dict[int, List[str]], pad: float
    ) -> Dict[str, Rect]:
        """Positions for left-to-right flow: one column per level."""
        return self._place_levels(groups, pad, along=0)

    def _calculate_vertical_positions(
        self, groups: Dict[int, List[str]], pad: float
    ) -> Dict[str, Rect]:
        """Positions for top-to-bottom flow: one row per level."""
        return self._place_levels(groups, pad, along=1)

    def _place_levels(
        self, groups: Dict[int, List[str]], pad: float, along: int
    ) -> Dict[str, Rect]:
        """Lay levels out along axis ``along`` (0 = x, 1 = y), sized by their boxes.

        Each level is as deep as its largest box, and its boxes stack across
        the other axis by their real sizes, centred in the window when they
        fit. Spare window space spreads the levels, up to 100 px apart. Nothing
        is clamped to the window: ``optimize_layout`` grows it to fit.
        """
        across = 1 - along
        window = (float(self.parent.width), float(self.parent.height))

        def dims(obj_id: str) -> Tuple[float, float]:
            obj = self.parent._objects.get(obj_id)
            return (
                self.box_dims(obj)
                if obj is not None
                else (
                    float(self.box_width),
                    float(self.box_height),
                )
            )

        levels = sorted(groups)
        depth = {
            lv: max((dims(o)[along] for o in groups[lv]), default=0.0) for lv in levels
        }
        spare = window[along] - 2 * pad - sum(depth.values())
        gap = max(pad, min(spare / max(len(levels) - 1, 1), 100.0))

        positions: Dict[str, Rect] = {}
        offset = pad
        for lv in levels:
            sizes = [dims(o) for o in groups[lv]]
            extent = sum(sz[across] for sz in sizes) + pad * (len(sizes) - 1)
            start = max(pad, (window[across] - extent) / 2)
            for obj_id, (w, h) in zip(groups[lv], sizes):
                xy = [0.0, 0.0]
                xy[along], xy[across] = offset, start
                positions[obj_id] = Rect(xy[0], xy[1], w, h)
                start += (w, h)[across] + pad
            offset += depth[lv] + gap
        return positions

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

    def _place(self, positions: Dict[str, Rect]) -> None:
        """Apply ``positions``, keeping each object's own size, then de-overlap.

        The computed position carries the manager's uniform grid size; each
        object keeps its own w/h so UI objects are not squashed (L2).
        """
        for obj_id, position in positions.items():
            if obj_id in self.parent._objects:
                obj = self.parent._objects[obj_id]
                w, h = self.box_dims(obj)
                obj.patching_rect = Rect(position[0], position[1], w, h)
        self.prevent_overlaps()
        # judge the layout as optimize_layout will leave it
        self._restore_port_order(self._port_order_before)

    def _placed_crossings(self) -> int:
        """Crossings between the patch's cords as currently placed."""
        segs = []
        for line in self.parent._lines:
            src = self.parent._objects.get(line.src)
            dst = self.parent._objects.get(line.dst)
            if src is None or dst is None:
                continue
            a, b = src.patching_rect, dst.patching_rect
            segs.append(
                (
                    (a[0] + a[2] / 2, a[1] + a[3]),
                    (b[0] + b[2] / 2, b[1]),
                    line.src,
                    line.dst,
                )
            )
        return _count_segment_crossings(segs)

    def _full_layout(self) -> None:
        """Perform full layout optimization based on signal flow analysis."""
        if len(self.parent._objects) < 2:
            return  # Nothing to optimize

        # Place each candidate ordering for real, since prevent_overlaps can
        # move boxes after placement, and keep the one with fewest crossings.
        best: Optional[Dict[str, Rect]] = None
        best_cost = -1
        for candidate in self._candidate_positions():
            self._place(candidate)
            cost = self._placed_crossings()
            if best is None or cost < best_cost:
                best_cost = cost
                best = {i: o.patching_rect for i, o in self.parent._objects.items()}
        for obj_id, rect in (best or {}).items():
            self.parent._objects[obj_id].patching_rect = rect


_Point = Tuple[float, float]


def _count_segment_crossings(segs: List[Tuple[_Point, _Point, str, str]]) -> int:
    """Pairs of cords ``(start, end, src_id, dst_id)`` that cross.

    Cords sharing an object are not counted: they meet at a port.
    """

    def side(a: _Point, b: _Point, c: _Point) -> float:
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    total = 0
    for i, (p1, p2, o1, d1) in enumerate(segs):
        for p3, p4, o2, d2 in segs[i + 1 :]:
            if {o1, d1} & {o2, d2}:
                continue
            if (
                side(p1, p2, p3) * side(p1, p2, p4) < 0
                and side(p3, p4, p1) * side(p3, p4, p2) < 0
            ):
                total += 1
    return total
