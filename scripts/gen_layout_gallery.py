#!/usr/bin/env python3
"""Generate a gallery of graph-layout renderings for the py2max docs.

Each supported layout backend is run over a single representative sample
patch and the result is rendered to SVG under ``docs/assets/imgs/``.  The
gallery page ``docs/user_guide/layout_gallery.md`` references these images.

Backends (all optional):

  * graph-hola   (``hola_graph``)  -- HOLA human-like orthogonal layout
  * graph-layout (``graph_layout``)-- COLA plus force-directed / geometric
  * ogdf         (``ogdf``)        -- OGDF layered / force-directed / planar

Install the layout engines with::

    pip install "py2max[graph]" hola-graph
    # or: uv sync --extra graph  (then add hola-graph)

A backend that is not installed is skipped with a note rather than failing
the whole run.  All rendering goes through py2max's own ``Patcher.to_svg`` so
every layout is shown as the same Max patch, only repositioned.

Usage::

    python scripts/gen_layout_gallery.py            # regenerate every image
    python scripts/gen_layout_gallery.py --list     # list available layouts
    python scripts/gen_layout_gallery.py --only hola cola ogdf-sugiyama
    python scripts/gen_layout_gallery.py --backend ogdf
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

# Running as ``python scripts/gen_layout_gallery.py`` puts this ``scripts/``
# directory on ``sys.path[0]``, where ``scripts/py2max.py`` would shadow the
# installed ``py2max`` package.  Drop the script's own directory first.
_here = str(Path(__file__).resolve().parent)
sys.path[:] = [p for p in sys.path if Path(p or ".").resolve() != Path(_here)]

import logging  # noqa: E402

logging.getLogger("py2max").setLevel(logging.WARNING)

from py2max import Patcher  # noqa: E402
from py2max.core.common import Rect  # noqa: E402
from py2max.export.svg import BG_COLOR  # noqa: E402

# Matches the single full-canvas patcher-background rect that export_svg draws.
_BG_RECT_RE = re.compile(
    r"[ \t]*<rect[^>]*fill=\"" + re.escape(BG_COLOR) + r"\"[^>]*/>\n?"
)


def _transparent_background(svg: str) -> str:
    """Drop the grey patcher-background rect so the SVG is transparent."""
    return _BG_RECT_RE.sub("", svg, count=1)

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTDIR = REPO_ROOT / "docs" / "assets" / "imgs"

# Positions returned by a backend: box id -> (x, y).
Positions = Dict[str, Tuple[float, float]]
LayoutFn = Callable[[Patcher], Positions]


# --------------------------------------------------------------------------- #
# Sample patch
# --------------------------------------------------------------------------- #
def build_sample_patch(**patcher_kwargs: object) -> Patcher:
    """A small two-voice synth patch used for every gallery image.

    Two oscillator chains are amplitude-scaled, summed, and sent to a dac
    and a scope -- enough branching and merging to make the differences
    between layout algorithms visible.
    """
    p = Patcher("gallery-sample.maxpat", **patcher_kwargs)
    fbox, ibox, tbox, link = (
        p.add_floatbox,
        p.add_intbox,
        p.add_textbox,
        p.add_line,
    )

    freq1 = fbox()
    freq2 = fbox()
    phase = fbox()
    osc1 = tbox("cycle~")
    osc2 = tbox("cycle~")
    amp1 = fbox()
    amp2 = fbox()
    mul1 = tbox("*~")
    mul2 = tbox("*~")
    add1 = tbox("+~")
    dac = tbox("ezdac~")
    scop = tbox("scope~")
    scp1 = ibox()

    link(freq1, osc1)
    link(osc1, mul1)
    link(mul1, add1)
    link(amp1, mul1, inlet=1)
    link(freq2, osc2)
    link(phase, osc2, inlet=1)
    link(osc2, mul2)
    link(amp2, mul2, inlet=1)
    link(mul2, add1, inlet=1)
    link(add1, dac)
    link(add1, dac, inlet=1)
    link(add1, scop)
    link(scp1, scop)
    return p


# --------------------------------------------------------------------------- #
# Backend adapters -- each returns a {box_id: (x, y)} mapping
# --------------------------------------------------------------------------- #
def _hola(patcher: Patcher) -> Positions:
    from hola_graph._core import Graph, HolaOpts, Node, do_hola

    graph = Graph()
    nodes = {}
    for box in patcher._boxes:
        x, y, w, h = box.patching_rect
        node = Node.allocate(x, y, w, h)
        nodes[box.id] = node
        graph.add_node(node)
    for line in patcher._lines:
        graph.add_edge(nodes[line.src], nodes[line.dst])

    do_hola(graph, HolaOpts())

    out: Positions = {}
    for box in patcher._boxes:
        centre = nodes[box.id].get_centre()
        out[box.id] = (centre.x, centre.y)
    return out


def _graph_layout(cls_name: str, **kwargs) -> LayoutFn:
    """Adapter for the uniform ``graph_layout`` layout classes."""

    def fn(patcher: Patcher) -> Positions:
        import graph_layout as gl

        cls = getattr(gl, cls_name)
        nodes: List[dict] = []
        index: Dict[str, int] = {}
        for i, box in enumerate(patcher._boxes):
            x, y, w, h = box.patching_rect
            nodes.append({"id": box.id, "x": x, "y": y, "width": w, "height": h})
            index[box.id] = i
        links = [
            {"source": index[line.src], "target": index[line.dst]}
            for line in patcher._lines
        ]
        layout = cls(nodes=nodes, links=links, **kwargs)
        layout.run()
        return {
            box.id: (layout.nodes[i].x, layout.nodes[i].y)
            for i, box in enumerate(patcher._boxes)
        }

    return fn


def _ogdf(factory_name: str) -> LayoutFn:
    """Adapter for OGDF layouts (raw Graph / GraphAttributes API)."""

    def fn(patcher: Patcher) -> Positions:
        import ogdf

        graph = ogdf.Graph()
        attrs = ogdf.GraphAttributes(
            graph, ogdf.NODE_GRAPHICS | ogdf.EDGE_GRAPHICS
        )
        onodes = {}
        for box in patcher._boxes:
            x, y, w, h = box.patching_rect
            node = graph.new_node()
            onodes[box.id] = node
            attrs.set_x(node, float(x))
            attrs.set_y(node, float(y))
            attrs.set_width(node, float(w))
            attrs.set_height(node, float(h))
        for line in patcher._lines:
            graph.new_edge(onodes[line.src], onodes[line.dst])

        getattr(ogdf, factory_name)().call(attrs)

        return {
            box.id: (attrs.x(onodes[box.id]), attrs.y(onodes[box.id]))
            for box in patcher._boxes
        }

    return fn


# --------------------------------------------------------------------------- #
# Layout registry
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class LayoutSpec:
    name: str  # gallery image basename
    backend: str  # graph-hola | graph-layout | ogdf | builtin
    fn: LayoutFn
    title: str  # human label for the gallery page
    # For built-in py2max managers: Patcher kwargs (e.g. layout="grid").
    # When set, the patch is built with these kwargs and positioned via
    # optimize_layout() instead of an external engine + normalization.
    patcher_kwargs: Optional[dict] = None


REGISTRY: List[LayoutSpec] = [
    # graph-hola --------------------------------------------------------------
    LayoutSpec("hola", "graph-hola", _hola, "HOLA (orthogonal)"),
    # graph-layout ------------------------------------------------------------
    LayoutSpec(
        "cola",
        "graph-layout",
        _graph_layout(
            "ColaLayoutAdapter",
            avoid_overlaps=True,
            link_distance=100,
            random_seed=7,
        ),
        "COLA (constraint)",
    ),
    LayoutSpec(
        "sugiyama",
        "graph-layout",
        _graph_layout("SugiyamaLayout"),
        "Sugiyama (layered)",
    ),
    LayoutSpec(
        "fruchterman-reingold",
        "graph-layout",
        _graph_layout("FruchtermanReingoldLayout", random_seed=7),
        "Fruchterman-Reingold",
    ),
    LayoutSpec(
        "kamada-kawai",
        "graph-layout",
        _graph_layout("KamadaKawaiLayout"),
        "Kamada-Kawai",
    ),
    LayoutSpec(
        "spectral",
        "graph-layout",
        _graph_layout("SpectralLayout"),
        "Spectral",
    ),
    LayoutSpec(
        "circular",
        "graph-layout",
        _graph_layout("CircularLayout"),
        "Circular",
    ),
    LayoutSpec(
        "shell",
        "graph-layout",
        _graph_layout("ShellLayout"),
        "Shell",
    ),
    # ogdf --------------------------------------------------------------------
    LayoutSpec(
        "ogdf-sugiyama",
        "ogdf",
        _ogdf("SugiyamaLayout"),
        "OGDF Sugiyama (layered)",
    ),
    LayoutSpec(
        "ogdf-fmmm",
        "ogdf",
        _ogdf("FMMMLayout"),
        "OGDF FMMM (force-directed)",
    ),
    LayoutSpec(
        "ogdf-planarization",
        "ogdf",
        _ogdf("PlanarizationLayout"),
        "OGDF Planarization (orthogonal)",
    ),
]


def _builtin_placeholder(patcher: Patcher) -> Positions:
    """Unused: built-in managers position via optimize_layout(), not fn."""
    return {}


# py2max's own layout managers (no external dependencies)
REGISTRY += [
    LayoutSpec(
        "grid-horizontal", "builtin", _builtin_placeholder,
        "Grid (horizontal)", {"layout": "grid", "flow_direction": "horizontal"},
    ),
    LayoutSpec(
        "grid-vertical", "builtin", _builtin_placeholder,
        "Grid (vertical)", {"layout": "grid", "flow_direction": "vertical"},
    ),
    LayoutSpec(
        "flow-horizontal", "builtin", _builtin_placeholder,
        "Flow (horizontal)", {"layout": "flow", "flow_direction": "horizontal"},
    ),
    LayoutSpec(
        "flow-vertical", "builtin", _builtin_placeholder,
        "Flow (vertical)", {"layout": "flow", "flow_direction": "vertical"},
    ),
    LayoutSpec(
        "columnar", "builtin", _builtin_placeholder,
        "Columnar", {"layout": "columnar"},
    ),
    LayoutSpec(
        "matrix", "builtin", _builtin_placeholder,
        "Matrix", {"layout": "matrix"},
    ),
]


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #
def _normalize(positions: Positions, span: float) -> Positions:
    """Rescale a position cloud so its longest side spans ``span`` px.

    Different engines emit coordinates on wildly different scales (unit-range
    for spectral/circular, pixels for ogdf/hola).  Normalising every layout to
    the same span keeps the gallery visually consistent.
    """
    xs = [p[0] for p in positions.values()]
    ys = [p[1] for p in positions.values()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    extent = max(max_x - min_x, max_y - min_y) or 1.0
    scale = span / extent
    return {
        k: ((x - min_x) * scale, (y - min_y) * scale)
        for k, (x, y) in positions.items()
    }


def _apply(patcher: Patcher, positions: Positions) -> None:
    """Move each box to its computed position, preserving its width/height."""
    for box in patcher._boxes:
        x, y = positions[box.id]
        r = box.patching_rect
        box.patching_rect = Rect(x, y, r[2], r[3])


def generate(
    specs: List[LayoutSpec],
    outdir: Path,
    span: float,
    quiet: bool = False,
) -> Tuple[List[str], List[Tuple[str, str]]]:
    """Render each spec to ``<outdir>/<name>.svg``.

    Returns ``(generated_names, failures)`` where each failure is
    ``(name, reason)``.
    """
    outdir.mkdir(parents=True, exist_ok=True)
    generated: List[str] = []
    failures: List[Tuple[str, str]] = []

    for spec in specs:
        try:
            if spec.patcher_kwargs is not None:
                # built-in py2max manager: build with the layout and let the
                # manager position the boxes via optimize_layout().
                patcher = build_sample_patch(**spec.patcher_kwargs)
                patcher.optimize_layout()
            else:
                # external engine: reposition + normalize into a common span.
                patcher = build_sample_patch()
                positions = _normalize(spec.fn(patcher), span)
                _apply(patcher, positions)
            path = outdir / f"{spec.name}.svg"
            svg = _transparent_background(patcher.to_svg_string())
            path.write_text(svg, encoding="utf-8")
            generated.append(spec.name)
            if not quiet:
                print(f"  ok    {spec.name:22s} -> {path.relative_to(REPO_ROOT)}")
        except ImportError as exc:
            failures.append((spec.name, f"backend not installed ({exc})"))
            if not quiet:
                print(f"  skip  {spec.name:22s} ({spec.backend} not installed)")
        except Exception as exc:  # layout engine raised on this graph
            failures.append((spec.name, f"{type(exc).__name__}: {exc}"))
            if not quiet:
                print(f"  FAIL  {spec.name:22s} {type(exc).__name__}: {exc}")

    return generated, failures


def _select(args: argparse.Namespace) -> List[LayoutSpec]:
    specs = REGISTRY
    if args.backend:
        specs = [s for s in specs if s.backend == args.backend]
    if args.only:
        wanted = set(args.only)
        specs = [s for s in specs if s.name in wanted]
        unknown = wanted - {s.name for s in specs}
        if unknown:
            sys.exit(f"unknown layout(s): {', '.join(sorted(unknown))}")
    return specs


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--outdir",
        type=Path,
        default=DEFAULT_OUTDIR,
        help=f"output directory (default: {DEFAULT_OUTDIR.relative_to(REPO_ROOT)})",
    )
    parser.add_argument(
        "--only",
        nargs="+",
        metavar="NAME",
        help="only render these layouts (by name)",
    )
    parser.add_argument(
        "--backend",
        choices=["graph-hola", "graph-layout", "ogdf", "builtin"],
        help="only render layouts from this backend",
    )
    parser.add_argument(
        "--span",
        type=float,
        default=520.0,
        help="target span in px for the normalized layout (default: 520)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="list available layouts and exit",
    )
    parser.add_argument("--quiet", action="store_true", help="suppress per-item output")
    args = parser.parse_args(argv)

    specs = _select(args)

    if args.list:
        width = max(len(s.name) for s in REGISTRY)
        for s in specs:
            print(f"{s.name:{width}s}  {s.backend:12s}  {s.title}")
        return 0

    if not specs:
        sys.exit("no layouts selected")

    print(f"Generating {len(specs)} layout image(s) into {args.outdir}")
    generated, failures = generate(specs, args.outdir, args.span, args.quiet)

    print(f"\n{len(generated)} generated, {len(failures)} skipped/failed")
    real_failures = [f for f in failures if not f[1].startswith("backend not installed")]
    if real_failures:
        print("failures:")
        for name, reason in real_failures:
            print(f"  {name}: {reason}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
