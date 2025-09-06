"""Abstract base classes for py2max core objects.

This module defines abstract base classes to break circular dependencies
between core.py and layout.py modules.
"""

from abc import ABC, abstractmethod
from typing import Optional, Union, Callable
from pathlib import Path

from .common import Rect


class AbstractLayoutManager(ABC):
    """Abstract base class for LayoutManager objects.
    
    This class defines the interface that layout managers expect from
    a LayoutManager object, allowing layout.py to reference LayoutManager without
    creating circular imports.
    """

    @abstractmethod
    def get_rect_from_maxclass(self, maxclass: str) -> Optional[Rect]:
        """retrieves default patching_rect from defaults dictionary."""
        pass

    @abstractmethod
    def get_relative_pos(self, rect: Rect) -> Rect:
        """returns a relative position for the object"""
        pass
    
    @abstractmethod
    def get_absolute_pos(self, rect: Rect) -> Rect:
        """returns an absolute position for the object"""
        pass
    
    @abstractmethod
    def get_pos(self, maxclass: Optional[str] = None) -> Rect:
        """get box rect (position) via maxclass or layout_manager"""
        pass


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


class AbstractPatchline(ABC):
    """Abstract base class for Patchline objects.
    
    This class defines the interface that layout managers expect from
    a Patchline object, allowing layout.py to reference Patchline without
    creating circular imports.
    """
    
    src: AbstractBox
    dst: AbstractBox


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
        pass
    
    @property
    @abstractmethod
    def height(self) -> float:
        """Height of patcher window."""
        pass
    
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
    _maxclass_methods: dict[str, Callable[[], AbstractBox]]


