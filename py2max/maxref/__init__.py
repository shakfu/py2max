"""Max object reference system for py2max.

This subpackage provides access to Max object documentation and metadata:

- MaxRefCache: Cache for parsed .maxref.xml files
- MaxRefDB: SQLite database for Max object reference data
- MAXCLASS_DEFAULTS: Dictionary of default object properties
- Various helper functions for object introspection

Example:
    >>> from py2max.maxref import get_object_info, MAXCLASS_DEFAULTS
    >>> info = get_object_info('cycle~')
    >>> defaults = MAXCLASS_DEFAULTS.get('cycle~')
"""

# Re-export from parser module (main maxref functionality)
from .parser import (
    MAXCLASS_DEFAULTS,
    MaxClassDefaults,
    MaxRefCache,
    get_all_jit_objects,
    get_all_m4l_objects,
    get_all_max_objects,
    get_all_msp_objects,
    get_available_objects,
    get_inlet_count,
    get_inlet_types,
    get_legacy_defaults,
    get_object_help,
    get_object_info,
    get_objects_by_category,
    get_outlet_count,
    get_outlet_types,
    replace_tags,
    validate_connection,
)

# Re-export from db module
from .db import MaxRefDB

# Re-export category sets for layout managers
from .category import (
    CONTROL_OBJECTS,
    GENERATOR_OBJECTS,
    INPUT_OBJECTS,
    OUTPUT_OBJECTS,
    PROCESSOR_OBJECTS,
)

__all__ = [
    # Parser module exports
    "MaxRefCache",
    "MaxClassDefaults",
    "MAXCLASS_DEFAULTS",
    "get_object_info",
    "get_object_help",
    "get_available_objects",
    "get_objects_by_category",
    "get_all_max_objects",
    "get_all_jit_objects",
    "get_all_msp_objects",
    "get_all_m4l_objects",
    "get_legacy_defaults",
    "validate_connection",
    "get_inlet_count",
    "get_outlet_count",
    "get_inlet_types",
    "get_outlet_types",
    "replace_tags",
    # Database exports
    "MaxRefDB",
    # Category exports
    "INPUT_OBJECTS",
    "CONTROL_OBJECTS",
    "GENERATOR_OBJECTS",
    "PROCESSOR_OBJECTS",
    "OUTPUT_OBJECTS",
]
