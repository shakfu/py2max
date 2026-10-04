import math

import pytest

from py2max.utils import parse_attr_args, pitch2freq


def test_pitch2freq_accepts_sharp_equivalents():
    assert math.isclose(pitch2freq("A#3"), pitch2freq("Bb3"), rel_tol=1e-9)


def test_pitch2freq_handles_multi_digit_octaves():
    assert pitch2freq("C10") > pitch2freq("C9")


def test_pitch2freq_rejects_invalid_note():
    with pytest.raises(ValueError):
        pitch2freq("H2")


@pytest.mark.parametrize(
    "tokens,expected",
    [
        ([], ([], {})),
        (["a", "2"], (["a", "2"], {})),
        (["@size", "3"], ([], {"size": 3})),
        (["@x", "-1.5", "@name", "foo"], ([], {"x": -1.5, "name": "foo"})),
        (["@color", "1", "0", "0", "1"], ([], {"color": [1, 0, 0, 1]})),
        (["@flag"], ([], {"flag": []})),
        (["a", "@size", "3"], (["a"], {"size": 3})),
    ],
)
def test_parse_attr_args(tokens, expected):
    assert parse_attr_args(tokens) == expected
