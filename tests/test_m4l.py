"""Tests for M4L presentation-mode helpers and integer-coord guardrail."""

from pathlib import Path

import pytest

from py2max import Patcher
from py2max.m4l import (
    NonIntegerCoordinateWarning,
    add_to_presentation,
    enable_presentation,
    enforce_integer_coords,
    is_m4l_infrastructure,
    is_presentation_ui,
)


OUT = Path("outputs")
OUT.mkdir(exist_ok=True)


def test_enable_presentation_sets_flag():
    p = Patcher("outputs/test_m4l_enable.maxpat")
    enable_presentation(p)
    assert p.openinpresentation == 1


def test_enable_presentation_with_devicewidth():
    p = Patcher("outputs/test_m4l_devicewidth.maxpat")
    enable_presentation(p, devicewidth=250)
    assert p.openinpresentation == 1
    assert p.devicewidth == 250
    assert isinstance(p.devicewidth, int)


def test_patcher_method_alias():
    p = Patcher("outputs/test_m4l_method.maxpat")
    p.enable_presentation(devicewidth=300)
    assert p.openinpresentation == 1
    assert p.devicewidth == 300


def test_add_to_presentation_on_ui_object():
    p = Patcher("outputs/test_m4l_ui.maxpat")
    dial = p.add("live.dial", maxclass="live.dial")
    dial.add_to_presentation([10, 10, 40, 40])
    assert dial.presentation == 1
    assert dial.presentation_rect == [10, 10, 40, 40]


def test_add_to_presentation_rejects_infrastructure():
    p = Patcher("outputs/test_m4l_infra.maxpat")
    remote = p.add_textbox("live.remote~")
    with pytest.raises(ValueError, match="live.remote~"):
        remote.add_to_presentation([0, 0, 50, 50])


def test_add_to_presentation_rejects_live_thisdevice():
    p = Patcher("outputs/test_m4l_thisdev.maxpat")
    td = p.add_textbox("live.thisdevice")
    with pytest.raises(ValueError, match="live.thisdevice"):
        td.add_to_presentation([0, 0, 50, 50])


def test_add_to_presentation_rounds_floats_with_warning():
    p = Patcher("outputs/test_m4l_round.maxpat")
    dial = p.add("live.dial", maxclass="live.dial")
    with pytest.warns(NonIntegerCoordinateWarning):
        dial.add_to_presentation([10.7, 20.3, 40.5, 40.0])
    assert dial.presentation_rect == [11, 20, 40, 40]


def test_add_to_presentation_integer_input_no_warning():
    import warnings

    p = Patcher("outputs/test_m4l_noint.maxpat")
    dial = p.add("live.dial", maxclass="live.dial")
    with warnings.catch_warnings():
        warnings.simplefilter("error", NonIntegerCoordinateWarning)
        dial.add_to_presentation([10, 20, 40, 40])


def test_strict_warns_on_unknown_ui_class():
    p = Patcher("outputs/test_m4l_strict.maxpat")
    weird = p.add_textbox("some.unknown.widget")
    with pytest.warns(UserWarning, match="not a known presentation UI"):
        weird.add_to_presentation([0, 0, 40, 40], strict=True)


def test_strict_off_allows_unknown_ui_class():
    import warnings

    p = Patcher("outputs/test_m4l_nonstrict.maxpat")
    weird = p.add_textbox("some.unknown.widget")
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        weird.add_to_presentation([0, 0, 40, 40], strict=False)


def test_classification_helpers():
    p = Patcher("outputs/test_m4l_classify.maxpat")
    dial = p.add("live.dial", maxclass="live.dial")
    remote = p.add_textbox("live.remote~")
    cycle = p.add_textbox("cycle~ 440")

    assert is_presentation_ui(dial)
    assert not is_presentation_ui(remote)
    assert not is_presentation_ui(cycle)

    assert is_m4l_infrastructure(remote)
    assert not is_m4l_infrastructure(dial)
    assert not is_m4l_infrastructure(cycle)


def test_enforce_integer_coords_rounds_rects():
    p = Patcher("outputs/test_m4l_enforce.maxpat")
    b = p.add_textbox("cycle~ 440", patching_rect=[10.6, 20.2, 100.0, 22.0])
    changed = p.enforce_integer_coords()
    assert changed == 1
    # patching_rect is stored as a list when passed as a list.
    assert b.patching_rect[0] == 11
    assert b.patching_rect[1] == 20


def test_enforce_integer_coords_noop_on_clean_rects():
    p = Patcher("outputs/test_m4l_enforce_noop.maxpat")
    p.add_textbox("cycle~ 440", patching_rect=[10, 20, 100, 22])
    assert p.enforce_integer_coords() == 0


def test_functional_api_matches_method_api():
    p1 = Patcher("outputs/test_m4l_api_fn.maxpat")
    d1 = p1.add("live.dial", maxclass="live.dial")
    add_to_presentation(d1, [5, 5, 40, 40])

    p2 = Patcher("outputs/test_m4l_api_method.maxpat")
    d2 = p2.add("live.dial", maxclass="live.dial")
    d2.add_to_presentation([5, 5, 40, 40])

    assert d1.presentation == d2.presentation == 1
    assert d1.presentation_rect == d2.presentation_rect == [5, 5, 40, 40]
