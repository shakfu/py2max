"""Common data structures and utilities for py2max.

This module contains shared data structures used throughout the py2max library.
"""

from typing import Any, Dict, NamedTuple


class Rect(NamedTuple):
    """Rectangle data structure for object positioning.

    Represents a rectangular area in Max patch coordinates using four coordinates:
    x (horizontal position), y (vertical position), w (width), and h (height).
    """

    x: float
    y: float
    w: float
    h: float


# Keys whose values carry ``.x/.y/.w/.h`` semantics, i.e. the ones py2max reads
# attribute-wise. Deliberately excludes the other ``*rect`` props
# (``client_rect``, ``dstrect``, ``storage_rect``, ...), which are opaque
# passthrough values the library never interprets.
RECT_KEYS = ("rect", "patching_rect", "presentation_rect")


def as_rect(value: Any) -> Any:
    """Coerce a 4-element JSON array into a ``Rect``, else pass it through.

    JSON has no tuple type, so a patch read off disk carries every rect as a
    plain list. ``Box.patching_rect`` is declared ``Optional[Rect]`` and read as
    ``rect.x``/``rect.y`` by the layout managers, so leaving the list in place
    breaks ``optimize_layout()`` on any loaded patch. Anything that is not a
    4-element sequence is left untouched rather than guessed at.
    """
    if isinstance(value, (list, tuple)) and len(value) == 4:
        return Rect(*value)
    return value


def rects_to_lists(d: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize ``Rect`` values in a serialization dict back to plain lists.

    ``Rect`` is an internal convenience type; the ``.maxpat`` format has only
    JSON arrays. Both forms encode identically via ``json.dump``, but leaking a
    NamedTuple out of ``to_dict()`` makes the result compare unequal to the dict
    it was loaded from, so the mapping is undone at the serialization boundary.
    Mutates and returns ``d``, which is always a fresh copy at the call sites.
    """
    for key in RECT_KEYS:
        value = d.get(key)
        if isinstance(value, Rect):
            d[key] = list(value)
    return d


# Advance widths in 1/1000 em from the Helvetica AFM, which Arial (Max's
# default box font) matches. Unlisted characters count as 556, a digit.
_GLYPH_WIDTHS: Dict[str, int] = {
    **dict.fromkeys("0123456789#$_?", 556),
    **dict(
        zip(
            "abcdefghijklmnopqrstuvwxyz",
            (
                556,
                556,
                500,
                556,
                556,
                278,
                556,
                556,
                222,
                222,
                500,
                222,
                833,
                556,
                556,
                556,
                556,
                333,
                500,
                278,
                556,
                500,
                722,
                500,
                500,
                500,
            ),
        )
    ),
    **dict(
        zip(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
            (
                667,
                667,
                722,
                722,
                667,
                611,
                778,
                722,
                278,
                500,
                667,
                556,
                833,
                722,
                778,
                667,
                778,
                722,
                667,
                611,
                722,
                667,
                944,
                667,
                667,
                611,
            ),
        )
    ),
    " ": 278,
    "!": 278,
    '"': 355,
    "%": 889,
    "&": 667,
    "'": 191,
    "(": 333,
    ")": 333,
    "*": 389,
    "+": 584,
    ",": 278,
    "-": 333,
    ".": 278,
    "/": 278,
    ":": 278,
    ";": 278,
    "<": 584,
    "=": 584,
    ">": 584,
    "@": 1015,
    "[": 278,
    "\\": 278,
    "]": 278,
    "^": 469,
    "`": 333,
    "{": 334,
    "|": 260,
    "}": 334,
    "~": 584,
}

# Fitted on 392 Arial newobj/message boxes in 60 Max-written patches: box
# width is text width plus 10.6 px (median error 2 px), at least 15 px per
# port and 28 px overall.
_BOX_TEXT_PAD = 10.6
_BOX_PORT_WIDTH = 15.0
_BOX_MIN_WIDTH = 28.0


def text_width(text: str, fontsize: float = 12.0) -> float:
    """Rendered width in px of one line of Arial ``text``."""
    return sum(_GLYPH_WIDTHS.get(c, 556) for c in text) * fontsize / 1000


def box_width_for(text: str, ports: int = 1, fontsize: float = 12.0) -> float:
    """Width Max gives an object or message box holding ``text``."""
    longest = max(
        (text_width(line, fontsize) for line in text.split("\n")), default=0.0
    )
    return round(
        max(longest + _BOX_TEXT_PAD, _BOX_PORT_WIDTH * ports, _BOX_MIN_WIDTH), 1
    )
