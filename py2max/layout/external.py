"""Graph-layout backends exposed as py2max layout managers.

This module adapts three optional external layout engines to py2max's
``LayoutManager`` contract so they can be selected with
``layout="graph:<algo>"`` and applied with ``Patcher.optimize_layout()``:

  * graph-hola   (``hola_graph``)  -- HOLA human-like orthogonal layout
  * graph-layout (``graph_layout``)-- COLA plus force-directed / geometric
  * ogdf-py      (``ogdf``)        -- OGDF layered / force-directed / planar

None of these are imported at module load; each is imported lazily inside
``_full_layout`` so importing py2max keeps zero runtime dependencies. Install
the engines with ``pip install "py2max[graph]"``.

Unlike the grid/flow managers, graph layouts need the *whole* graph to run, so
they only take effect on ``optimize_layout()`` -- objects keep their add-time
positions until then. Build the patch fully, then call ``optimize_layout()``.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Set, Tuple

from py2max.core.abstract import AbstractPatcher
from py2max.core.common import Rect

from .base import LayoutManager

Positions = Dict[str, Tuple[float, float]]

# graph-layout algorithm name -> (class name, engine kwargs)
_GRAPH_LAYOUT_KW: Dict[str, Tuple[str, Dict[str, Any]]] = {
    "cola": (
        "ColaLayoutAdapter",
        {"avoid_overlaps": True, "link_distance": 100, "random_seed": 7},
    ),
    "sugiyama": ("SugiyamaLayout", {}),
    "fruchterman-reingold": ("FruchtermanReingoldLayout", {"random_seed": 7}),
    "kamada-kawai": ("KamadaKawaiLayout", {}),
    "spectral": ("SpectralLayout", {}),
    "circular": ("CircularLayout", {}),
    "shell": ("ShellLayout", {}),
}

# ogdf algorithm name -> OGDF layout factory attribute
_OGDF_FACTORY: Dict[str, str] = {
    "ogdf-sugiyama": "SugiyamaLayout",
    "ogdf-fmmm": "FMMMLayout",
    "ogdf-planarization": "PlanarizationLayout",
}


def _components(boxes: List[Any], lines: List[Any]) -> List[List[Any]]:
    """Boxes grouped into connected components, largest first, isolated last."""
    neighbours: Dict[str, List[str]] = {box.id: [] for box in boxes}
    for line in lines:
        if line.src in neighbours and line.dst in neighbours:
            neighbours[line.src].append(line.dst)
            neighbours[line.dst].append(line.src)
    by_id = {box.id: box for box in boxes}
    seen: Set[str] = set()
    groups: List[List[Any]] = []
    for box in boxes:
        if box.id in seen:
            continue
        stack, group = [box.id], []
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            group.append(by_id[node])
            stack.extend(neighbours[node])
        groups.append(group)
    return sorted(groups, key=lambda g: -len(g))  # stable: ties keep box order


# graph-layout engines whose y axis points up
_FLIP_Y = frozenset({"sugiyama"})

# engines that lay out from real box sizes and return box centres
_SIZE_AWARE = frozenset({"hola", *_OGDF_FACTORY})

# backend key -> pip package name (for the missing-dependency error)
_PACKAGE = {
    "hola": "hola-graph",
    "graph_layout": "graph-layout",
    "ogdf": "ogdf-py",
}


class GraphLayoutManager(LayoutManager):
    """Position boxes with an external graph-layout engine.

    Args:
        parent: the parent patcher.
        algorithm: one of :attr:`ALGORITHMS` (e.g. ``"hola"``, ``"cola"``,
            ``"ogdf-sugiyama"``).
        span: target size in px for the longest side of the normalized layout.
            Defaults to a value scaled by object count so boxes do not overlap.
        seed: random seed for the OGDF engines.
        runs: OGDF Sugiyama crossing-minimization runs; the best is kept.
            More than 1 can trade reproducibility for fewer crossings.
    """

    #: supported algorithm names (the part after ``graph:``)
    ALGORITHMS: Tuple[str, ...] = (
        ("hola",) + tuple(_GRAPH_LAYOUT_KW) + tuple(_OGDF_FACTORY)
    )

    def __init__(
        self,
        parent: AbstractPatcher,
        algorithm: str,
        span: Optional[float] = None,
        seed: int = 7,
        runs: int = 1,
        **kwargs: Any,
    ) -> None:
        super().__init__(parent, **kwargs)
        if algorithm not in self.ALGORITHMS:
            raise ValueError(
                f"unknown graph layout {algorithm!r}; choose from: "
                + ", ".join(self.ALGORITHMS)
            )
        self.algorithm = algorithm
        self.span = span
        self.seed = seed
        self.runs = runs

    # -- LayoutManager hook ------------------------------------------------
    def _full_layout(self) -> None:
        boxes: List[Any] = list(self.parent._boxes)
        if not boxes:
            return
        positions = self._compute_positions(boxes, list(self.parent._lines))
        if self.algorithm in _SIZE_AWARE:
            positions = self._translate(positions, boxes)
        else:
            positions = self._normalize(positions, len(boxes))
        for box in boxes:
            x, y = positions[box.id]
            w, h = self.box_dims(box)
            box.patching_rect = Rect(x, y, w, h)
        # Constraint/force engines can leave residual overlaps around large
        # nodes (e.g. scope~ at 130x130) even with avoid_overlaps enabled, since
        # they optimise on approximate sizes. Run the dimension-aware safety net
        # the grid/flow managers use so the saved patch is overlap-free.
        self.prevent_overlaps()

    # -- helpers -----------------------------------------------------------
    def _box_xywh(self, box: Any) -> Tuple[float, float, float, float]:
        rect = box.patching_rect
        w, h = self.box_dims(box)
        return float(rect[0]), float(rect[1]), w, h

    def _compute_positions(self, boxes: List[Any], lines: List[Any]) -> Positions:
        if self.algorithm == "hola":
            return self._run_hola(boxes, lines)
        if self.algorithm in _GRAPH_LAYOUT_KW:
            cls_name, kw = _GRAPH_LAYOUT_KW[self.algorithm]
            return self._run_graph_layout(cls_name, kw, boxes, lines)
        return self._run_ogdf(_OGDF_FACTORY[self.algorithm], boxes, lines)

    def _run_hola(self, boxes: List[Any], lines: List[Any]) -> Positions:
        """HOLA per connected component, packed left to right.

        HOLA needs a connected graph: an isolated box raises ``map::at`` and a
        second component aborts the process from a C++ assertion. So each
        component is laid out alone, and isolated boxes follow in a row.
        """
        try:
            from hola_graph._core import Graph, HolaOpts, Node, do_hola
        except ImportError as exc:
            raise self._missing("hola") from exc

        out: Positions = {}
        x_offset = 0.0
        gap = 2.0 * self.pad
        for component in _components(boxes, lines):
            ids = {box.id for box in component}
            graph = Graph()
            nodes = {}
            for box in component:
                x, y, w, h = self._box_xywh(box)
                nodes[box.id] = Node.allocate(x, y, w, h)
                graph.add_node(nodes[box.id])
            edges = [ln for ln in lines if ln.src in ids and ln.dst in ids]
            for line in edges:
                graph.add_edge(nodes[line.src], nodes[line.dst])
            if edges:
                do_hola(graph, HolaOpts())
            # shift this component so its left edge sits at x_offset
            centres = {
                box.id: (nodes[box.id].get_centre().x, nodes[box.id].get_centre().y)
                for box in component
            }
            left = min(centres[b.id][0] - self.box_dims(b)[0] / 2 for b in component)
            top = min(centres[b.id][1] - self.box_dims(b)[1] / 2 for b in component)
            for box in component:
                cx, cy = centres[box.id]
                out[box.id] = (cx - left + x_offset, cy - top)
            right = max(out[b.id][0] + self.box_dims(b)[0] / 2 for b in component)
            x_offset = right + gap
        return out

    def _run_graph_layout(
        self,
        cls_name: str,
        kw: Dict[str, Any],
        boxes: List[Any],
        lines: List[Any],
    ) -> Positions:
        try:
            import graph_layout as gl
        except ImportError as exc:
            raise self._missing("graph_layout") from exc
        cls = getattr(gl, cls_name)
        nodes: List[Dict[str, Any]] = []
        index: Dict[str, int] = {}
        for i, box in enumerate(boxes):
            x, y, w, h = self._box_xywh(box)
            nodes.append({"id": box.id, "x": x, "y": y, "width": w, "height": h})
            index[box.id] = i
        links = [
            {"source": index[line.src], "target": index[line.dst]}
            for line in lines
            if line.src in index and line.dst in index
        ]
        engine = cls(nodes=nodes, links=links, **kw)
        engine.run()
        # graph-layout's Sugiyama puts sources at the bottom even with its
        # default orientation="top-to-bottom"; Max cords run downward
        flip = -1.0 if self.algorithm in _FLIP_Y else 1.0
        return {
            box.id: (engine.nodes[i].x, flip * engine.nodes[i].y)
            for i, box in enumerate(boxes)
        }

    def _run_ogdf(
        self, factory_name: str, boxes: List[Any], lines: List[Any]
    ) -> Positions:
        try:
            import ogdf
        except ImportError as exc:
            raise self._missing("ogdf") from exc
        graph = ogdf.Graph()
        attrs = ogdf.GraphAttributes(graph, ogdf.NODE_GRAPHICS | ogdf.EDGE_GRAPHICS)
        onodes = {}
        for box in boxes:
            x, y, w, h = self._box_xywh(box)
            node = graph.new_node()
            onodes[box.id] = node
            attrs.set_x(node, x)
            attrs.set_y(node, y)
            attrs.set_width(node, w)
            attrs.set_height(node, h)
        for line in lines:
            if line.src in onodes and line.dst in onodes:
                graph.new_edge(onodes[line.src], onodes[line.dst])
        # OGDF's randomized passes break ties differently in each process
        # unless its process-wide engine is seeded before every call.
        ogdf.set_seed(self.seed)
        layout = getattr(ogdf, factory_name)()
        if hasattr(layout, "set_runs"):
            layout.set_runs(self.runs)
        if hasattr(layout, "set_rand_seed"):
            layout.set_rand_seed(self.seed)
        layout.call(attrs)
        return {
            box.id: (attrs.x(onodes[box.id]), attrs.y(onodes[box.id])) for box in boxes
        }

    def _translate(self, positions: Positions, boxes: List[Any]) -> Positions:
        """Centres to top-left corners, moved to the margin, scale kept.

        HOLA and OGDF place boxes from their real sizes, so their spacing is
        already right; rescaling it would make the gaps arbitrary.
        """
        corners = {}
        for box in boxes:
            w, h = self.box_dims(box)
            cx, cy = positions[box.id]
            corners[box.id] = (cx - w / 2, cy - h / 2)
        min_x = min(x for x, _ in corners.values())
        min_y = min(y for _, y in corners.values())
        return {
            k: (self.pad + x - min_x, self.pad + y - min_y)
            for k, (x, y) in corners.items()
        }

    def _normalize(self, positions: Positions, n: int) -> Positions:
        xs = [p[0] for p in positions.values()]
        ys = [p[1] for p in positions.values()]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        extent = max(max_x - min_x, max_y - min_y) or 1.0
        span = self.span or max(300.0, 2.2 * self.box_width * math.sqrt(n))
        scale = span / extent
        margin = self.pad
        return {
            k: (margin + (x - min_x) * scale, margin + (y - min_y) * scale)
            for k, (x, y) in positions.items()
        }

    def _missing(self, backend: str) -> ImportError:
        pkg = _PACKAGE[backend]
        return ImportError(
            f"layout 'graph:{self.algorithm}' requires the {pkg!r} package; "
            'install it with: pip install "py2max[graph]"'
        )
