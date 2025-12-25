"""Backward compatibility shim for py2max.maxclassdb module.

This module re-exports from py2max.maxref.legacy for backward compatibility.
New code should import directly from py2max.maxref.
"""

from py2max.maxref.legacy import MAXCLASS_DEFAULTS

__all__ = ["MAXCLASS_DEFAULTS"]
