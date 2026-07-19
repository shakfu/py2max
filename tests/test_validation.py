"""Golden message-type matrix for connection validation.

Locks in the conservative rules of ``maxref.validate_connection`` /
``maxref.porttypes``: real errors are caught, ambiguous / unknown cases are
allowed so on-by-default checking never rejects a valid patch.
"""

import pytest

from py2max import Patcher, InvalidConnectionError
from py2max.maxref import validate_connection

# (src, outlet, dst, inlet, expect_valid, note)
MATRIX = [
    # --- definite errors ---
    ("metro", 0, "cycle~", 0, False, "bang into oscillator freq inlet"),
    ("metro", 0, "saw~", 1, False, "bang into signal-only phase inlet"),
    ("loadbang", 0, "noise~", 0, False, "bang into signal-only inlet (curated)"),
    ("button", 0, "cycle~", 0, False, "bang button into oscillator"),
    ("cycle~", 5, "gain~", 0, False, "outlet index out of range"),
    ("cycle~", 0, "ezdac~", 5, False, "inlet index out of range"),
    # --- valid / allowed ---
    ("flonum", 0, "cycle~", 0, True, "float sets oscillator frequency"),
    ("number", 0, "cycle~", 0, True, "int sets oscillator frequency"),
    ("cycle~", 0, "gain~", 0, True, "signal into signal inlet"),
    ("gain~", 0, "ezdac~", 1, True, "signal into dac right inlet"),
    ("metro", 0, "counter", 0, True, "bang into a control inlet"),
    # adsr~'s signal/float inlet *is* bang-triggerable -> must NOT be flagged
    ("metro", 0, "adsr~", 0, True, "bang triggers an envelope (no false positive)"),
    # maxref-unknown objects -> cannot judge -> allowed
    ("totally_unknown~", 0, "also_unknown", 0, True, "unknown objects are allowed"),
]


@pytest.mark.parametrize("src,so,dst,di,expect,note", MATRIX)
def test_validate_connection_matrix(src, so, dst, di, expect, note):
    valid, msg = validate_connection(src, so, dst, di)
    assert valid is expect, f"{note}: {src}[{so}]->{dst}[{di}] expected {expect} ({msg})"
    if not expect:
        assert msg, "an error must carry a message"


def test_arg_dependent_ports_are_understood():
    # limi~ 2 has 2 inlets/outlets; a connection to the second must be allowed
    valid, _ = validate_connection("limi~", 1, "ezdac~", 1, src_text="limi~ 2")
    assert valid is True
    # but limi~ with no arg defaults to 1 outlet
    valid, _ = validate_connection("limi~", 1, "ezdac~", 1, src_text="limi~")
    assert valid is False


def test_add_line_raises_when_validation_enabled():
    p = Patcher(validate_connections=True)
    metro = p.add_textbox("metro 500")
    osc = p.add_textbox("cycle~ 440")
    with pytest.raises(InvalidConnectionError):
        p.add_line(metro, osc)


def test_add_line_allows_valid_when_validation_enabled():
    p = Patcher(validate_connections=True)
    freq = p.add_floatbox()
    osc = p.add_textbox("cycle~ 440")
    gain = p.add_textbox("gain~")
    p.add_line(freq, osc)  # float -> freq inlet
    p.add_line(osc, gain)  # signal -> signal
    assert len(p._lines) == 2
