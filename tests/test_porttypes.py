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
        ("select", "select 0 1 2 3 4 5 6 7", (2, 9)),  # 8 matches + 1 reject
        ("route", "route 1 2 3", (2, 4)),
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
    # unknown control outlet -> permissive
    assert pt.outlet_emits("some_unknown_ctrl", 0) == pt.ANY


def test_inlet_accept_classification():
    assert pt.inlet_accepts("cycle~", 0) == frozenset({pt.SIGNAL, pt.FLOAT, pt.INT})
    assert pt.inlet_accepts("saw~", 1) == frozenset({pt.SIGNAL})  # signal-only
    assert pt.inlet_accepts("noise~", 0) == frozenset({pt.SIGNAL})  # curated
    # a control object with a placeholder inlet type stays permissive
    assert pt.ANY in pt.inlet_accepts("counter", 0)


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
