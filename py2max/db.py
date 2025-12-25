"""Backward compatibility shim for py2max.db module.

This module re-exports classes from py2max.maxref.db for backward compatibility.
New code should import directly from py2max.maxref.
"""

from py2max.maxref.db import MaxRefDB

# Also re-export functions that were imported in old db.py for monkey-patching compatibility
from py2max.maxref import (
    get_all_jit_objects,
    get_all_m4l_objects,
    get_all_max_objects,
    get_all_msp_objects,
    get_available_objects,
    get_object_info,
)

__all__ = [
    "MaxRefDB",
    "get_object_info",
    "get_available_objects",
    "get_all_max_objects",
    "get_all_jit_objects",
    "get_all_msp_objects",
    "get_all_m4l_objects",
]
