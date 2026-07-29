"""Regression tests: rects survive a load as ``Rect``, not as plain lists.

JSON has no tuple type, so every rect in a patch read off disk arrives as a
list. ``Box.patching_rect`` is declared ``Optional[Rect]`` and read attribute-
wise (``rect.y``) by the layout managers, so before the fix any layout call on a
loaded patch died with ``AttributeError: 'list' object has no attribute 'y'`` --
including the documented ``py2max optimize <file>`` CLI subcommand.

The matching constraint is that ``to_dict()`` must still emit plain JSON arrays,
so a load/save round trip stays faithful at the Python level and does not leak
the internal ``Rect`` type into the serialized form.
"""

import json

import pytest

from py2max import Patcher
from py2max.core.common import Rect
from py2max.m4l import enforce_integer_coords

DATA_DIR = __import__("pathlib").Path(__file__).parent / "data"

OPTIMIZING_LAYOUTS = ["flow", "grid", "matrix", "columnar"]


def _make_patch(path, layout="grid"):
    p = Patcher(path, layout=layout)
    osc = p.add_textbox("cycle~ 440")
    gain = p.add_textbox("gain~")
    dac = p.add_textbox("ezdac~")
    p.add_line(osc, gain)
    p.add_line(gain, dac)
    p.save()
    return path


def test_loaded_box_rect_is_a_rect(tmp_path):
    path = _make_patch(tmp_path / "load.maxpat")
    p = Patcher.from_file(path)
    for box in p._boxes:
        assert isinstance(box.patching_rect, Rect)
        # attribute access is the thing that used to blow up
        assert box.patching_rect.y == box.patching_rect[1]


def test_loaded_patcher_rect_is_a_rect(tmp_path):
    path = _make_patch(tmp_path / "load.maxpat")
    p = Patcher.from_file(path)
    assert isinstance(p.rect, Rect)
    assert p.width == p.rect[2]
    assert p.height == p.rect[3]


@pytest.mark.parametrize("layout", OPTIMIZING_LAYOUTS)
def test_optimize_layout_on_loaded_patch(tmp_path, layout):
    """The original bug: optimize_layout() crashed on any patch read off disk."""
    path = _make_patch(tmp_path / f"opt_{layout}.maxpat", layout=layout)
    p = Patcher.from_file(path)
    p.set_layout_mgr(layout)
    p.optimize_layout()  # AttributeError before the fix
    for box in p._boxes:
        assert isinstance(box.patching_rect, Rect)


def test_nested_subpatcher_rects_are_coerced():
    """Coercion must reach boxes inside nested patchers, not just the top level."""
    p = Patcher.from_file(DATA_DIR / "nested.maxpat")

    def walk(patcher):
        for box in patcher._boxes:
            yield box
            if getattr(box, "_patcher", None) is not None:
                yield from walk(box._patcher)

    boxes = list(walk(p))
    assert len(boxes) > len(p._boxes), "fixture should contain subpatchers"
    for box in boxes:
        pr = getattr(box, "patching_rect", None)
        if pr is not None:
            assert isinstance(pr, Rect), f"{box.id} kept a plain list"


@pytest.mark.parametrize(
    "name",
    ["simple.maxpat", "complex.maxpat", "nested.maxpat", "tabular.maxpat"],
)
def test_to_dict_emits_plain_lists_not_rects(name):
    """``Rect`` is internal; the serialized form must be pure JSON types."""
    src = json.loads((DATA_DIR / name).read_text())
    out = Patcher.from_file(DATA_DIR / name).to_dict()

    def assert_no_rects(node):
        if isinstance(node, dict):
            for v in node.values():
                assert_no_rects(v)
        elif isinstance(node, list):
            for v in node:
                assert_no_rects(v)
        else:
            assert not isinstance(node, Rect), "Rect leaked into to_dict output"

    assert_no_rects(out)
    assert out == src, "load/save round trip is not faithful"


def test_enforce_integer_coords_on_immutable_rect(tmp_path):
    """``Rect`` is a NamedTuple; rounding used to assign to ``rect.x`` and crash."""
    p = Patcher(tmp_path / "m4l.maxpat")
    box = p.add_textbox("cycle~ 440", patching_rect=Rect(1.5, 2.5, 62.0, 22.0))

    assert enforce_integer_coords(p) == 1
    assert box.patching_rect == Rect(2, 2, 62, 22)
    assert isinstance(box.patching_rect, Rect)


def test_enforce_integer_coords_preserves_list_form(tmp_path):
    """A hand-assigned plain list must stay a list, and still get rounded."""
    p = Patcher(tmp_path / "m4l_list.maxpat")
    box = p.add_textbox("cycle~ 440")
    box.patching_rect = [1.5, 2.5, 62.0, 22.0]

    assert enforce_integer_coords(p) == 1
    assert box.patching_rect == [2, 2, 62, 22]
    assert isinstance(box.patching_rect, list)


def test_enforce_integer_coords_noop_when_already_integral(tmp_path):
    p = Patcher(tmp_path / "m4l_noop.maxpat")
    p.add_textbox("cycle~ 440", patching_rect=Rect(1.0, 2.0, 62.0, 22.0))
    assert enforce_integer_coords(p) == 0
