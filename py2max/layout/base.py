"""Base layout manager for py2max patches.

This module provides the base LayoutManager class that all layout managers inherit from.
"""

from typing import Any, Dict, List, Optional, Set, Tuple, cast

from py2max.core.abstract import AbstractLayoutManager, AbstractPatcher
from py2max.core.common import Rect
from py2max.maxref import MAXCLASS_DEFAULTS

from .graph import PatchGraph

# Threshold for incremental vs full layout (30% of total objects)
INCREMENTAL_THRESHOLD = 0.3

# Value/UI "param" objects: their role is to set a value on one object's inlet,
# so they read better docked next to that object than spread through the graph.
PARAM_MAXCLASSES = frozenset(
    {"flonum", "number", "message", "toggle", "slider", "dial"}
)


def _is_param(box: object) -> bool:
    """True for a value/UI control that parameterizes another object."""
    mc = getattr(box, "maxclass", "") or ""
    return mc in PARAM_MAXCLASSES or mc.startswith("live.")


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
            return cast(Rect, MAXCLASS_DEFAULTS[maxclass]["patching_rect"])
        except KeyError:
            return None

    def box_dims(self, obj: object) -> tuple[float, float]:
        """Return an object's own (width, height) for repositioning.

        Optimizers place objects on a uniform grid sized by ``box_width`` /
        ``box_height``, but they must not *write back* those defaults as the
        object's size -- doing so squashes every UI object (``dial``, ``scope~``,
        ``function``, ``live.*``, comments) down to text-box dimensions (L2).
        Read the object's existing rect and keep its real w/h, falling back to
        the manager defaults only when it has no usable rect. Works whether the
        rect is a ``Rect`` namedtuple (programmatic) or a plain list (loaded).
        """
        rect = getattr(obj, "patching_rect", None)
        try:
            if rect is not None and len(rect) >= 4:
                w, h = float(rect[2]), float(rect[3])
                if w and h:
                    return w, h
        except (TypeError, ValueError):
            # A malformed patching_rect (e.g. a string from a misused add_*
            # call) must not crash layout; fall back to the manager defaults.
            pass
        return float(self.box_width), float(self.box_height)

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

    def prevent_overlaps(self, min_gap: float = 10.0, max_iterations: int = 50) -> int:
        """Iteratively push overlapping objects apart.

        This method should be called after layout optimization to ensure
        no objects overlap. It uses an iterative approach where overlapping
        objects are pushed apart in the direction of their center offset.

        Args:
            min_gap: Minimum gap between objects in pixels.
            max_iterations: Maximum number of iterations to prevent infinite loops.

        Returns:
            Number of iterations performed (0 if no overlaps found).
        """
        objects = [
            o for o in self.parent._objects.values() if hasattr(o, "patching_rect")
        ]
        if len(objects) < 2:
            return 0

        def overlapping(a: Rect, b: Rect) -> bool:
            return (
                a.x < b.x + b.w + min_gap
                and b.x < a.x + a.w + min_gap
                and a.y < b.y + b.h + min_gap
                and b.y < a.y + a.h + min_gap
            )

        iterations_performed = 0
        for iteration in range(max_iterations):
            # Sweep in reading order and push each object clear of any *earlier*
            # one it overlaps, along the axis of least penetration. Objects only
            # move away from earlier ones (never back into them), so the total
            # displacement is monotone and the sweep converges. A symmetric
            # pairwise push instead oscillates on dense clusters and never
            # settles. Real layout-manager output is already overlap-free, so
            # this is a safety net rather than the primary placement.
            objects.sort(key=lambda o: (o.patching_rect.y, o.patching_rect.x))
            moved = False
            for i in range(1, len(objects)):
                ri = objects[i].patching_rect
                original = ri
                for j in range(i):
                    rj = objects[j].patching_rect
                    if not overlapping(ri, rj):
                        continue
                    pen_x = min(ri.x + ri.w, rj.x + rj.w) - max(ri.x, rj.x) + min_gap
                    pen_y = min(ri.y + ri.h, rj.y + rj.h) - max(ri.y, rj.y) + min_gap
                    if pen_x <= pen_y:
                        if ri.x + ri.w / 2 >= rj.x + rj.w / 2:
                            nx = rj.x + rj.w + min_gap
                        else:
                            nx = max(self.pad, rj.x - ri.w - min_gap)
                        ri = Rect(nx, ri.y, ri.w, ri.h)
                    else:
                        if ri.y + ri.h / 2 >= rj.y + rj.h / 2:
                            ny = rj.y + rj.h + min_gap
                        else:
                            ny = max(self.pad, rj.y - ri.h - min_gap)
                        ri = Rect(ri.x, ny, ri.w, ri.h)
                if ri != original:
                    objects[i].patching_rect = ri
                    moved = True
            iterations_performed = iteration + 1
            if not moved:
                break

        return iterations_performed

    def place_params(self, direction: Optional[str] = None, gap: float = 8.0) -> None:
        """Dock value/UI 'param' objects next to the single object they drive.

        A param (number box, toggle, slider, dial, message, ``live.*``) whose
        outgoing connections all go to one non-param target is repositioned
        adjacent to that target, perpendicular to the signal flow -- above the
        target for a horizontal flow, to its left for a vertical flow -- and
        aligned to the inlet it feeds. This keeps value controls with their
        object instead of spread through the signal graph.

        Runs after the main layout as the final placement pass. ``direction``
        defaults to the manager's ``flow_direction``.
        """
        objects = self.parent._objects

        # outgoing edges per source: source_id -> [(inlet, target_id), ...]
        out_edges: Dict[str, List[Tuple[int, str]]] = {}
        for line in self.parent._lines:
            source = getattr(line, "source", None)
            destination = getattr(line, "destination", None)
            if not source or not destination:
                continue
            inlet = int(destination[1]) if len(destination) > 1 else 0
            out_edges.setdefault(source[0], []).append((inlet, destination[0]))

        # a param drives exactly one non-param target -> group by that target
        by_target: Dict[str, List[Tuple[int, Any]]] = {}
        for src_id, edges in out_edges.items():
            box = objects.get(src_id)
            if box is None or not _is_param(box):
                continue
            targets = {t for _, t in edges}
            if len(targets) != 1:
                continue
            target_id = next(iter(targets))
            target = objects.get(target_id)
            if target is None or _is_param(target):
                continue
            inlet = min(i for i, _ in edges)
            by_target.setdefault(target_id, []).append((inlet, box))

        if not by_target:
            return

        direction = direction or getattr(self, "flow_direction", "horizontal")
        left_side = direction in ("vertical", "column")
        for target_id, params in by_target.items():
            params.sort(key=lambda p: p[0])
            self._dock_params(objects[target_id], params, left_side, gap)

        self.prevent_overlaps()

    def _dock_params(
        self,
        target: Any,
        params: List[Tuple[int, Any]],
        left_side: bool,
        gap: float,
    ) -> None:
        """Position a target's param satellites (params sorted by inlet).

        Docks on the perpendicular side that has room: left of the target when a
        vertical flow leaves space, otherwise right; above for a horizontal flow,
        otherwise below. This keeps params clear of a flow that hugs an edge.
        """
        tr = target.patching_rect
        tx, ty, tw, th = float(tr[0]), float(tr[1]), float(tr[2]), float(tr[3])
        n_inlets = int(getattr(target, "numinlets", 1) or 1)

        if left_side:
            max_w = max(float(b.patching_rect[2]) for _, b in params)
            x = tx - max_w - gap
            if x < self.pad:  # no room on the left -> dock on the right
                x = tx + tw + gap
            y = ty
            for _, box in params:
                bw, bh = float(box.patching_rect[2]), float(box.patching_rect[3])
                box.patching_rect = Rect(x, y, bw, bh)
                y += bh + gap
            return

        max_h = max(float(b.patching_rect[3]) for _, b in params)
        y = ty - max_h - gap
        if y < self.pad:  # no room above -> dock below
            y = ty + th + gap
        if len(params) == 1:
            inlet, box = params[0]
            bw = float(box.patching_rect[2])
            cx = self._inlet_center_x(tx, tw, n_inlets, inlet)
            box.patching_rect = Rect(
                max(self.pad, cx - bw / 2), y, bw, box.patching_rect[3]
            )
        else:
            # pack params as a centered row, in inlet order
            widths = [float(b.patching_rect[2]) for _, b in params]
            row_w = sum(widths) + gap * (len(params) - 1)
            x = max(self.pad, tx + tw / 2 - row_w / 2)
            for (_, box), bw in zip(params, widths):
                box.patching_rect = Rect(x, y, bw, float(box.patching_rect[3]))
                x += bw + gap

    @staticmethod
    def _inlet_center_x(tx: float, tw: float, n_inlets: int, inlet: int) -> float:
        """Approximate x of the center of ``inlet`` on a box (Max spreads inlets
        edge-to-edge across the top)."""
        if n_inlets <= 1:
            return tx + tw / 2
        return tx + tw * min(inlet, n_inlets - 1) / (n_inlets - 1)

    def get_connected_objects(self, obj_ids: Set[str]) -> Set[str]:
        """Get all objects connected to the given objects via patchlines.

        Args:
            obj_ids: Set of object IDs to find connections for.

        Returns:
            Set of object IDs that are directly connected to the input objects.
        """
        return PatchGraph(self.parent._lines).neighbors_of(obj_ids)

    def get_affected_objects(self, changed_objects: Set[str]) -> Set[str]:
        """Get all objects affected by changes to the given objects.

        This includes the changed objects themselves plus their immediate
        neighbors (objects connected via patchlines).

        Args:
            changed_objects: Set of object IDs that have changed.

        Returns:
            Set of all affected object IDs.
        """
        affected = set(changed_objects)
        neighbors = self.get_connected_objects(changed_objects)
        affected.update(neighbors)
        return affected

    def should_use_incremental(self, changed_objects: Optional[Set[str]]) -> bool:
        """Determine whether to use incremental or full layout.

        Uses incremental layout when:
        - changed_objects is provided
        - The number of affected objects is less than INCREMENTAL_THRESHOLD
          of total objects

        Args:
            changed_objects: Set of changed object IDs, or None for full layout.

        Returns:
            True if incremental layout should be used.
        """
        if changed_objects is None:
            return False

        total_objects = len(self.parent._objects)
        if total_objects == 0:
            return False

        affected = self.get_affected_objects(changed_objects)
        return len(affected) < total_objects * INCREMENTAL_THRESHOLD

    def optimize_layout(self, changed_objects: Optional[Set[str]] = None) -> None:
        """Optimize the layout of objects.

        If changed_objects is provided and the number of affected objects
        is small relative to the total, only those objects and their
        neighbors will be repositioned (incremental layout). Otherwise,
        a full layout recalculation is performed.

        Args:
            changed_objects: Optional set of object IDs that have changed.
                If None, performs full layout optimization.

        Subclasses should override _full_layout() and optionally
        _incremental_layout() to implement specific algorithms.
        """
        if self.should_use_incremental(changed_objects):
            # changed_objects is guaranteed non-None here since should_use_incremental
            # returns False when changed_objects is None
            assert changed_objects is not None
            affected = self.get_affected_objects(changed_objects)
            self._incremental_layout(affected)
        else:
            self._full_layout()

    def _full_layout(self) -> None:
        """Perform full layout optimization.

        Subclasses should override this method to implement their
        full layout algorithm.
        """
        pass

    def _incremental_layout(self, affected_objects: Set[str]) -> None:
        """Perform incremental layout optimization for affected objects.

        This method repositions only the affected objects while keeping
        other objects in their current positions. The default implementation
        finds optimal positions for affected objects that minimize overlap
        with existing objects.

        Args:
            affected_objects: Set of object IDs to reposition.

        Subclasses can override this for more sophisticated incremental layouts.
        """
        if not affected_objects:
            return

        # Get current positions of non-affected objects (these are fixed)
        fixed_positions: Dict[str, Rect] = {}
        for obj_id, obj in self.parent._objects.items():
            if obj_id not in affected_objects:
                if hasattr(obj, "patching_rect"):
                    fixed_positions[obj_id] = obj.patching_rect

        # For each affected object, find a position that doesn't overlap
        for obj_id in affected_objects:
            if obj_id not in self.parent._objects:
                continue

            obj = self.parent._objects[obj_id]
            if not hasattr(obj, "patching_rect"):
                continue

            current_rect = obj.patching_rect

            # Try to find a nearby position that doesn't overlap
            best_pos = self._find_non_overlapping_position(
                current_rect, fixed_positions, affected_objects
            )

            if best_pos:
                obj.patching_rect = best_pos
                # Add to fixed positions for subsequent objects
                fixed_positions[obj_id] = best_pos

        # Final overlap prevention pass
        self.prevent_overlaps()

    def _find_non_overlapping_position(
        self,
        rect: Rect,
        fixed_positions: Dict[str, Rect],
        exclude_ids: Set[str],
    ) -> Optional[Rect]:
        """Find a position for rect that doesn't overlap with fixed positions.

        Tries positions in a spiral pattern around the current position.

        Args:
            rect: The rectangle to position.
            fixed_positions: Dictionary of fixed object positions.
            exclude_ids: Object IDs to exclude from overlap checking.

        Returns:
            A non-overlapping Rect, or the original rect if no better position found.
        """
        pad = self.pad
        min_gap = 10.0

        def overlaps_any(test_rect: Rect) -> bool:
            for obj_id, fixed_rect in fixed_positions.items():
                if obj_id in exclude_ids:
                    continue
                # Check overlap
                if (
                    test_rect.x < fixed_rect.x + fixed_rect.w + min_gap
                    and fixed_rect.x < test_rect.x + test_rect.w + min_gap
                    and test_rect.y < fixed_rect.y + fixed_rect.h + min_gap
                    and fixed_rect.y < test_rect.y + test_rect.h + min_gap
                ):
                    return True
            return False

        # If current position doesn't overlap, keep it
        if not overlaps_any(rect):
            return rect

        # Try positions in a spiral pattern
        step = pad / 2
        max_radius = max(self.parent.width, self.parent.height) / 2

        for radius in range(1, int(max_radius / step) + 1):
            offset = radius * step
            # Try 8 directions
            for dx, dy in [
                (offset, 0),
                (-offset, 0),
                (0, offset),
                (0, -offset),
                (offset, offset),
                (-offset, offset),
                (offset, -offset),
                (-offset, -offset),
            ]:
                new_x = rect.x + dx
                new_y = rect.y + dy

                # Ensure within bounds
                new_x = max(pad, min(new_x, self.parent.width - rect.w - pad))
                new_y = max(pad, min(new_y, self.parent.height - rect.h - pad))

                test_rect = Rect(new_x, new_y, rect.w, rect.h)
                if not overlaps_any(test_rect):
                    return test_rect

        # No non-overlapping position found, return original
        return rect
