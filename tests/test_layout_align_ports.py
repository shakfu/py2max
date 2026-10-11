"""optimize_layout(align_ports=True) straightens cords from boxes above."""

import itertools

import pytest

from py2max import Patcher
from py2max.core.common import Rect

LAYOUTS = [
    ("grid", "vertical"),
    ("grid", "horizontal"),
    ("vertical", "vertical"),
    ("horizontal", "horizontal"),
    ("flow", "vertical"),
    ("flow", "horizontal"),
    ("columnar", "vertical"),
    ("matrix", "horizontal"),
]


# invalid cords raise, so every test patch is one Max would accept
STRICT = {"validate_connections": True}


def _xy(box):
    return tuple(box.patching_rect[:2])


def _stereo_chain(layout="grid"):
    p = Patcher(
        "outputs/align.maxpat", layout=layout, flow_direction="vertical", **STRICT
    )
    osc, gain, dac = p.add("cycle~ 440"), p.add("gain~"), p.add("ezdac~")
    p.link(osc, gain)
    p.link(gain, dac)
    p.link(gain, dac, inlet=1)
    return p, osc, gain, dac


def test_off_by_default():
    p, osc, gain, dac = _stereo_chain()
    p.optimize_layout()
    assert _xy(dac)[0] != _xy(gain)[0]


@pytest.mark.parametrize("layout", ["grid", "flow"])
def test_vertical_aligns_inlet_under_outlet(layout):
    # ezdac~ is window-anchored at x = 0.1 * width; inlet 0 goes under
    # gain~ outlet 0 and its y is kept
    p, osc, gain, dac = _stereo_chain(layout)
    p.optimize_layout()
    ys = [_xy(b)[1] for b in (osc, gain, dac)]
    p.optimize_layout(align_ports=True)
    assert _xy(osc)[0] == _xy(gain)[0] == _xy(dac)[0]
    assert [_xy(b)[1] for b in (osc, gain, dac)] == ys


def test_skips_cord_through_box():
    # osc -> dac would drop through gain~, which sits between them
    p, osc, gain, dac = _stereo_chain()
    p._lines = [ln for ln in p._lines if ln.dst != dac.id]
    p.link(osc, dac)
    x = _xy(dac)[0]
    p.optimize_layout(align_ports=True)
    assert _xy(dac)[0] == x


def test_never_moves_explicit_rect():
    p = Patcher(
        "outputs/align_x.maxpat", layout="grid", flow_direction="vertical", **STRICT
    )
    osc = p.add("cycle~ 440")
    dac = p.add("ezdac~", patching_rect=Rect(300, 300, 45, 45))
    p.link(osc, dac)
    p.optimize_layout(align_ports=True)
    assert _xy(dac) == (300, 300)


def test_subset():
    p, osc, gain, dac = _stereo_chain()
    p.optimize_layout_subset([osc, gain, dac], align_ports=True)
    assert _xy(osc)[0] == _xy(gain)[0] == _xy(dac)[0]


def test_topdown_aligns_by_default():
    p, osc, gain, dac = _stereo_chain("topdown")
    p.optimize_layout()
    assert _xy(osc)[0] == _xy(gain)[0] == _xy(dac)[0]


def test_topdown_places_like_vertical():
    td, v = _stereo_chain("topdown"), _stereo_chain("vertical")
    assert [_xy(b) for b in td[0]._boxes] == [_xy(b) for b in v[0]._boxes]


def test_topdown_explicit_false_wins():
    p, osc, gain, dac = _stereo_chain("topdown")
    x = _xy(dac)[0]
    p.optimize_layout(align_ports=False)
    assert _xy(dac)[0] == x != _xy(gain)[0]


def _build(layout, flow_direction):
    p = Patcher(
        "outputs/align_all.maxpat",
        layout=layout,
        flow_direction=flow_direction,
        **STRICT,
    )
    freq, osc, saw = p.add("flonum"), p.add("cycle~ 440"), p.add("saw~ 220")
    lores, gain, dac = p.add("lores~ 1000"), p.add("gain~"), p.add("ezdac~")
    for a, b in ((freq, osc), (osc, lores), (saw, lores), (lores, gain)):
        p.link(a, b)
    p.link(gain, dac)
    p.link(gain, dac, inlet=1)
    return p


def _overlapping(p):
    rects = [Rect(*b.patching_rect[:4]) for b in p._boxes]
    return {
        (i, j)
        for (i, a), (j, b) in itertools.combinations(enumerate(rects), 2)
        if a.x < b.x + b.w and b.x < a.x + a.w and a.y < b.y + b.h and b.y < a.y + a.h
    }


@pytest.mark.parametrize("layout,flow_direction", LAYOUTS)
def test_every_layout_moves_x_only_without_new_overlaps(layout, flow_direction):
    off, on = _build(layout, flow_direction), _build(layout, flow_direction)
    off.optimize_layout()
    on.optimize_layout(align_ports=True)
    assert [_xy(b)[1] for b in on._boxes] == [_xy(b)[1] for b in off._boxes]
    assert _overlapping(on) <= _overlapping(off)
