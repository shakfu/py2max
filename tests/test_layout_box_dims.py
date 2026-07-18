"""Regression tests for L2: optimizers must preserve real box dimensions.

Before the fix, every optimizer wrote a hardcoded ``box_width``/``box_height``
(66x22) back onto each object, squashing UI objects (``scope~``, ``dial``,
``function``, ``live.*``, comments) down to text-box size on ``optimize_layout``.
These tests assert that an object's own width/height survives optimization.
"""

import pytest

from py2max import Patcher

OPTIMIZING_LAYOUTS = ["flow", "grid", "matrix"]


def _dims(box):
    r = tuple(box.patching_rect)
    return (r[2], r[3])


@pytest.mark.parametrize("layout", OPTIMIZING_LAYOUTS)
def test_ui_object_dims_survive_optimize(tmp_path, layout):
    p = Patcher(tmp_path / f"dims_{layout}.maxpat", layout=layout)
    scope = p.add_textbox("scope~")  # maxref default ~130x130
    dial = p.add_textbox("dial")  # square UI object
    osc = p.add_textbox("cycle~ 440")
    p.add_line(osc, scope)
    p.add_line(osc, dial)

    before = {scope.id: _dims(scope), dial.id: _dims(dial)}
    assert before[scope.id] != (66.0, 22.0), "fixture should use non-default size"

    p.optimize_layout()

    assert _dims(scope) == before[scope.id]
    assert _dims(dial) == before[dial.id]


@pytest.mark.parametrize("flow_direction", ["horizontal", "vertical"])
def test_ui_object_dims_survive_clustered_optimize(tmp_path, flow_direction):
    """The clustered grid path (``cluster_connected=True``) has its own
    reposition code (``_apply_horizontal/vertical_clustered_layout``). It used
    to hardcode ``box_width``/``box_height`` back onto every object, squashing
    ``scope~`` (~130x130) and ``ezdac~`` (~45x45) to text-box size. The default
    grid path is non-clustered, so this case needs explicit coverage.
    """
    p = Patcher(
        tmp_path / f"clustered_{flow_direction}.maxpat",
        layout="grid",
        flow_direction=flow_direction,
        cluster_connected=True,
    )
    osc = p.add_textbox("cycle~ 440")
    scope = p.add_textbox("scope~")  # maxref default ~130x130
    dac = p.add_textbox("ezdac~")  # maxref default ~45x45
    p.add_line(osc, scope)
    p.add_line(osc, dac)

    before = {scope.id: _dims(scope), dac.id: _dims(dac)}
    assert before[scope.id] != (66.0, 22.0), "fixture should use non-default size"
    assert before[dac.id] != (66.0, 22.0), "fixture should use non-default size"

    p.optimize_layout()

    assert _dims(scope) == before[scope.id]
    assert _dims(dac) == before[dac.id]


@pytest.mark.parametrize("layout", OPTIMIZING_LAYOUTS)
def test_comment_height_survives_optimize(tmp_path, layout):
    p = Patcher(tmp_path / f"cmt_{layout}.maxpat", layout=layout)
    osc = p.add_textbox("cycle~ 440")
    gain = p.add_textbox("gain~")
    p.add_line(osc, gain)
    # a wide comment; its width should not be crushed to 66
    comment = p.add_comment("this is a fairly long descriptive label")
    wide_w = tuple(comment.patching_rect)[2]

    p.optimize_layout()

    assert tuple(comment.patching_rect)[2] == wide_w
