"""FlowLayoutManager crossing reduction."""

import random

import pytest

from py2max import Patcher
from py2max.layout.flow import _count_segment_crossings


def _crossings(p):
    segs = []
    for ln in p._lines:
        a = p._objects[ln.src].patching_rect
        b = p._objects[ln.dst].patching_rect
        segs.append(
            ((a[0] + a[2] / 2, a[1] + a[3]), (b[0] + b[2] / 2, b[1]), ln.src, ln.dst)
        )
    return _count_segment_crossings(segs)


def _two_components(p):
    """Two independent message chains with skip cords, built interleaved."""
    a = [p.add_textbox(f"+ {i}") for i in range(14)]
    b = [p.add_textbox(f"* {i}") for i in range(14)]
    for chain in (a, b):
        for i in range(13):
            p.add_line(chain[i], chain[i + 1])
        for i in range(0, 11, 3):
            p.add_line(chain[i], chain[i + 3])


def _random_dag(p, seed, n=24, m=34):
    rng = random.Random(seed)
    boxes = [p.add_textbox("+ 0") for _ in range(n)]
    for _ in range(m):
        i, j = sorted(rng.sample(range(n), 2))
        p.add_line(boxes[i], boxes[j])


def test_segment_crossing_count():
    x = [((0, 0), (10, 10), "a", "b"), ((0, 10), (10, 0), "c", "d")]
    assert _count_segment_crossings(x) == 1
    shared = [((0, 0), (10, 10), "a", "b"), ((0, 10), (10, 0), "a", "d")]
    assert _count_segment_crossings(shared) == 0
    parallel = [((0, 0), (10, 0), "a", "b"), ((0, 5), (10, 5), "c", "d")]
    assert _count_segment_crossings(parallel) == 0


def test_independent_components_do_not_cross():
    p = Patcher(layout="flow", flow_direction="vertical")
    _two_components(p)
    p.optimize_layout()
    assert _crossings(p) == 0


@pytest.mark.parametrize("direction", ["vertical", "horizontal"])
@pytest.mark.parametrize("seed", range(4))
def test_never_worse_than_single_barycenter_pass(direction, seed):
    p = Patcher(layout="flow", flow_direction=direction)
    _random_dag(p, seed)
    mgr = p._layout_mgr
    original = mgr._candidate_positions()[0]  # the previous algorithm's order
    mgr._place(original)
    baseline = _crossings(p)
    p.optimize_layout()
    assert _crossings(p) <= baseline


def test_flow_layout_is_deterministic():
    def build():
        p = Patcher(layout="flow")
        _random_dag(p, 7)
        p.optimize_layout()
        return [tuple(b.patching_rect) for b in p._boxes]

    assert build() == build()


def _synth(p):
    """ezdac~ fed directly by the oscillator and through a 3-box chain."""
    osc = p.add_textbox("cycle~ 440")
    chain = [p.add_textbox(t) for t in ("lores~ 800", "*~ 0.5", "+~")]
    dac = p.add_textbox("ezdac~")
    p.add_line(osc, chain[0])
    for a, b in zip(chain, chain[1:]):
        p.add_line(a, b)
    p.add_line(chain[-1], dac)
    p.add_line(osc, dac, inlet=1)
    return osc, chain, dac


def test_vertical_flow_cords_all_point_down():
    for seed in range(4):
        p = Patcher(layout="flow", flow_direction="vertical")
        _random_dag(p, seed)
        p.optimize_layout()
        y = {b.id: b.patching_rect[1] for b in p._boxes}
        assert all(y[ln.src] < y[ln.dst] for ln in p._lines)


def test_vertical_flow_puts_outputs_last():
    p = Patcher(layout="flow", flow_direction="vertical")
    osc, chain, dac = _synth(p)
    scope = p.add_textbox("scope~")
    p.add_line(osc, scope)
    p.optimize_layout()
    bottom = max(b.patching_rect[1] for b in p._boxes if b is not dac)
    assert dac.patching_rect[1] > bottom


def test_feedback_cycle_still_lays_out():
    p = Patcher(layout="flow", flow_direction="vertical")
    a, b, c = (p.add_textbox(t) for t in ("+ 1", "* 2", "- 3"))
    p.add_line(a, b)
    p.add_line(b, c)
    p.add_line(c, a)  # feedback
    p.optimize_layout()
    assert len({tuple(x.patching_rect) for x in (a, b, c)}) == 3
