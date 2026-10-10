"""Unit tests for the port message-type model (py2max.maxref.porttypes).

Locks the curation and arg-count resolvers that validation/linting rest on.
"""

import pytest

from py2max.maxref import porttypes as pt


@pytest.mark.parametrize(
    "maxclass,text,expected",
    [
        # value-scaled: count = first integer arg
        ("limi~", "limi~ 2", (2, 2)),
        ("limi~", "limi~", (1, 1)),  # no arg -> maxref default (unchanged)
        ("selector~", "selector~ 3", (4, 1)),  # N signal inlets + 1 control
        # arg-count-scaled: count = number of args (+1 where applicable)
        # select/route: a right inlet per match + 1; match outlets + 1 reject
        ("select", "select 0 1 2 3 4 5 6 7", (9, 9)),
        ("route", "route 1 2 3", (4, 4)),
        ("sel", 'sel bang "New Preset"', (3, 3)),  # a quoted argument is one
        ("join", "join 3 @triggers 1", (3, 1)),  # @attr tail is not an argument
        ("unjoin", "unjoin 3", (1, 4)),
        ("mc.pack~", "mc.pack~ 3", (3, None)),  # mc.* outlets: unknown
        ("mc.matrix~", "mc.matrix~ 1 4 0. @ramp 50", (1, 6)),
        ("matrix~", "matrix~ 2 2", (2, 3)),  # + 1 info outlet
        ("dac~", "dac~ 1 2 3 4", (4, 0)),
        ("expr", "expr $f1 * pow($f2\\,$f3)", (3, 1)),
        ("if", "if $f1 < 0 then 0 else out2 $f1", (1, 2)),
        ("sprintf", "sprintf %s::%d 100%%", (2, 1)),
        # maxref omits the port list; counts are those Max writes
        ("midiformat", "midiformat", (7, 2)),
        # ports follow content or attributes: unknown
        ("js", "js foo.js", (None, None)),
        ("mc.line~", "mc.line~", (None, None)),
        ("unpack", "unpack 0 0 0", (1, 3)),
        ("pack", "pack 0 0", (2, 1)),
    ],
)
def test_arg_aware_port_counts(maxclass, text, expected):
    assert pt.port_counts(maxclass, text) == expected


def test_outlet_emit_curation():
    assert pt.outlet_emits("metro", 0) == pt.BANG
    assert pt.outlet_emits("loadbang", 0) == pt.BANG
    assert pt.outlet_emits("flonum", 0) == pt.FLOAT
    assert pt.outlet_emits("cycle~", 0) == pt.SIGNAL
    assert pt.outlet_emits("tempo", 0) == pt.INT  # a beat count
    # control outlets maxref types exactly
    assert pt.outlet_emits("onebang", 0) == pt.BANG
    assert pt.outlet_emits("snapshot~", 0) == pt.FLOAT
    assert pt.outlet_emits("live.dial", 0) == pt.FLOAT
    # unknown control outlet -> permissive
    assert pt.outlet_emits("some_unknown_ctrl", 0) == pt.ANY


def test_tempo_into_cycle_is_valid():
    from py2max import Patcher

    p = Patcher(validate_connections=True)
    p.add_line(p.add_textbox("tempo"), p.add_textbox("cycle~"))


def test_signal_into_placeholder_typed_ui_inlet_is_invalid():
    # dial's inlet type is the INLET_TYPE placeholder; its method list
    # (bang/int/float) must decide, not the placeholder's ANY
    from py2max import InvalidConnectionError, Patcher

    accepts, authoritative = pt.inlet_acceptance("dial", 0)
    assert authoritative is True
    assert pt.ANY not in accepts and pt.SIGNAL not in accepts
    p = Patcher(validate_connections=True)
    with pytest.raises(InvalidConnectionError):
        p.add_line(p.add_textbox("cycle~ 440"), p.add_textbox("dial"))


def test_pong_emits_float_not_signal():
    # maxref types pong's outlet "signal"; it is the control-rate pong
    from py2max import Patcher

    assert pt.outlet_emits("pong", 0) == pt.FLOAT
    p = Patcher(validate_connections=True)
    p.add_line(p.add_textbox("pong"), p.add_textbox("i"))


