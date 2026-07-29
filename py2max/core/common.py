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
