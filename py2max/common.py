"""Common data structures and utilities for py2max.

This module contains shared data structures used throughout the py2max library.
"""

from typing import NamedTuple


class Rect(NamedTuple):
    """Rectangle data structure for object positioning.

    Represents a rectangular area in Max patch coordinates using four coordinates:
    x (horizontal position), y (vertical position), w (width), and h (height).
    """
    x: float
    y: float
    w: float
    h: float
