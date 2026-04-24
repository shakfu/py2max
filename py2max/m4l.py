"""Max for Live (M4L) helpers: presentation mode and device constraints.

Reference: https://github.com/shakfu/py2max/issues/9

M4L devices live in a fixed-size device strip in Ableton Live. The patcher
renders in *presentation mode* (not patching mode), so each UI object must
be explicitly marked with ``presentation=1`` and given a ``presentation_rect``.
Infrastructure objects (``live.remote~``, ``live.map``, etc.) stay hidden.

Ableton's device view also imposes these constraints:
- Device strip height is fixed at ~170 px by the host.
- Coordinates should be whole integers; fractional values render blurry on
  non-retina displays.
- ``devicewidth`` on the patcher controls the device strip width.
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Iterable, List, Tuple, Union

if TYPE_CHECKING:
    from .core import Box, Patcher


# ---------------------------------------------------------------------------
# Object classification for presentation-mode filtering
#
# Only user-facing controls belong in the device strip. Infrastructure
# objects (Live API bridges, routing, device lifecycle) stay in the patcher
# but must not get presentation=1.

M4L_PRESENTATION_UI_CLASSES: frozenset = frozenset(
    {
        "live.dial",
        "live.numbox",
        "live.slider",
        "live.menu",
        "live.tab",
        "live.text",
        "live.toggle",
        "live.button",
        "live.comment",
        "live.gain~",
        "live.step",
        "live.grid",
        "live.meter~",
        "live.scope~",
        # Classic (non-live.*) UI that also works in presentation
        "dial",
        "number",
        "flonum",
        "toggle",
        "button",
        "comment",
        "panel",
        "umenu",
        "slider",
    }
)

M4L_INFRASTRUCTURE_CLASSES: frozenset = frozenset(
    {
        "live.remote~",
        "live.map",
        "live.object",
        "live.path",
        "live.observer",
        "live.thisdevice",
        "live.banks",
        "live.parameter",
    }
)

# Ableton's device view height is fixed; devicewidth is the one dim you set.
M4L_DEVICE_HEIGHT_PX = 170


# ---------------------------------------------------------------------------
# Integer-coordinate guardrail


class NonIntegerCoordinateWarning(UserWarning):
    """Emitted when a rect contains fractional coordinates."""


def _to_int_rect(
    rect: Iterable[Union[int, float]], *, context: str
) -> List[int]:
    """Coerce a 4-tuple rect to ints, warning on non-integer inputs."""
    values = list(rect)
    if len(values) != 4:
        raise ValueError(f"rect must have 4 elements, got {len(values)}: {values}")

    rounded = []
    had_float = False
    for v in values:
        if isinstance(v, float) and not v.is_integer():
            had_float = True
        rounded.append(int(round(float(v))))

    if had_float:
        warnings.warn(
            f"M4L: non-integer coords in {context} {values} -> {rounded}; "
            "Ableton renders decimals blurry on non-retina.",
            NonIntegerCoordinateWarning,
            stacklevel=3,
        )
    return rounded


# ---------------------------------------------------------------------------
# Classification helpers


def _object_name(box: "Box") -> str:
    """Resolve the effective object name for classification.

    Native-maxclass objects (live.dial, toggle, etc.) carry the name in
    ``maxclass``. ``newobj`` boxes carry it as the first token of ``text``.
    """
    if box.maxclass and box.maxclass != "newobj":
        return box.maxclass
    text = getattr(box, "text", "") or ""
    return text.split()[0] if text else box.maxclass or ""


def is_presentation_ui(box: "Box") -> bool:
    """True if the box is a user-facing control suitable for presentation."""
    return _object_name(box) in M4L_PRESENTATION_UI_CLASSES


def is_m4l_infrastructure(box: "Box") -> bool:
    """True if the box is M4L infrastructure that must stay hidden."""
    return _object_name(box) in M4L_INFRASTRUCTURE_CLASSES


# ---------------------------------------------------------------------------
# Public API


def add_to_presentation(
    box: "Box",
    rect: Union[Iterable[Union[int, float]], Tuple[int, int, int, int]],
    *,
    strict: bool = False,
) -> "Box":
    """Mark a box as a presentation-mode UI element.

    Sets ``presentation=1`` and ``presentation_rect=[x, y, w, h]``. Rounds
    fractional coordinates to integers with a warning. Refuses known
    infrastructure objects (``live.remote~`` etc.), which must not appear in
    the device strip.

    Args:
        box: the Box to expose in presentation mode.
        rect: [x, y, width, height] in device-strip coordinates.
        strict: if True, warn when the box is not a recognized UI class.
            Useful to catch typos early; defaults to False so user-defined
            or unusual UI objects still work.
    """
    if is_m4l_infrastructure(box):
        raise ValueError(
            f"refusing to add {_object_name(box)!r} to presentation: it is "
            "M4L infrastructure and must stay hidden from the device strip."
        )

    if strict and not is_presentation_ui(box):
        warnings.warn(
            f"M4L: {_object_name(box)!r} is not a known presentation UI class; "
            "it may still work but is unusual in a device strip.",
            UserWarning,
            stacklevel=2,
        )

    int_rect = _to_int_rect(rect, context=f"{_object_name(box)} presentation_rect")

    # These are patcher-level attributes on the box dict.
    box.presentation = 1  # type: ignore[attr-defined]
    box.presentation_rect = int_rect  # type: ignore[attr-defined]
    return box


def enable_presentation(
    patcher: "Patcher",
    devicewidth: Union[int, None] = None,
) -> "Patcher":
    """Configure a patcher to open in presentation mode as an M4L device.

    Sets ``openinpresentation=1`` and optionally ``devicewidth`` (px).
    Ableton's device strip height is fixed at ~170 px; only width is
    author-controlled.
    """
    patcher.openinpresentation = 1  # type: ignore[attr-defined]
    if devicewidth is not None:
        patcher.devicewidth = int(round(devicewidth))  # type: ignore[attr-defined]
    return patcher


def enforce_integer_coords(patcher: "Patcher") -> int:
    """Walk a patcher and round all rect coords to integers.

    Returns the number of rects that were non-integer (and got rounded).
    Recurses into nested subpatchers.
    """
    def _round_rect(rect):
        """Round a rect in-place. Returns 1 if any coord was non-integer."""
        # Rect dataclass with .x/.y/.w/.h or a plain [x,y,w,h] list.
        if hasattr(rect, "x"):
            coords = [rect.x, rect.y, rect.w, rect.h]
            if any(isinstance(v, float) and not v.is_integer() for v in coords):
                rect.x, rect.y, rect.w, rect.h = (int(round(v)) for v in coords)
                return 1
        elif isinstance(rect, list):
            if any(isinstance(v, float) and not v.is_integer() for v in rect):
                rect[:] = [int(round(v)) for v in rect]
                return 1
        return 0

    changed = 0
    for box in patcher._boxes:
        pr = getattr(box, "patching_rect", None)
        if pr is not None:
            changed += _round_rect(pr)

        if hasattr(box, "presentation_rect"):
            changed += _round_rect(box.presentation_rect)

        sub = getattr(box, "_patcher", None)
        if sub is not None:
            changed += enforce_integer_coords(sub)

    return changed


__all__ = [
    "M4L_PRESENTATION_UI_CLASSES",
    "M4L_INFRASTRUCTURE_CLASSES",
    "M4L_DEVICE_HEIGHT_PX",
    "NonIntegerCoordinateWarning",
    "is_presentation_ui",
    "is_m4l_infrastructure",
    "add_to_presentation",
    "enable_presentation",
    "enforce_integer_coords",
]
