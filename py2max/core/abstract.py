"""Abstract base classes for py2max core objects.

This module defines abstract base classes to break circular dependencies
between core.py and layout.py modules.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, Optional, Union

from .common import Rect


class AbstractLayoutManager(ABC):
    """Abstract base class for LayoutManager objects.

    This class defines the interface that layout managers expect from
    a LayoutManager object, allowing layout.py to reference LayoutManager without
    creating circular imports.
    """

    # Required attributes
    box_height: float

    @abstractmethod
    def get_rect_from_maxclass(self, maxclass: str) -> Optional[Rect]:
        """retrieves default patching_rect from defaults dictionary."""
        ...

    @abstractmethod
    def get_relative_pos(self, rect: Rect) -> Rect:
        """returns a relative position for the object"""
        ...

    @abstractmethod
    def get_absolute_pos(self, rect: Rect) -> Rect:
        """returns an absolute position for the object"""
        ...

    @abstractmethod
    def get_pos(self, maxclass: Optional[str] = None) -> Rect:
        """get box rect (position) via maxclass or layout_manager"""
        ...

    @abstractmethod
    def above(self, rect: Rect) -> Rect:
        """Return a position of a comment above the object"""
        ...


class AbstractBox(ABC):
    """Abstract base class for Box objects.

    This class defines the interface that layout managers expect from
    a Box object, allowing layout.py to reference Box without
    creating circular imports.
    """

    # These are instance attributes, not properties
    id: Optional[str]
    maxclass: str
    patching_rect: Rect
    _kwds: Dict[str, Any]

    @abstractmethod
    def render(self) -> None:
        """Render the box object."""
        ...

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert the box to a dictionary representation."""
        ...

    @abstractmethod
    def __iter__(self) -> Iterator[Any]:
        """Make the box iterable."""
        ...


class AbstractPatchline(ABC):
    """Abstract base class for Patchline objects.

    This class defines the interface that layout managers expect from
    a Patchline object, allowing layout.py to reference Patchline without
    creating circular imports.
    """

    @property
    @abstractmethod
    def src(self) -> str:
        """Source object identifier."""
        ...

    @property
    @abstractmethod
    def dst(self) -> str:
        """Destination object identifier."""
        ...

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert the patchline to a dictionary representation."""
        ...


class AbstractPatcher(ABC):
    """Abstract base class for Patcher objects.

    This class defines the interface that layout managers expect from
    a Patcher object, allowing layout.py to reference Patcher without
    creating circular imports.
    """

    @property
    @abstractmethod
    def width(self) -> float:
        """Width of patcher window."""
        ...

    @property
    @abstractmethod
    def height(self) -> float:
        """Height of patcher window."""
        ...

    # rect is an instance attribute, not a property
    rect: Rect

    _path: Optional[Union[str, Path]]
    _parent: Optional["AbstractPatcher"]
    _node_ids: list[str]
    _objects: dict[str, AbstractBox]
    _boxes: list[AbstractBox]
    _lines: list[AbstractPatchline]
    _edge_ids: list[tuple[str, str]]
    _id_counter: int = 0
    _link_counter: int = 0
    _last_link: Optional[tuple[str, str]]
    _reset_on_render: bool
    _flow_direction: str
    _cluster_connected: bool
    _layout_mgr: AbstractLayoutManager
    _auto_hints: bool
    _validate_connections: bool
    _maxclass_methods: dict[str, Callable[..., Any]]
    _semantic_ids: bool
    _semantic_counters: dict[str, int]
    _device_type: str
    classnamespace: str
    _pending_comments: list[tuple[str, str, Optional[str]]]
    # Rendered (dict) forms, populated by render() and read by serialization.
    boxes: list[dict[str, Any]]
    lines: list[dict[str, Any]]

    # Core methods implemented by Patcher and relied on by the BoxFactory and
    # serialization mixins. Declared here (non-abstract) so each mixin can be
    # type-checked in isolation; Patcher provides the real implementations.
    def get_id(self, object_name: Optional[str] = None) -> str:
        """Generate an object id (implemented by Patcher)."""
        raise NotImplementedError

    def get_pos(self, maxclass: Optional[str] = None) -> Rect:
        """Get a box position from the layout manager (implemented by Patcher)."""
        raise NotImplementedError

    def render(self, reset: bool = False) -> None:
        """Render boxes/lines to dicts (implemented by Patcher)."""
        raise NotImplementedError

    def _process_pending_comments(self) -> None:
        """Position deferred associated comments (implemented by Patcher)."""
        raise NotImplementedError
