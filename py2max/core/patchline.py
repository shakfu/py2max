"""Patchline class for representing connections between Max objects."""

from typing import Optional, Tuple, Union

from .abstract import AbstractPatchline


class Patchline(AbstractPatchline):
    """Represents a connection between two Max objects.

    A Patchline connects an outlet of one object to an inlet of another,
    enabling signal or message flow between objects in a patch.

    Args:
        source: Source connection as [object_id, outlet_index].
        destination: Destination connection as [object_id, inlet_index].
        **kwds: Additional patchline properties.

    Attributes:
        source: Source object ID and outlet index.
        destination: Destination object ID and inlet index.
    """

    def __init__(
        self, source: Optional[list] = None, destination: Optional[list] = None, **kwds
    ):
        self.source = source or []
        self.destination = destination or []
        self._kwds = kwds

    def __repr__(self):
        return f"Patchline({self.source} -> {self.destination})"

    @property
    def src(self):
        """first object from source list"""
        return self.source[0]

    @property
    def dst(self):
        """first object from destination list"""
        return self.destination[0]

    def to_tuple(self) -> Tuple[str, str, str, str, Union[str, int]]:
        """Return a tuple describing the patchline."""
        return (
            self.source[0],
            self.source[1],
            self.destination[0],
            self.destination[1],
            self._kwds.get("order", 0),
        )

    def to_dict(self):
        """create dict from object with extra kwds included"""
        d = vars(self).copy()
        to_del = [k for k in d if k.startswith("_")]
        for k in to_del:
            del d[k]
        d.update(self._kwds)
        return dict(patchline=d)

    @classmethod
    def from_dict(cls, obj_dict: dict):
        """convert to`Patchline` object from dict"""
        patchline = cls()
        patchline.__dict__.update(obj_dict)
        return patchline
