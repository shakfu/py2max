"""Patcher.optimize_layout_subset(): lay out a subset, keep the rest."""

import pytest

from py2max import Patcher
from py2max.core.common import Rect


def _overlaps(boxes):
    rs = [b.patching_rect for b in boxes]
    return [
        (i, j)
        for i in range(len(rs))
        for j in range(i + 1, len(rs))
        if rs[i][0] < rs[j][0] + rs[j][2]
        and rs[j][0] < rs[i][0] + rs[i][2]
        and rs[i][1] < rs[j][1] + rs[j][3]
        and rs[j][1] < rs[i][1] + rs[i][3]
    ]


def _patch(layout="flow"):
    p = Patcher(layout=layout)
    ui = [
        p.add_textbox("live.dial", patching_rect=Rect(20.0, 20.0, 44.0, 48.0)),
        p.add_textbox("live.dial", patching_rect=Rect(80.0, 20.0, 44.0, 48.0)),
    ]
    logic = [p.add_textbox(f"+ {i}") for i in range(6)]
    for a, b in zip(logic, logic[1:]):
        p.add_line(a, b)
    p.add_line(ui[0], logic[0])
    p.add_line(ui[1], logic[2], inlet=1)
    return p, ui, logic


def test_fixed_boxes_do_not_move():
    p, ui, logic = _patch()
    before = [tuple(b.patching_rect) for b in ui]
    p.optimize_layout_subset(logic)
    assert [tuple(b.patching_rect) for b in ui] == before


def test_subset_is_laid_out_and_clear_of_fixed_boxes():
    p, ui, logic = _patch()
    for b in logic:  # pile the logic onto the UI
        b.patching_rect = Rect(30.0, 30.0, 60.0, 22.0)
    p.optimize_layout_subset(logic)
    assert _overlaps(p._boxes) == []
    # horizontal flow puts the chain on successive levels, left to right
    xs = [b.patching_rect[0] for b in logic]
    assert xs == sorted(xs) and len(set(xs)) == len(xs)


def test_subset_keeps_its_corner_when_clear():
    p, ui, logic = _patch(layout="grid")
    for i, b in enumerate(logic):
        b.patching_rect = Rect(400.0 + i * 5, 300.0, 60.0, 22.0)
    p.optimize_layout_subset(logic)
    assert min(b.patching_rect[0] for b in logic) == 400.0
    assert min(b.patching_rect[1] for b in logic) == 300.0


def test_patch_state_is_restored():
    p, ui, logic = _patch()
    boxes, lines, objects = list(p._boxes), list(p._lines), dict(p._objects)
    p.optimize_layout_subset(logic)
    assert p._boxes == boxes and p._lines == lines and p._objects == objects


@pytest.mark.parametrize(
    "layout", ["horizontal", "vertical", "grid", "flow", "matrix", "columnar"]
)
def test_window_grows_to_show_every_box(layout):
    p = Patcher(layout=layout, on_invalid="ignore")
    boxes = [p.add_textbox(t) for t in ["metro 100", "scope~", "gain~", "+ 1"] * 20]
    for a, b in zip(boxes, boxes[1:]):
        p.add_line(a, b)
    p.optimize_layout()
    assert not [f for f in p.lint() if f.code == "W-OFFCANVAS"]


@pytest.mark.parametrize("name", ["nodes", "codebox", "gen.codebox~"])
def test_absolute_default_coordinates_are_not_anchors(name):
    """codebox defaults hold absolute coords; read as fractions they put the
    box at the window's far corner, off-canvas."""
    p = Patcher()
    box = p.add_textbox(name)
    assert box.patching_rect[0] < p.width and box.patching_rect[1] < p.height


def test_fractional_anchor_still_applies():
    p = Patcher()
    dac = p.add_textbox("ezdac~")  # anchored bottom-left
    assert dac.patching_rect[1] > p.height / 2
