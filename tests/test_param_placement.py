"""Param docking: value/UI controls placed next to the object they drive."""

import pytest

from py2max import Patcher

# (layout, flow_direction) covering every built-in layout variant
LAYOUT_VARIANTS = [
    ("horizontal", "horizontal"),
    ("vertical", "vertical"),
    ("grid", "horizontal"),
    ("grid", "vertical"),
    ("flow", "horizontal"),
    ("flow", "vertical"),
    ("columnar", "column"),
    ("matrix", "row"),
    ("matrix", "column"),
]


def _xy(box):
    r = box.patching_rect
    return float(r[0]), float(r[1])


def _overlaps(p):
    return [f for f in p.lint() if f.code == "W-OVERLAP"]


def test_param_docks_above_in_horizontal_flow():
    p = Patcher(layout="flow", flow_direction="horizontal", param_placement=True)
    freq = p.add_floatbox()
    osc = p.add_textbox("cycle~ 440")
    dac = p.add_textbox("ezdac~")
    p.add_line(freq, osc)
    p.add_line(osc, dac)
    p.optimize_layout()
    assert _xy(freq)[1] < _xy(osc)[1]  # param sits above its target
    assert not _overlaps(p)


def test_param_docks_left_in_vertical_flow():
    p = Patcher(layout="flow", flow_direction="vertical", param_placement=True)
    freq = p.add_floatbox()
    osc = p.add_textbox("cycle~ 440")
    dac = p.add_textbox("ezdac~")
    p.add_line(freq, osc)
    p.add_line(osc, dac)
    p.optimize_layout()
    assert _xy(freq)[0] < _xy(osc)[0]  # param sits to the left of its target
    assert not _overlaps(p)


def test_two_params_align_to_their_inlets():
    p = Patcher(layout="flow", flow_direction="horizontal", param_placement=True)
    freq = p.add_floatbox()
    phase = p.add_floatbox()
    osc = p.add_textbox("cycle~ 440")
    dac = p.add_textbox("ezdac~")
    p.add_line(freq, osc, inlet=0)
    p.add_line(phase, osc, inlet=1)
    p.add_line(osc, dac)
    p.optimize_layout()
    oy = _xy(osc)[1]
    assert _xy(freq)[1] < oy and _xy(phase)[1] < oy  # both above the target
    assert _xy(freq)[0] < _xy(phase)[0]  # ordered by inlet: freq(0) left of phase(1)
    assert not _overlaps(p)


def test_shared_control_is_not_docked():
    """A control feeding two objects is not a param satellite of either."""

    def build(param_placement):
        p = Patcher(layout="flow", param_placement=param_placement)
        shared = p.add_floatbox()  # fans out to two -> not docked
        solo = p.add_floatbox()  # drives one inlet -> docked
        osc1 = p.add_textbox("cycle~ 440")
        osc2 = p.add_textbox("saw~ 220")
        dac = p.add_textbox("ezdac~")
        p.add_line(shared, osc1)
        p.add_line(shared, osc2)
        p.add_line(solo, osc1, inlet=1)
        p.add_line(osc1, dac)
        p.add_line(osc2, dac)
        p.optimize_layout()
        return _xy(shared), _xy(solo)

    shared_off, solo_off = build(False)
    shared_on, solo_on = build(True)
    assert shared_on == shared_off  # shared control untouched by param placement
    assert solo_on != solo_off  # single-target param was docked (moved)


@pytest.mark.parametrize("layout,flow_direction", LAYOUT_VARIANTS)
def test_param_docking_across_all_layouts(layout, flow_direction):
    """Param docking works in every built-in layout variant. Each case saves a
    patch under build/test-output/ for visual inspection in Max."""
    p = Patcher(
        f"outputs/param_variant_{layout}_{flow_direction}.maxpat",
        layout=layout,
        flow_direction=flow_direction,
        param_placement=True,
    )
    freq = p.add_floatbox()
    phase = p.add_floatbox()
    cutoff = p.add_floatbox()
    osc = p.add_textbox("cycle~ 440")
    filt = p.add_textbox("lores~ 1000")
    dac = p.add_textbox("ezdac~")
    p.add_line(freq, osc, inlet=0)
    p.add_line(phase, osc, inlet=1)
    p.add_line(osc, filt)
    p.add_line(cutoff, filt, inlet=1)
    p.add_line(filt, dac)
    p.optimize_layout()
    p.save()

    def docked(param, target, gap=8, tol=25):
        px, py, pw, ph = (float(v) for v in param.patching_rect)
        tx, ty, tw, th = (float(v) for v in target.patching_rect)
        # adjacent on one perpendicular side with a small gap
        return (
            0 <= ty - (py + ph) <= gap + tol  # just above
            or 0 <= py - (ty + th) <= gap + tol  # just below
            or 0 <= tx - (px + pw) <= gap + tol  # just left
            or 0 <= px - (tx + tw) <= gap + tol  # just right
        )

    assert docked(freq, osc)
    assert docked(phase, osc)
    assert docked(cutoff, filt)
    assert not _overlaps(p)
    assert not [f for f in p.lint() if f.severity == "error"]


def test_flag_is_off_by_default():
    def build(**kw):
        p = Patcher(layout="flow", **kw)
        freq = p.add_floatbox()
        osc = p.add_textbox("cycle~ 440")
        dac = p.add_textbox("ezdac~")
        p.add_line(freq, osc)
        p.add_line(osc, dac)
        p.optimize_layout()
        return _xy(freq)

    assert build() == build(param_placement=False)
    assert build(param_placement=True) != build()