def test_inlet_accept_classification():
    assert pt.inlet_accepts("cycle~", 0) == frozenset({pt.SIGNAL, pt.FLOAT, pt.INT})
    assert pt.inlet_accepts("saw~", 1) == frozenset({pt.SIGNAL})  # signal-only
    assert pt.inlet_accepts("noise~", 0) == frozenset({pt.SIGNAL})  # curated
    # a placeholder inlet type defers to the method list, so a control
    # object takes its own messages and no signal
    assert pt.inlet_accepts("counter", 0) == frozenset({pt.BANG, pt.INT, pt.FLOAT})


def test_inlet_acceptance_is_authoritative_from_methodlist():
    # cycle~ has no bang/anything method -> its left inlet is an authoritative
    # signal/number set that excludes bang
    accepts, authoritative = pt.inlet_acceptance("cycle~", 0)
    assert authoritative is True
    assert pt.BANG not in accepts
    # adsr~ has an `anything` method -> permissive (bang trigger is legal)
    adsr_accepts, adsr_auth = pt.inlet_acceptance("adsr~", 0)
    assert pt.ANY in adsr_accepts


def test_message_compatible_rules():
    S, F, NUM, ANY = pt.SIGNAL, pt.FLOAT, pt.INT, pt.ANY
    # signal must reach a signal-capable inlet
    assert pt.message_compatible(S, frozenset({S})) is True
    assert pt.message_compatible(S, frozenset({F, NUM})) is False
    # number into a signal/float inlet is fine; into signal-only is not
    assert pt.message_compatible(F, frozenset({S, F, NUM})) is True
    assert pt.message_compatible(F, frozenset({S})) is False
    # anything into an ANY inlet, or an ANY outlet, is not a definite error
    assert pt.message_compatible(pt.BANG, frozenset({ANY})) is True
    assert pt.message_compatible(ANY, frozenset({S})) is None


def test_inlet_rejects_bang_curation():
    assert pt.inlet_rejects_bang("cycle~", 0) is True
    assert pt.inlet_rejects_bang("adsr~", 0) is False  # envelopes accept a bang trigger


def test_subpatcher_counts_from_content():
    from py2max import Patcher

    p = Patcher()
    sp = p.add_subpatcher("p sub")
    sp._patcher.add_textbox("inlet")
    sp._patcher.add_textbox("inlet")
    sp._patcher.add_textbox("outlet")
    assert pt.subpatcher_counts(sp) == (2, 1)
    # a plain box has no nested patcher
    assert pt.subpatcher_counts(p.add_textbox("cycle~")) == (None, None)


# --- names maxref files elsewhere -----------------------------------------------
@pytest.mark.parametrize(
    "typed,name", [("*~", "*~"), ("+", "+"), ("t", "trigger"), ("sel", "select")]
)
def test_alias_resolves_to_its_refpage(typed, name):
    from py2max.maxref import get_object_info

    info = get_object_info(typed)
    assert info is not None and info["name"] == name


def test_alias_takes_its_targets_resolver():
    assert pt.port_counts("b", "b 3") == (1, 3)  # bangbang


def test_alias_is_range_checked():
    from py2max import InvalidConnectionError, Patcher

    p = Patcher(validate_connections=True)
    with pytest.raises(InvalidConnectionError):
        p.add_line(p.add_textbox("*~ 0.5"), p.add_textbox("dac~"), outlet=1)


def test_aliases_module_is_not_stale():
    """aliases.py is generated from Max's objectmappings; skip without Max."""
    import subprocess
    import sys
    from pathlib import Path

    from py2max.maxref.parser import MaxRefCache

    refpages = MaxRefCache()._get_refpages()
    if refpages is None or not (refpages.parent.parent / "init").is_dir():
        pytest.skip("needs a Max install")
    root = Path(__file__).resolve().parent.parent
    script = root / "scripts" / "gen_maxref_aliases.py"
    result = subprocess.run(
        [sys.executable, str(script), "--check"], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr
