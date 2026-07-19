"""Patch-level linter: each finding code fires, and save-time behavior."""

import logging

import pytest

from py2max import Patcher, InvalidPatchError, lint
from py2max.lint import (
    E_BAD_CONNECTION,
    E_DUP_ID,
    E_INLET_RANGE,
    E_ORPHAN_LINE,
    E_OUTLET_RANGE,
    W_OFFCANVAS,
    W_OVERLAP,
    W_UNKNOWN_OBJECT,
)


def _codes(patcher):
    return {f.code for f in patcher.lint()}


# --- each finding code fires -------------------------------------------------
def test_bad_connection_code():
    p = Patcher()  # validation off so we can build a broken patch
    p.add_line(p.add_textbox("metro 500"), p.add_textbox("cycle~ 440"))
    assert E_BAD_CONNECTION in _codes(p)


def test_outlet_range_code():
    p = Patcher()
    p.add_line(p.add_textbox("cycle~ 440"), p.add_textbox("gain~"), outlet=5)
    assert E_OUTLET_RANGE in _codes(p)


def test_inlet_range_code():
    p = Patcher()
    p.add_line(p.add_textbox("cycle~ 440"), p.add_textbox("ezdac~"), inlet=9)
    assert E_INLET_RANGE in _codes(p)


def test_orphan_line_code():
    p = Patcher()
    line = p.add_line(p.add_textbox("cycle~ 440"), p.add_textbox("gain~"))
    line.destination = ["ghost-id", 0]  # dangle the destination
    assert E_ORPHAN_LINE in _codes(p)


def test_dup_id_code():
    p = Patcher()
    a = p.add_textbox("cycle~ 440")
    b = p.add_textbox("saw~ 220")
    b.id = a.id  # force a duplicate id
    assert E_DUP_ID in _codes(p)


def test_overlap_code():
    p = Patcher()
    p.add_textbox("cycle~ 440", patching_rect=[100, 100, 66, 22])
    p.add_textbox("saw~ 220", patching_rect=[100, 100, 66, 22])
    assert W_OVERLAP in _codes(p)


def test_offcanvas_code():
    p = Patcher()
    p.add_textbox("cycle~ 440", patching_rect=[5000, 5000, 66, 22])
    assert W_OFFCANVAS in _codes(p)


def test_unknown_object_code():
    p = Patcher()
    p.add_textbox("totally_made_up_object~")
    assert W_UNKNOWN_OBJECT in _codes(p)


# --- clean patches are clean -------------------------------------------------
def test_clean_signal_chain_has_no_errors():
    p = Patcher(layout="grid")
    freq = p.add_floatbox()
    osc = p.add_textbox("cycle~ 440")
    gain = p.add_textbox("gain~")
    dac = p.add_textbox("ezdac~")
    p.add_line(freq, osc)
    p.add_line(osc, gain)
    p.add_line(gain, dac)
    p.optimize_layout()
    errors = [f for f in p.lint() if f.severity == "error"]
    assert errors == []


def test_synth_voice_pattern_lints_clean():
    """The canonical voice used by the layout examples must be error-free:
    a number box sets frequency, metro triggers the envelope, and the envelope
    modulates amplitude through a *~ VCA."""
    p = Patcher(layout="grid")
    freq = p.add_floatbox()
    metro = p.add_textbox("metro 500")
    osc = p.add_textbox("cycle~ 440")
    env = p.add_textbox("adsr~ 10 100 0.7 500")
    vca = p.add_textbox("*~")
    filt = p.add_textbox("lores~ 1000")
    dac = p.add_textbox("ezdac~")
    p.add_line(freq, osc)  # float -> frequency
    p.add_line(metro, env)  # bang -> envelope trigger
    p.add_line(osc, vca)  # signal -> VCA
    p.add_line(env, vca, inlet=1)  # envelope -> VCA amplitude
    p.add_line(vca, filt)
    p.add_line(filt, dac)
    p.optimize_layout()
    assert [f for f in p.lint() if f.severity == "error"] == []


def test_lint_module_function_matches_method():
    p = Patcher()
    p.add_textbox("cycle~ 440")
    assert [str(f) for f in lint(p)] == [str(f) for f in p.lint()]


# --- subpatchers -------------------------------------------------------------
def _subpatcher_with_ports(p, n_inlets, n_outlets):
    sp = p.add_subpatcher("p mysub")
    for _ in range(n_inlets):
        sp._patcher.add_textbox("inlet")
    for _ in range(n_outlets):
        sp._patcher.add_textbox("outlet")
    return sp


def test_subpatcher_inlet_count_is_content_derived():
    p = Patcher()
    sp = _subpatcher_with_ports(p, n_inlets=2, n_outlets=1)
    src = p.add_textbox("cycle~ 440")
    p.add_line(src, sp, inlet=1)  # in range: subpatcher has 2 inlets
    assert not [f for f in p.lint() if f.severity == "error"]


def test_subpatcher_inlet_out_of_range_is_flagged():
    p = Patcher()
    sp = _subpatcher_with_ports(p, n_inlets=2, n_outlets=1)
    src = p.add_textbox("cycle~ 440")
    p.add_line(src, sp, inlet=5)  # subpatcher only has 2 inlets
    assert E_INLET_RANGE in {f.code for f in p.lint()}


def test_lint_recurses_into_subpatchers():
    p = Patcher()
    sp = p.add_subpatcher("p mysub")
    sub = sp._patcher
    sub.add_line(sub.add_textbox("metro 500"), sub.add_textbox("cycle~ 440"))
    nested = [f for f in p.lint() if f.code == E_BAD_CONNECTION]
    assert nested, "nested bad connection should be reported"
    # the finding is path-qualified with the subpatcher box id
    assert nested[0].line is not None and "/" in nested[0].line[0]


# --- save-time behavior ------------------------------------------------------
def test_strict_save_raises_on_error(tmp_path):
    p = Patcher(tmp_path / "bad.maxpat", strict=True)
    p.add_line(p.add_textbox("metro 500"), p.add_textbox("cycle~ 440"))
    with pytest.raises(InvalidPatchError):
        p.save()


def test_nonstrict_save_logs_but_succeeds(tmp_path, caplog):
    path = tmp_path / "bad.maxpat"
    p = Patcher(path)  # strict defaults False
    p.add_line(p.add_textbox("metro 500"), p.add_textbox("cycle~ 440"))
    with caplog.at_level(logging.WARNING):
        p.save()
    assert path.exists()  # save still succeeds
    assert any("E-BAD-CONNECTION" in r.message for r in caplog.records)


def test_strict_clean_save_succeeds(tmp_path):
    path = tmp_path / "ok.maxpat"
    p = Patcher(path, strict=True)
    p.add_line(p.add_floatbox(), p.add_textbox("cycle~ 440"))
    p.save()
    assert path.exists()
