"""Backward compatibility shim for py2max.converters module.

This module re-exports from py2max.export.converters for backward compatibility.
New code should import directly from py2max.export.
"""

from .export.converters import maxpat_to_python, maxref_to_sqlite

__all__ = ["maxpat_to_python", "maxref_to_sqlite"]
