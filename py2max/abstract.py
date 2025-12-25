"""Backward compatibility shim for py2max.abstract module.

This module re-exports classes from py2max.core.abstract for backward compatibility.
New code should import directly from py2max.core.abstract.
"""

from py2max.core.abstract import (
    AbstractBox,
    AbstractLayoutManager,
    AbstractPatcher,
    AbstractPatchline,
)

__all__ = [
    "AbstractBox",
    "AbstractLayoutManager",
    "AbstractPatcher",
    "AbstractPatchline",
]
