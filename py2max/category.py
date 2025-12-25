"""Backward compatibility shim for py2max.category module.

This module re-exports from py2max.maxref.category for backward compatibility.
New code should import directly from py2max.maxref.category.
"""

from py2max.maxref.category import (
    CONTROL_OBJECTS,
    GENERATOR_OBJECTS,
    INPUT_OBJECTS,
    OUTPUT_OBJECTS,
    PROCESSOR_OBJECTS,
)

__all__ = [
    "INPUT_OBJECTS",
    "CONTROL_OBJECTS",
    "GENERATOR_OBJECTS",
    "PROCESSOR_OBJECTS",
    "OUTPUT_OBJECTS",
]
