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
    moved = any(
        tuple(b.patching_rect)[:2] != before[b.id][:2] for b in p._boxes
    )
    assert moved, "optimize_layout() did not reposition any box"

    for b in p._boxes:
        x, y, w, h = b.patching_rect
        # coordinates are finite (no NaN/inf from the engine)
        assert all(math.isfinite(v) for v in (x, y, w, h))
        # normalized into the positive quadrant
        assert x >= 0 and y >= 0
        # box dimensions preserved (UI objects not squashed)
        assert (w, h) == (before[b.id][2], before[b.id][3])
