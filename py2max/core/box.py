"""Box class for representing Max objects in a patch."""

# Annotations are postponed so ``Unpack[BoxProps]`` can be written in signatures
# without importing ``typing_extensions`` at runtime -- the library ships zero
# runtime dependencies, and PEP 692 is only a 3.12 runtime feature.
from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Mapping, Optional

from .abstract import AbstractBox
from .common import Rect
from .props import BoxProps

if TYPE_CHECKING:
    from typing_extensions import Unpack

    from .colors import ColorLike
    from .patcher import Patcher


def _scrub(value: Any) -> Any:
    """Recursively drop None-valued keys from any dicts inside `value`.

    Lists are walked but not filtered: a None *element* is positional (an
    `outlettype` slot, say) and dropping it would change the arity. Tuples are
    left alone so `Rect`, a NamedTuple, survives as itself.
    """
    if isinstance(value, Mapping):
        return _scrub_mapping(value)
    if isinstance(value, list):
        return [_scrub(item) for item in value]
    return value


def _scrub_mapping(mapping: Mapping[str, Any]) -> Dict[str, Any]:
    return {k: _scrub(v) for k, v in mapping.items() if v is not None}


class Box(AbstractBox):
    """Represents a Max object in a patch.

    The Box class encapsulates a single Max object with its properties,
    position, and connections. It provides methods for introspection
    and help information.

    Args:
        maxclass: Max object class name (e.g., 'newobj', 'flonum').
        numinlets: Number of input connections.
        numoutlets: Number of output connections.
        id: Unique identifier for the object.
        patching_rect: Position and size rectangle.
        **kwds: Additional Max object properties.

    Attributes:
        id: Unique identifier for the object.
        maxclass: Max object class name.
        numinlets: Number of input connections.
        numoutlets: Number of output connections.
        patching_rect: Position and size as Rect.
    """

    def __init__(
        self,
        maxclass: Optional[str] = None,
        numinlets: Optional[int] = None,
        numoutlets: Optional[int] = None,
        id: Optional[str] = None,
        patching_rect: Optional[Rect] = None,
        **kwds: "Unpack[BoxProps]",
    ) -> None:
        self.id = id
        self.maxclass = maxclass or "newobj"
        # `x if x is not None else default`, not `x or default`: an explicit 0 is
        # meaningful (an object with no outlets cannot be a connection source,
        # and a subpatcher with no `outlet` objects genuinely has none), but it
        # is falsy, so `or` silently promoted it to the default.
        self.numinlets = numinlets if numinlets is not None else 0
        self.numoutlets = numoutlets if numoutlets is not None else 1
        # self.outlettype = outlettype
        self.patching_rect = patching_rect or Rect(0, 0, 62, 22)

        self._kwds = self._remove_none_entries(kwds)
        self._patcher: Optional["Patcher"] = self._kwds.pop("patcher", None)

    def _remove_none_entries(self, kwds: Mapping[str, Any]) -> Dict[str, Any]:
        """Drop keys whose value is None, at any depth.

        Max distinguishes an absent key from a null one, and an unset optional
        argument arrives here as None -- so a key that was never asked for must
        not be written as ``"key": null``.

        Nested dicts are scrubbed too: `saved_attribute_attributes` is built
        with optional members, so a shallow pass left `"parameter_mmax": null`
        one level down where nothing would ever remove it.

        Takes a ``Mapping`` rather than a ``dict`` so a ``BoxProps`` TypedDict
        can be passed straight in; TypedDicts are ``Mapping[str, object]``, not
        ``dict[str, Any]``.
        """
        return _scrub_mapping(kwds)

    def __iter__(self) -> Iterator[Any]:
        yield self
        if self._patcher:
            yield from iter(self._patcher)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id='{self.id}', maxclass='{self.maxclass}')"

    def __pt_repr__(self) -> Any:
        """Custom representation for ptpython REPL.

        Provides rich colored output when displaying objects in the ptpython REPL.
        Shows object type, ID, position, and text content in a readable format.

        prompt_toolkit is not a dependency of py2max core; this hook only fires
        under ptpython (which provides it). Fall back to plain repr otherwise.
        """
        try:
            from prompt_toolkit.formatted_text import HTML  # type: ignore[import-not-found]
        except ImportError:
            return repr(self)

        # Get object details
        obj_type = self.maxclass or "newobj"
        obj_id = self.id or "unknown"
        text = getattr(self, "text", None) or ""

        # Get position
        rect = self.patching_rect
        if rect:
            pos = f"[{rect.x:.0f}, {rect.y:.0f}]"
        else:
            pos = "[?, ?]"

        # Build colored representation
        if text:
            return HTML(
                f"<ansigreen>{obj_type}</ansigreen> "
                f"<ansicyan>{obj_id}</ansicyan> "
                f"at {pos}: <ansiyellow>'{text}'</ansiyellow>"
            )
        else:
            return HTML(
                f"<ansigreen>{obj_type}</ansigreen> "
                f"<ansicyan>{obj_id}</ansicyan> "
                f"at {pos}"
            )

    def render(self) -> None:
        """convert self and children to dictionary."""
        if self._patcher:
            self._sync_subpatcher_ports()
            self._patcher.render()
            self.patcher = self._patcher.to_dict()

    def _sync_subpatcher_ports(self) -> None:
        """Match this box's port counts to the ``inlet``/``outlet`` objects inside.

        A subpatcher box's real port count is however many ``inlet`` / ``outlet``
        objects its nested patcher holds, and those are usually added *after* the
        box itself, so the counts fixed at construction time go stale. Max shows
        a box's declared ports, so a two-outlet subpatcher declaring one outlet
        emits a patch whose second outlet cannot be connected.

        Deliberately conservative: the counts are only overwritten for a
        dimension that actually found objects to count. A nested patcher can hold
        I/O this cannot interpret -- ``gen~`` and ``rnbo~`` declare theirs with
        ``in``/``out`` objects, and an empty subpatcher is a stub the caller has
        yet to fill -- and zeroing those boxes' ports would be worse than leaving
        the constructed default alone.
        """
        from py2max.maxref.porttypes import subpatcher_counts

        n_in, n_out = subpatcher_counts(self)
        if n_in:
            self.numinlets = n_in
        if n_out:
            self.numoutlets = n_out
            self._kwds["outlettype"] = [""] * n_out

    def to_dict(self) -> Dict[str, Any]:
        """create dict from object with extra kwds included"""
        d = vars(self).copy()
        to_del = [k for k in d if k.startswith("_")]
        for k in to_del:
            del d[k]
        d.update(self._kwds)
        return dict(box=d)

    @classmethod
    def from_dict(cls, obj_dict: Dict[str, Any]) -> "Box":
        """create instance from dict"""
        box = cls()
        box.__dict__.update(obj_dict)
        if hasattr(box, "patcher"):
            # Lazy import to avoid circular dependency
            from .patcher import Patcher

            box._patcher = Patcher.from_dict(getattr(box, "patcher"))
        return box

    @property
    def oid(self) -> Optional[int]:
        """Trailing numeric part of the object id, or None if it has none.

        Works for numeric ids (``obj-5`` -> 5) and semantic ids
        (``cycle_1`` -> 1).
        """
        if not self.id:
            return None
        match = re.search(r"\d+$", self.id)
        return int(match.group()) if match else None

    @property
    def subpatcher(self) -> Optional["Patcher"]:
        """synonym for parent patcher object"""
        return self._patcher

    @property
    def text(self) -> Any:
        """Get the text content of the box."""
        # Check if text is stored as a direct attribute (from file loading)
        if "text" in self.__dict__:
            return self.__dict__["text"]
        # Otherwise get from _kwds (from programmatic creation)
        return self._kwds.get("text", "")

    def set_color(
        self,
        bg: Optional["ColorLike"] = None,
        text: Optional["ColorLike"] = None,
        border: Optional["ColorLike"] = None,
    ) -> "Box":
        """Set this box's colors, returning self for chaining.

        Each argument accepts a named color (e.g. ``"red"``), a hex string
        (``"#ff8800"``), or an ``[r, g, b(, a)]`` float sequence (0..1). Sets the
        ``bgcolor`` / ``textcolor`` / ``bordercolor`` attributes respectively.

        Example:
            >>> p.add_textbox("toggle").set_color(bg="blue", text="white")
        """
        from .colors import resolve_color

        if bg is not None:
            self._kwds["bgcolor"] = resolve_color(bg)
        if text is not None:
            self._kwds["textcolor"] = resolve_color(text)
        if border is not None:
            self._kwds["bordercolor"] = resolve_color(border)
        return self

    def add_to_presentation(
        self,
        rect: Any,
        *,
        strict: bool = False,
    ) -> "Box":
        """Mark this box as a presentation-mode UI element (Max for Live).

        Sets ``presentation=1`` and ``presentation_rect`` on the box. Rounds
        fractional coordinates to integers with a warning. Raises if the box
        is M4L infrastructure (``live.remote~``, ``live.map``, etc.) that
        must stay hidden from the device strip.

        Args:
            rect: [x, y, width, height] in device-strip coordinates.
            strict: if True, warn when this isn't a known UI class.
        """
        from py2max.m4l import add_to_presentation

        return add_to_presentation(self, rect, strict=strict)

    def help_text(self) -> str:
        """Get formatted help documentation for this Max object.

        Returns:
            Formatted help string with object documentation from .maxref.xml files.
        """
        from py2max import maxref

        return maxref.get_object_help(self.maxclass)

    def help(self) -> None:
        """Print formatted help documentation for this Max object."""
        print(self.help_text())

    def get_info(self) -> Optional[Dict[str, Any]]:
        """Get complete object information from .maxref.xml files.

        Returns:
            Dictionary with complete object information or None if not found.
        """
        from py2max import maxref

        return maxref.get_object_info(self.maxclass)

    def get_inlet_count(self) -> Optional[int]:
        """Get the number of inlets for this object from maxref data.

        Returns:
            Number of inlets or None if unknown.
        """
        from py2max.maxref import get_inlet_count

        object_name = self._get_object_name()
        return get_inlet_count(object_name)

    def get_outlet_count(self) -> Optional[int]:
        """Get the number of outlets for this object from maxref data.

        Returns:
            Number of outlets or None if unknown.
        """
        from py2max.maxref import get_outlet_count

        object_name = self._get_object_name()
        return get_outlet_count(object_name)

    def get_inlet_types(self) -> List[str]:
        """Get the inlet types for this object from maxref data

        Returns:
            List of inlet type strings
        """
        from py2max.maxref import get_inlet_types

        object_name = self._get_object_name()
        return get_inlet_types(object_name)

    def get_outlet_types(self) -> List[str]:
        """Get the outlet types for this object from maxref data

        Returns:
            List of outlet type strings
        """
        from py2max.maxref import get_outlet_types

        object_name = self._get_object_name()
        return get_outlet_types(object_name)

    def _get_object_name(self) -> str:
        """Get the actual Max object name for this Box (see utils.object_name)."""
        from ..utils import object_name

        return object_name(self)
