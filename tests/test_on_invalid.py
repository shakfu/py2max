"""Connection-validation policy: Patcher(on_invalid=...)."""

import logging

import pytest

from py2max import InvalidConnectionError, Patcher


def _bad_link(p):
    """metro -> cycle~ inlet 0: a bang into a signal-only inlet."""
    return p.add_line(p.add_textbox("metro 500"), p.add_textbox("cycle~ 440"))


def test_default_warns_and_adds_the_cord(caplog):
    p = Patcher()
    with caplog.at_level(logging.WARNING):
        _bad_link(p)
    assert len(p._lines) == 1
    assert "Invalid connection from metro[0] to cycle~[0]" in caplog.text


def test_valid_connection_logs_nothing(caplog):
    p = Patcher()
    with caplog.at_level(logging.WARNING):
        p.add_line(p.add_textbox("cycle~ 440"), p.add_textbox("ezdac~"))
    assert "Invalid connection" not in caplog.text


@pytest.mark.parametrize(
    "kwargs", [{"on_invalid": "raise"}, {"validate_connections": True}]
)
def test_raise_policy(kwargs):
    p = Patcher(**kwargs)
    with pytest.raises(InvalidConnectionError, match="metro"):
        _bad_link(p)
    assert p._lines == []


@pytest.mark.parametrize(
    "kwargs", [{"on_invalid": "ignore"}, {"validate_connections": False}]
)
def test_ignore_policy(kwargs, caplog):
    p = Patcher(**kwargs)
    with caplog.at_level(logging.WARNING):
        _bad_link(p)
    assert len(p._lines) == 1
    assert "Invalid connection" not in caplog.text


def test_missing_object_warns_by_default(caplog):
    p = Patcher()
    box = p.add_textbox("cycle~ 440")
    with caplog.at_level(logging.WARNING):
        p.add_patchline(box.id, 0, "obj-404", 0)
    assert "Destination object not found: obj-404" in caplog.text


def test_unknown_policy_is_rejected():
    with pytest.raises(ValueError, match="on_invalid"):
        Patcher(on_invalid="explode")


def test_conflicting_spellings_are_rejected():
    with pytest.raises(ValueError, match="conflicts"):
        Patcher(validate_connections=True, on_invalid="warn")


def test_agreeing_spellings_are_accepted():
    assert Patcher(validate_connections=True, on_invalid="raise")._on_invalid == "raise"


@pytest.mark.parametrize("policy", ["warn", "raise", "ignore"])
def test_subpatcher_inherits_policy(policy):
    sp = Patcher(on_invalid=policy).add_subpatcher("p sub")
    assert sp._patcher._on_invalid == policy


def test_subpatcher_inherits_validate_attrs():
    sp = Patcher(validate_attrs=False).add_subpatcher("p sub")
    assert sp._patcher._validate_attrs is False


def test_encapsulate_does_not_reraise_existing_faults():
    p = Patcher(on_invalid="ignore")
    metro, osc = p.add_textbox("metro 500"), p.add_textbox("cycle~ 440")
    p.add_line(metro, osc)
    p._on_invalid, p._validate_connections = "raise", True
    p.encapsulate([osc], text="p osc")  # must not raise on the old metro cord
    assert p._on_invalid == "raise"
