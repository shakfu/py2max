"""Tests for py2max.utils.kwds_filter.

``kwds_filter(kwds, **elems)`` lets a method keep an optional parameter in its
signature but drop it from the forwarded ``**kwds`` when it was left unset
(``None``), so unset options never reach the serialized patch.
"""

from py2max.utils import kwds_filter


def f(x, y=None, **kwds):
    return (x, y, kwds)


def eg_kwds_filter(x, y=None, z=None, **kwds):
    # keep ``z`` in the signature but forward it only when set
    return f(x, y, **kwds_filter(kwds, z=z))


def test_t1_kwds_filter():
    assert eg_kwds_filter("a", 1) == ("a", 1, {})


def test_t2_kwds_filter():
    assert eg_kwds_filter("a", 1, z=10) == ("a", 1, {"z": 10})


def test_t3_kwds_filter():
    assert eg_kwds_filter("a", 1, z=None) == ("a", 1, {})


def test_t4_kwds_filter():
    assert eg_kwds_filter("a", 1, z=None, h=20) == ("a", 1, {"h": 20})


def test_t5_kwds_filter():
    assert eg_kwds_filter("a", 1, z=1, h=20) == ("a", 1, {"h": 20, "z": 1})


def test_kwds_filter_keeps_falsy_non_none():
    # 0 / "" are legitimate values and must be kept (unlike the old truthy filter)
    assert kwds_filter({}, a=0, b="", c=None, d=5) == {"a": 0, "b": "", "d": 5}


def test_kwds_filter_does_not_mutate_input():
    kwds = {"x": 1}
    result = kwds_filter(kwds, y=2)
    assert result == {"x": 1, "y": 2}
    assert kwds == {"x": 1}  # original untouched
