import math

import pytest

from py2max.utils import pitch2freq


def test_pitch2freq_accepts_sharp_equivalents():
    assert math.isclose(pitch2freq("A#3"), pitch2freq("Bb3"), rel_tol=1e-9)


def test_pitch2freq_handles_multi_digit_octaves():
    assert pitch2freq("C10") > pitch2freq("C9")


def test_pitch2freq_rejects_invalid_note():
    with pytest.raises(ValueError):
        pitch2freq("H2")
