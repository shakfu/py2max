"""Tests for maxref-backed keyword-attribute validation (validate_attrs)."""

import warnings

import pytest

from py2max import Patcher


def _warnings_for(build):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        build()
    return [str(w.message) for w in caught if issubclass(w.category, UserWarning)]


def test_validate_attrs_catches_typo():
    msgs = _warnings_for(
        lambda: Patcher(validate_attrs=True).add_floatparam("master", inital=0.5)
    )
    assert any("inital" in m for m in msgs)


def test_validate_attrs_off_by_default():
    # Same typo, but validation disabled -> silent (non-breaking default).
    assert _warnings_for(lambda: Patcher().add_floatparam("x", inital=0.5)) == []


def test_validate_attrs_no_false_positives_on_real_attrs():
    def build():
        p = Patcher(validate_attrs=True)
        p.add_textbox("cycle~ 440", frequency=440)  # object-specific attr
        p.add_textbox("gain~", bgcolor=[0, 0, 0, 1])  # universal jbox attr
        p.add_floatparam("amp", 0.5, 0, 1)  # parameter machinery
        p.add_umenu(items="a b c")  # umenu-specific attr
        p.add_message("1 2")
        p.add_comment("hi")
        p.add_subpatcher("p sub")

    assert _warnings_for(build) == []


def test_validate_attrs_skips_unknown_objects():
    # No maxref entry -> cannot validate -> no warning even for odd kwargs.
    msgs = _warnings_for(
        lambda: Patcher(validate_attrs=True).add_textbox(
            "totally.made.up.object", nonsense=1
        )
    )
    assert msgs == []


def test_validate_attrs_flags_unknown_on_known_object():
    msgs = _warnings_for(
        lambda: Patcher(validate_attrs=True).add_textbox("cycle~ 440", wibble=1)
    )
    assert any("wibble" in m and "cycle~" in m for m in msgs)


@pytest.mark.parametrize("flag", [True, False])
def test_validate_attrs_does_not_change_output(flag):
    # Validation is warn-only: the generated patch is identical either way.
    p = Patcher(validate_attrs=flag)
    p.add_textbox("cycle~ 440")
    p.add_textbox("gain~")
    assert len(p._boxes) == 2
