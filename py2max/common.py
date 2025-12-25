"""Backward compatibility shim for py2max.common module.

This module re-exports classes from py2max.core.common for backward compatibility.
New code should import directly from py2max.core.common.
"""

from py2max.core.common import Rect

__all__ = ["Rect"]
