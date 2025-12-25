"""py2max: A pure Python library for offline generation of Max/MSP patcher files.

py2max provides a Python object model that mirrors Max's patch organization with
round-trip conversion capabilities. It enables programmatic creation of Max/MSP
patches (.maxpat) files.

Main Classes:
    Patcher: Core class for creating and managing Max patches
    Box: Represents individual Max objects (oscillators, effects, etc.)
    Patchline: Represents connections between objects
    MaxRefDB: SQLite database for Max object reference data

Exceptions:
    Py2MaxError: Base exception for all py2max errors
    InvalidConnectionError: Exception raised for invalid connections
    InvalidObjectError: Exception raised for invalid object configuration
    InvalidPatchError: Exception raised for invalid patcher state
    PatcherIOError: Exception raised for file I/O errors
    MaxRefError: Exception raised for MaxRef XML parsing errors
    LayoutError: Exception raised for layout manager errors
    DatabaseError: Exception raised for database errors

Logging:
    get_logger: Get a configured logger for a module
    log_exception: Log an exception with full traceback
    log_operation: Context manager for logging operations

Example:
    >>> from py2max import Patcher
    >>> p = Patcher('my-patch.maxpat')
    >>> osc = p.add_textbox('cycle~ 440')
    >>> gain = p.add_textbox('gain~')
    >>> dac = p.add_textbox('ezdac~')
    >>> p.add_line(osc, gain)
    >>> p.add_line(gain, dac)
    >>> p.save()
"""

__version__ = "0.1.2"

from .core import Box, Patcher, Patchline
from .maxref import MaxRefDB
from .exceptions import (
    DatabaseError,
    InvalidConnectionError,
    InvalidObjectError,
    InvalidPatchError,
    LayoutError,
    MaxRefError,
    PatcherIOError,
    Py2MaxError,
)
from .log import get_logger, log_exception, log_operation
from .export import export_svg, export_svg_string

__all__ = [
    # Version
    "__version__",
    # Core classes
    "Patcher",
    "Box",
    "Patchline",
    "MaxRefDB",
    # SVG export
    "export_svg",
    "export_svg_string",
    # Exceptions
    "Py2MaxError",
    "InvalidConnectionError",
    "InvalidObjectError",
    "InvalidPatchError",
    "PatcherIOError",
    "MaxRefError",
    "LayoutError",
    "DatabaseError",
    # Logging utilities
    "get_logger",
    "log_exception",
    "log_operation",
]
