"""Box class for representing Max objects in a patch."""

from typing import TYPE_CHECKING, List, Optional

from .abstract import AbstractBox
from .common import Rect

if TYPE_CHECKING:
    from .patcher import Patcher


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
        **kwds,
    ):
        self.id = id
        self.maxclass = maxclass or "newobj"
        self.numinlets = numinlets or 0
        self.numoutlets = numoutlets or 1
        # self.outlettype = outlettype
        self.patching_rect = patching_rect or Rect(0, 0, 62, 22)

        self._kwds = self._remove_none_entries(kwds)
        self._patcher: Optional["Patcher"] = self._kwds.pop("patcher", None)

    def _remove_none_entries(self, kwds):
        """removes items in the dict which have None values.

        TODO: make recursive in case of nested dicts.
        """
        return {k: v for k, v in kwds.items() if v is not None}

    def __iter__(self):
        yield self
        if self._patcher:
            yield from iter(self._patcher)

    def __repr__(self):
        return f"{self.__class__.__name__}(id='{self.id}', maxclass='{self.maxclass}')"

    def __pt_repr__(self):
        """Custom representation for ptpython REPL.

        Provides rich colored output when displaying objects in the ptpython REPL.
        Shows object type, ID, position, and text content in a readable format.
        """
        from prompt_toolkit.formatted_text import HTML

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

    def render(self):
        """convert self and children to dictionary."""
        if self._patcher:
            self._patcher.render()
            self.patcher = self._patcher.to_dict()

    def to_dict(self):
        """create dict from object with extra kwds included"""
        d = vars(self).copy()
        to_del = [k for k in d if k.startswith("_")]
        for k in to_del:
            del d[k]
        d.update(self._kwds)
        return dict(box=d)

    @classmethod
    def from_dict(cls, obj_dict):
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
        """numerical part of object id as int"""
        if self.id:
            return int(self.id[4:])
        return None

    @property
    def subpatcher(self):
        """synonym for parent patcher object"""
        return self._patcher

    @property
    def text(self):
        """Get the text content of the box."""
        # Check if text is stored as a direct attribute (from file loading)
        if "text" in self.__dict__:
            return self.__dict__["text"]
        # Otherwise get from _kwds (from programmatic creation)
        return self._kwds.get("text", "")

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

    def get_info(self) -> Optional[dict]:
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
        """Get the actual object name for this Box.

        For 'newobj' maxclass objects, extract the first word from the text field.
        For other objects, use the maxclass directly.
        """
        if self.maxclass == "newobj":
            # Text is stored in _kwds for Box objects
            text = self._kwds.get("text", "")
            if text:
                # Extract the first word from text (the object name)
                return text.split()[0] if text.split() else self.maxclass
        return self.maxclass
