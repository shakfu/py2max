"""Tests for the gated GraphLayoutManager (``layout="graph:<algo>"``).

The layout engines are optional (the ``graph`` extra: graph-layout, ogdf-py,
hola-graph). Each parametrized case skips when its backend is not installed;
the dispatch and error-path tests run without any backend.
"""

import importlib.util
import math

import pytest

from py2max import Patcher
from py2max.layout import GraphLayoutManager


def _installed(module):
    return importlib.util.find_spec(module) is not None


# (algorithm, backend module)
CASES = [
    ("hola", "hola_graph"),
    ("cola", "graph_layout"),
    ("sugiyama", "graph_layout"),
    ("kamada-kawai", "graph_layout"),
    ("circular", "graph_layout"),
    ("ogdf-sugiyama", "ogdf"),
    ("ogdf-fmmm", "ogdf"),
    ("ogdf-planarization", "ogdf"),
]


def _build(layout):
    """A small two-voice synth patch with branching/merging connections."""
    p = Patcher("outputs/test_layout_graph_manager.maxpat", layout=layout)
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


def test_graph_manager_is_selected():
    p = Patcher("outputs/x.maxpat", layout="graph:hola")
    assert isinstance(p._layout_mgr, GraphLayoutManager)
    assert p._layout_mgr.algorithm == "hola"


def test_unknown_graph_algorithm_raises():
    with pytest.raises(ValueError):
        Patcher("outputs/x.maxpat", layout="graph:nonsense")


def test_missing_backend_raises_helpful_import_error(monkeypatch):
    """Force the backend to look uninstalled and assert a clear error.

    Runs regardless of whether hola-graph is actually installed.
    """
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name.startswith("hola_graph"):
            raise ImportError("simulated missing hola_graph")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    p = _build("graph:hola")
    with pytest.raises(ImportError, match=r"graph:hola.*hola-graph"):
        p.optimize_layout()


@pytest.mark.parametrize("algorithm,module", CASES)
def test_graph_layout_manager_repositions(algorithm, module):
    if not _installed(module):
        pytest.skip(f"requires {module}")

    p = _build(f"graph:{algorithm}")
    before = {b.id: tuple(b.patching_rect) for b in p._boxes}

    p.optimize_layout()

    # something actually moved
    moved = any(tuple(b.patching_rect)[:2] != before[b.id][:2] for b in p._boxes)
    assert moved, "optimize_layout() did not reposition any box"

    for b in p._boxes:
        x, y, w, h = b.patching_rect
        # coordinates are finite (no NaN/inf from the engine)
        assert all(math.isfinite(v) for v in (x, y, w, h))
        # normalized into the positive quadrant
        assert x >= 0 and y >= 0
        # box dimensions preserved (UI objects not squashed)
        assert (w, h) == (before[b.id][2], before[b.id][3])


# 30 boxes with crossing cords: big enough that unseeded OGDF Sugiyama breaks
# ties differently between processes (the 13-box _build graph does not).
_POSITIONS_SCRIPT = """
import json
from py2max import Patcher
p = Patcher("x.maxpat", layout="graph:{algorithm}")
bs = [p.add_textbox("t b b b") for _ in range(30)]
for i in range(30):
    for k in (1, 3, 7):
        j = (i * 5 + k) % 30
        if j > i:
            p.add_line(bs[i], bs[j], outlet=k % 3)
p.optimize_layout()
print(json.dumps([list(b.patching_rect) for b in p._boxes]))
"""


# ogdf-planarization is left out: it differs between processes even when seeded.
@pytest.mark.parametrize("algorithm", ["ogdf-sugiyama", "ogdf-fmmm"])
def test_ogdf_layout_is_reproducible_across_processes(algorithm):
    if not _installed("ogdf"):
        pytest.skip("requires ogdf")
    import subprocess
    import sys

    script = _POSITIONS_SCRIPT.format(algorithm=algorithm)
    runs = {
        subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        for _ in range(4)
    }
    assert len(runs) == 1


def _overlaps(p):
    rs = [b.patching_rect for b in p._boxes]
    return sum(
        1
        for i in range(len(rs))
        for j in range(i + 1, len(rs))
        if rs[i][0] < rs[j][0] + rs[j][2]
        and rs[j][0] < rs[i][0] + rs[i][2]
        and rs[i][1] < rs[j][1] + rs[j][3]
        and rs[j][1] < rs[i][1] + rs[i][3]
    )


def _random_patch(layout, seed, n=28, m=36):
    import random

    p = Patcher(layout=layout, on_invalid="ignore")
    rng = random.Random(seed)
    texts = ["metro 100", "scope~", "t b b", "route a b c", "gain~", "+ 1", "live.dial"]
    boxes = [p.add_textbox(rng.choice(texts)) for _ in range(n)]
    for _ in range(m):
        i, j = sorted(rng.sample(range(n), 2))
        p.add_line(boxes[i], boxes[j])
    return p


@pytest.mark.parametrize("seed", range(6))
def test_hola_handles_disconnected_patches(seed):
    """HOLA aborts the process on a disconnected graph unless split up."""
    if not _installed("hola_graph"):
        pytest.skip("requires hola_graph")
    import subprocess
    import sys

    import os

    script = (
        f"import sys; sys.path.insert(0, {os.path.dirname(__file__)!r});"
        "from test_layout_graph_manager import _random_patch, _overlaps;"
        f"p = _random_patch('graph:hola', {seed}); p.optimize_layout();"
        "print(_overlaps(p))"
    )
    out = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr[-300:]
    assert out.stdout.strip() == "0"


@pytest.mark.parametrize("algorithm", ["ogdf-sugiyama", "ogdf-planarization"])
def test_size_aware_engines_keep_their_spacing(algorithm):
    if not _installed("ogdf"):
        pytest.skip("requires ogdf")
    import itertools

    p = _build(f"graph:{algorithm}")
    mgr = p._layout_mgr
    raw = mgr._compute_positions(list(p._boxes), list(p._lines))
    p.optimize_layout()
    centre = {
        b.id: (
            b.patching_rect[0] + b.patching_rect[2] / 2,
            b.patching_rect[1] + b.patching_rect[3] / 2,
        )
        for b in p._boxes
    }
    for a, b in itertools.combinations(centre, 2):
        before = math.dist(raw[a], raw[b])
        assert math.dist(centre[a], centre[b]) == pytest.approx(before, abs=1e-6)


@pytest.mark.parametrize("layout", ["flow", "grid", "matrix", "graph:ogdf-fmmm"])
@pytest.mark.parametrize("seed", range(4))
def test_layouts_leave_no_overlaps(layout, seed):
    if layout.startswith("graph:") and not _installed("ogdf"):
        pytest.skip("requires ogdf")
    p = _random_patch(layout, seed)
    p.optimize_layout()
    assert _overlaps(p) == 0


@pytest.mark.parametrize("algorithm", ["sugiyama", "ogdf-sugiyama"])
def test_layered_layouts_run_top_to_bottom(algorithm):
    module = "ogdf" if algorithm.startswith("ogdf") else "graph_layout"
    if not _installed(module):
        pytest.skip(f"requires {module}")
    p = _build(f"graph:{algorithm}")
    p.optimize_layout()
    y = {b.id: b.patching_rect[1] for b in p._boxes}
    assert all(y[ln.src] < y[ln.dst] for ln in p._lines)
