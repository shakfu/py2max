"""Core patcher functionality for py2max.

This subpackage contains the core classes for creating and managing Max/MSP patches:

- Patcher: Core class for creating and managing Max patches
- Box: Represents individual Max objects
- Patchline: Represents connections between objects
- Rect: Rectangle data structure for positioning

Abstract base classes are also provided for type checking and interface definitions.
"""

from py2max.exceptions import InvalidConnectionError

from .abstract import (
    AbstractBox,
    AbstractLayoutManager,
    AbstractPatcher,
    AbstractPatchline,
)
from .box import Box
from .common import Rect
from .patcher import Patcher
from .patchline import Patchline

__all__ = [
    # Core classes
    "Patcher",
    "Box",
    "Patchline",
    "Rect",
    # Abstract base classes
    "AbstractPatcher",
    "AbstractBox",
    "AbstractPatchline",
    "AbstractLayoutManager",
    # Backward compatibility - exceptions re-exported
    "InvalidConnectionError",
]
