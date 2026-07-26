"""py2max: a pure python library to generate .maxpat patcher files.

GENERATED FILE -- DO NOT EDIT BY HAND.
py2max 0.3.6, generated from 455f575 (working tree modified)
Regenerate with: python scripts/build_single_file.py

This is the single-file edition: the package's core object model, layout
managers, linter and .amxd support amalgamated into one dependency-free module,
with an offline maxref table embedded for connection validation and object
defaults.

Included: Patcher/Box/Patchline, grid/flow/columnar/matrix layouts, lint(),
connection and attribute validation, .amxd read/write, SVG export.

Not included: Box.help() documentation prose (structured get_info() data is
present), graph layouts (layout="graph:*", needs third-party backends), the CLI,
and the SQLite maxref database. For those: pip install py2max

basic usage:

    >>> p = Patcher('out.maxpat')
    >>> osc1 = p.add_textbox('cycle~ 440')
    >>> gain = p.add_textbox('gain~')
    >>> dac = p.add_textbox('ezdac~')
    >>> p.add_line(osc1, gain)
    >>> p.add_line(gain, dac)
    >>> p.save()

"""

from __future__ import annotations


import base64
import contextlib
import datetime
import gzip
import html
import inspect
import json
import logging
import os
import re
import struct
import sys
import time
import traceback
import warnings

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    Union,
    cast,
)
from typing import (
    FrozenSet,
)
from typing import (
    Iterator,
)
from typing import Set
from typing import Sequence, TypedDict
from typing import NamedTuple
from typing import Mapping


# Type-checking-only imports, hoisted out of the modules'
# `if TYPE_CHECKING:` blocks. Never imported at runtime.
if TYPE_CHECKING:
    from typing_extensions import Unpack


# Module-qualified references (maxref.get_object_info, porttypes.BANG,
# category.INPUT_OBJECTS, layout_module.GridLayoutManager) resolve here:
# every symbol lives in this one module, so alias those names to it.
maxref = porttypes = category = layout_module = sys.modules[__name__]


__all__ = [
    "Patcher",
    "Box",
    "Patchline",
    "Rect",
    "LayoutManager",
    "GridLayoutManager",
    "HorizontalLayoutManager",
    "VerticalLayoutManager",
    "FlowLayoutManager",
    "MatrixLayoutManager",
    "ColumnarLayoutManager",
    "lint",
    "Finding",
]


# --------------------------------------------------------------------------
# py2max/exceptions.py
# --------------------------------------------------------------------------


class Py2MaxError(Exception):
    """Base exception for all py2max errors.

    All py2max-specific exceptions inherit from this class, allowing users
    to catch all library errors with a single exception handler.

    Attributes:
        message: Error message describing what went wrong.
        context: Optional dict with additional error context.
    """

    def __init__(self, message: str, context: Optional[dict[str, Any]] = None):
        """Initialize exception with message and optional context.

        Args:
            message: Error message describing the problem.
            context: Optional dict with additional error context (object IDs, etc.).
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}

    def __str__(self) -> str:
        """Return formatted error message with context.

        Returns:
            Formatted error message including context if available.
        """
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} ({context_str})"
        return self.message


# ----------------------------------------------------------------------------
# Validation Errors


class ValidationError(Py2MaxError):
    """Base class for validation errors.

    Raised when user input or object state fails validation checks.
    """


class InvalidConnectionError(ValidationError):
    """Raised when attempting to create an invalid patchline connection.

    This exception is raised when validation is enabled and an invalid
    connection is attempted, such as:
    - Connecting to a non-existent inlet or outlet
    - Connecting incompatible signal types
    - Creating duplicate connections

    Attributes:
        src: Source object identifier.
        dst: Destination object identifier.
        outlet: Source outlet index (if applicable).
        inlet: Destination inlet index (if applicable).
    """

    def __init__(
        self,
        message: str,
        src: Optional[str] = None,
        dst: Optional[str] = None,
        outlet: Optional[int] = None,
        inlet: Optional[int] = None,
    ):
        """Initialize connection error with connection details.

        Args:
            message: Error message.
            src: Source object ID.
            dst: Destination object ID.
            outlet: Source outlet index.
            inlet: Destination inlet index.
        """
        context: dict[str, Any] = {}
        if src:
            context["src"] = src
        if dst:
            context["dst"] = dst
        if outlet is not None:
            context["outlet"] = outlet
        if inlet is not None:
            context["inlet"] = inlet
        super().__init__(message, context)
        self.src = src
        self.dst = dst
        self.outlet = outlet
        self.inlet = inlet


class InvalidObjectError(ValidationError):
    """Raised when object configuration is invalid.

    Examples:
    - Invalid object type name
    - Missing required parameters
    - Invalid parameter values
    - Unknown maxclass

    Attributes:
        object_id: Object identifier.
        maxclass: Max object class name.
    """

    def __init__(
        self,
        message: str,
        object_id: Optional[str] = None,
        maxclass: Optional[str] = None,
    ):
        """Initialize object error with object details.

        Args:
            message: Error message.
            object_id: Object ID.
            maxclass: Max object class name.
        """
        context = {}
        if object_id:
            context["object_id"] = object_id
        if maxclass:
            context["maxclass"] = maxclass
        super().__init__(message, context)
        self.object_id = object_id
        self.maxclass = maxclass


class InvalidPatchError(ValidationError):
    """Raised when patcher state is invalid.

    Examples:
    - Circular subpatcher references
    - Missing required objects
    - Orphaned connections
    - Invalid patch structure

    Attributes:
        patch_path: Path to the patcher file.
    """

    def __init__(self, message: str, patch_path: Optional[str] = None):
        """Initialize patch error with patch details.

        Args:
            message: Error message.
            patch_path: Path to patcher file.
        """
        context = {}
        if patch_path:
            context["patch_path"] = patch_path
        super().__init__(message, context)
        self.patch_path = patch_path


# ----------------------------------------------------------------------------
# Configuration Errors


class ConfigurationError(Py2MaxError):
    """Base class for configuration errors.

    Raised when library configuration is invalid or incompatible.
    """


class LayoutError(ConfigurationError):
    """Raised when layout manager encounters an error.

    Examples:
    - Unknown layout type
    - Invalid layout parameters
    - Layout algorithm failure

    Attributes:
        layout_type: Layout manager type.
    """

    def __init__(self, message: str, layout_type: Optional[str] = None):
        """Initialize layout error with layout details.

        Args:
            message: Error message.
            layout_type: Layout manager type (e.g., 'grid', 'flow').
        """
        context = {}
        if layout_type:
            context["layout_type"] = layout_type
        super().__init__(message, context)
        self.layout_type = layout_type


class DatabaseError(ConfigurationError):
    """Raised when database operations fail.

    Examples:
    - Database connection failure
    - Schema mismatch
    - Data corruption
    - Query errors

    Attributes:
        db_path: Path to database file.
        operation: Operation that failed.
    """

    def __init__(
        self,
        message: str,
        db_path: Optional[str] = None,
        operation: Optional[str] = None,
    ):
        """Initialize database error with database details.

        Args:
            message: Error message.
            db_path: Path to database file.
            operation: Operation that failed (e.g., 'query', 'insert').
        """
        context = {}
        if db_path:
            context["db_path"] = str(db_path)
        if operation:
            context["operation"] = operation
        super().__init__(message, context)
        self.db_path = db_path
        self.operation = operation


# ----------------------------------------------------------------------------
# I/O Errors


class PatcherIOError(Py2MaxError, IOError):
    """Raised when patcher file I/O operations fail.

    Examples:
    - File not found
    - Permission denied
    - Invalid JSON format
    - Disk full

    Attributes:
        file_path: Path to the file.
        operation: I/O operation that failed.
    """

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
    ):
        """Initialize I/O error with file details.

        Args:
            message: Error message.
            file_path: Path to file.
            operation: Operation that failed (e.g., 'read', 'write').
        """
        context = {}
        if file_path:
            context["file_path"] = str(file_path)
        if operation:
            context["operation"] = operation
        Py2MaxError.__init__(self, message, context)
        self.file_path = file_path
        self.operation = operation


class MaxRefError(Py2MaxError, IOError):
    """Raised when MaxRef XML parsing or lookup fails.

    Examples:
    - MaxRef XML file not found
    - Invalid XML format
    - Object not found in MaxRef database
    - Max installation not found

    Attributes:
        object_name: Max object name being looked up.
        xml_path: Path to .maxref.xml file.
    """

    def __init__(
        self,
        message: str,
        object_name: Optional[str] = None,
        xml_path: Optional[str] = None,
    ):
        """Initialize MaxRef error with lookup details.

        Args:
            message: Error message.
            object_name: Name of Max object being looked up.
            xml_path: Path to .maxref.xml file.
        """
        context = {}
        if object_name:
            context["object_name"] = object_name
        if xml_path:
            context["xml_path"] = str(xml_path)
        Py2MaxError.__init__(self, message, context)
        self.object_name = object_name
        self.xml_path = xml_path


# ----------------------------------------------------------------------------
# Internal Errors


class InternalError(Py2MaxError):
    """Raised for unexpected internal errors.

    This exception indicates a bug in the library code and should be reported.
    Users should not typically need to catch this exception.

    Attributes:
        location: Location in code where error occurred.
    """

    def __init__(self, message: str, location: Optional[str] = None):
        """Initialize internal error with location.

        Args:
            message: Error message.
            location: Code location (e.g., 'Patcher.add_line').
        """
        context = {}
        if location:
            context["location"] = location
        super().__init__(f"Internal error: {message}", context)
        self.location = location


# ----------------------------------------------------------------------------
# Exports


# --------------------------------------------------------------------------
# py2max/log.py
# --------------------------------------------------------------------------


# ----------------------------------------------------------------------------
# env helpers


def getenv(key: str, default: bool = False) -> bool:
    """Convert '0','1' env values to bool {True, False}.

    Args:
        key: Environment variable name.
        default: Default value if env var not set.

    Returns:
        Boolean value parsed from environment variable.
    """
    return bool(int(os.getenv(key, str(int(default)))))


def getenv_str(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get string environment variable with optional default.

    Args:
        key: Environment variable name.
        default: Default value if env var not set.

    Returns:
        Environment variable value or default.
    """
    return os.getenv(key, default)


# ----------------------------------------------------------------------------
# constants

PY_VER_MINOR = sys.version_info.minor

#: Root logger name for the package. Every py2max logger is a child of this, so
#: an application can configure or silence all of py2max with one call:
#: ``logging.getLogger("py2max").setLevel(...)``.
LOGGER_NAME = "py2max"

# Env-var opt-ins. Note these are read once at import; nothing is *applied*
# unless one of them is explicitly set (see _configure_from_env below).
DEBUG = getenv("PY2MAX_DEBUG", default=False)
COLOR = getenv("PY2MAX_COLOR", default=True)
LOG_FILE = getenv_str("PY2MAX_LOG_FILE")
LOG_LEVEL = getenv_str("PY2MAX_LOG_LEVEL", "DEBUG" if DEBUG else "INFO")

# ----------------------------------------------------------------------------
# logging config


class CustomFormatter(logging.Formatter):
    """Custom logging formatter with color support and timestamp.

    Provides colored output for terminal display with consistent formatting
    across all log levels. Timestamps show elapsed time since logger initialization.
    """

    white = "\x1b[97;20m"
    grey = "\x1b[38;20m"
    green = "\x1b[32;20m"
    cyan = "\x1b[36;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    fmt = "%(delta)s - %(levelname)s - %(name)s.%(funcName)s - %(message)s"
    cfmt = (
        f"{white}%(delta)s{reset} - "
        f"{{}}%(levelname)s{{}} - "
        f"{white}%(name)s.%(funcName)s{reset} - "
        f"{grey}%(message)s{reset}"
    )

    FORMATS = {
        logging.DEBUG: cfmt.format(grey, reset),
        logging.INFO: cfmt.format(green, reset),
        logging.WARNING: cfmt.format(yellow, reset),
        logging.ERROR: cfmt.format(red, reset),
        logging.CRITICAL: cfmt.format(bold_red, reset),
    }

    def __init__(self, use_color: bool = COLOR) -> None:
        """Initialize formatter with color preference.

        Args:
            use_color: Whether to use ANSI color codes in output.
        """
        super().__init__()
        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors and timestamp.

        Args:
            record: Log record to format.

        Returns:
            Formatted log message string.
        """
        if not self.use_color:
            log_fmt: Optional[str] = self.fmt
        else:
            log_fmt = self.FORMATS.get(record.levelno)
        if PY_VER_MINOR > 10:
            duration = datetime.datetime.fromtimestamp(
                record.relativeCreated / 1000, datetime.timezone.utc
            )
        else:
            duration = datetime.datetime.utcfromtimestamp(record.relativeCreated / 1000)
        record.delta = duration.strftime("%H:%M:%S")
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


# A NullHandler on the package logger is the standard way for a library to
# participate in logging without imposing any: records propagate to whatever the
# application configured, and "No handlers could be found" warnings are avoided.
logging.getLogger(LOGGER_NAME).addHandler(logging.NullHandler())

# Tracks the handler installed by setup_logging so repeat calls reconfigure
# rather than stack up duplicate output.
_own_handlers: "list[logging.Handler]" = []


def setup_logging(
    level: Optional[str] = None,
    *,
    color: Optional[bool] = None,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """Opt in to py2max's colored console logging.

    Attaches py2max's own handler(s) to the ``py2max`` logger and sets its level.
    Only that logger is touched -- the root logger and any application
    configuration are left alone, so calling this cannot disturb the host
    program's logging.

    Idempotent: calling it again replaces the handlers it installed previously
    instead of adding a second copy of every message.

    Propagation is deliberately left as-is. Disabling it here would be a global
    side effect on a process-wide logger: anything that captures py2max records
    through an ancestor logger (an application's root handler, pytest's
    ``caplog``) would silently stop seeing them. An application that wants sole
    ownership of the output can set ``propagate`` itself.

    Args:
        level: Log level name (default: PY2MAX_LOG_LEVEL, else INFO).
        color: Use ANSI colors (default: PY2MAX_COLOR, else True).
        log_file: Also append records to this file, uncolored.

    Returns:
        The configured ``py2max`` logger.

    Example:
        >>> from py2max.log import setup_logging
        >>> setup_logging("DEBUG")
        >>> import py2max
        >>> py2max.Patcher("out.maxpat")   # now logs
    """
    logger = logging.getLogger(LOGGER_NAME)

    for handler in _own_handlers:
        logger.removeHandler(handler)
        handler.close()
    _own_handlers.clear()

    use_color = COLOR if color is None else color
    strm_handler = logging.StreamHandler()
    strm_handler.setFormatter(CustomFormatter(use_color=use_color))
    _own_handlers.append(strm_handler)

    path = log_file if log_file is not None else LOG_FILE
    if path:
        log_path = Path(path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, mode="a")
        file_handler.setFormatter(CustomFormatter(use_color=False))
        _own_handlers.append(file_handler)

    for handler in _own_handlers:
        logger.addHandler(handler)

    resolved = (level or LOG_LEVEL or "INFO").upper()
    logger.setLevel(getattr(logging, resolved, logging.INFO))
    return logger


def _configure_from_env() -> None:
    """Apply env-var logging config, if any was explicitly requested.

    Importing py2max stays silent unless the user asked for output, which keeps
    the library well-behaved while preserving the "export a variable and see
    what it is doing" workflow.
    """
    # DEBUG is the parsed PY2MAX_DEBUG flag, so an explicit '0' stays silent.
    if DEBUG or os.getenv("PY2MAX_LOG_LEVEL") or os.getenv("PY2MAX_LOG_FILE"):
        setup_logging()


_configure_from_env()


def config(name: str) -> logging.Logger:
    """Return a named logger under the ``py2max`` hierarchy.

    Retained for backwards compatibility; it no longer configures anything.
    Prefer :func:`get_logger`, and :func:`setup_logging` to enable output.

    Args:
        name: Logger name (typically __name__ from calling module).

    Returns:
        Logger instance for the specified name.
    """
    return logging.getLogger(name)


def get_logger(name: str) -> logging.Logger:
    """Get a logger for the specified module.

    Does not configure logging: a library must not decide where its host
    application's log records go. Use :func:`setup_logging` to opt in to
    py2max's own console output.

    Args:
        name: Logger name (typically __name__ from calling module).

    Returns:
        Logger instance.

    Example:
        >>> from py2max.log import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.debug("Processing object: cycle~")
    """
    return logging.getLogger(name)


# ----------------------------------------------------------------------------
# Error logging utilities


def log_exception(
    logger: logging.Logger, exc: Exception, context: Optional[str] = None
) -> None:
    """Log an exception with full traceback and optional context.

    Provides detailed error logging with stack traces for debugging.

    Args:
        logger: Logger instance to use.
        exc: Exception to log.
        context: Optional context description (e.g., "while parsing XML").

    Example:
        >>> try:
        ...     risky_operation()
        ... except Exception as e:
        ...     log_exception(logger, e, "while creating patcher")
    """
    if context:
        logger.error(f"{context}: {exc.__class__.__name__}: {exc}")
    else:
        logger.error(f"{exc.__class__.__name__}: {exc}")
    logger.debug(traceback.format_exc())


# Module-level set for tracking warned keys
_warned_keys: set[str] = set()


def log_warning_once(logger: logging.Logger, key: str, message: str) -> None:
    """Log a warning message only once per unique key.

    Useful for avoiding log spam from repeated warnings (e.g., deprecation warnings).

    Args:
        logger: Logger instance to use.
        key: Unique key for this warning.
        message: Warning message to log.

    Example:
        >>> log_warning_once(logger, "deprecated_api", "Method foo() is deprecated")
    """
    if key not in _warned_keys:
        logger.warning(message)
        _warned_keys.add(key)


@contextlib.contextmanager
def log_operation(
    logger: logging.Logger, operation: str, **kwargs: Any
) -> Iterator[None]:
    """Context manager for logging operations with timing and error handling.

    Logs operation start, completion time, and any errors that occur.

    Args:
        logger: Logger instance to use.
        operation: Operation description (e.g., "create patcher").
        **kwargs: Additional context to log with operation.

    Yields:
        None

    Example:
        >>> with log_operation(logger, "save patcher", path="out.maxpat"):
        ...     patcher.save()
    """
    import time

    # Build context string
    context_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    if context_str:
        logger.debug(f"Starting {operation} ({context_str})")
    else:
        logger.debug(f"Starting {operation}")

    start_time = time.time()
    try:
        yield
        elapsed = time.time() - start_time
        logger.debug(f"Completed {operation} in {elapsed:.3f}s")
    except Exception as exc:
        elapsed = time.time() - start_time
        logger.error(f"Failed {operation} after {elapsed:.3f}s: {exc}")
        raise


# ----------------------------------------------------------------------------
# Domain-specific logger helpers


class LoggerMixin:
    """Mixin class to add logging capabilities to any class.

    Provides a `logger` property that returns a logger named after the class.

    Example:
        >>> class MyClass(LoggerMixin):
        ...     def process(self):
        ...         self.logger.info("Processing")
    """

    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class.

        Returns:
            Logger instance named after the class.
        """
        return get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")


# ----------------------------------------------------------------------------
# Convenience exports


# --------------------------------------------------------------------------
# py2max/utils.py
# --------------------------------------------------------------------------


def kwds_filter(kwds: Dict[str, Any], **elems: Any) -> Dict[str, Any]:
    """Return ``kwds`` merged with the ``elems`` whose value is not ``None``.

    Lets a method keep an optional parameter in its signature but omit it from
    the forwarded ``**kwds`` when the caller left it at its ``None`` default,
    so unset options never reach the serialized patch::

        def add(self, text, varname=None, **kwds):
            return Box(text, **kwds_filter(kwds, varname=varname))

    Only ``None`` is treated as "unset"; legitimate falsy values such as ``0``
    or ``""`` are kept. The input ``kwds`` is not mutated.
    """
    return {**kwds, **{k: v for k, v in elems.items() if v is not None}}


def object_name(box: Any) -> str:
    """Resolve the effective Max object name for a box.

    Native-maxclass objects (e.g. ``live.dial``, ``toggle``) carry the name in
    ``maxclass``. ``newobj`` boxes carry it as the first token of their text.

    Reading the ``text`` property (rather than ``_kwds`` directly) means this
    works for both programmatically-created boxes and boxes loaded from a file,
    where the text lives in ``__dict__`` instead of ``_kwds``.
    """
    maxclass = getattr(box, "maxclass", "newobj")
    if maxclass and maxclass != "newobj":
        return maxclass
    text = getattr(box, "text", "") or ""
    tokens = text.split()
    return tokens[0] if tokens else (maxclass or "")


NOTE_TO_SEMITONE = {
    "C": 0,
    "C#": 1,
    "Db": 1,
    "D": 2,
    "D#": 3,
    "Eb": 3,
    "E": 4,
    "Fb": 4,
    "E#": 5,
    "F": 5,
    "F#": 6,
    "Gb": 6,
    "G": 7,
    "G#": 8,
    "Ab": 8,
    "A": 9,
    "A#": 10,
    "Bb": 10,
    "B": 11,
    "Cb": 11,
    "B#": 0,
}


def pitch2freq(pitch: str, A4: int = 440) -> float:
    """Convert a pitch name to a frequency in Hz.

    Converts standard pitch notation (e.g., "C4", "A#3") to frequency
    values using equal temperament tuning.

    Args:
        pitch: Pitch name in format like "C4", "A#3", "Bb2".
        A4: Reference frequency for A4 (default: 440 Hz).

    Returns:
        Frequency in Hz as a float.

    Example:
        >>> pitch2freq("C3")
        130.8127826502993
        >>> pitch2freq("A4")
        440.0

    Note:
        Based on: https://gist.github.com/CGrassin/26a1fdf4fc5de788da9b376ff717516e
    """

    token = pitch.strip()
    if len(token) < 2:
        raise ValueError(f"Invalid pitch name: '{pitch}'")

    note = token[0].upper()
    idx = 1

    if idx < len(token) and token[idx] in ("#", "b", "♯", "♭"):
        accidental = token[idx]
        if accidental == "♯":
            accidental = "#"
        elif accidental == "♭":
            accidental = "b"
        note += accidental
        idx += 1

    octave_part = token[idx:]
    try:
        octave = int(octave_part)
    except ValueError as exc:
        raise ValueError(f"Invalid octave in pitch name: '{pitch}'") from exc

    if note not in NOTE_TO_SEMITONE:
        raise ValueError(f"Unsupported note name: '{pitch}'")

    semitone = NOTE_TO_SEMITONE[note]
    midi_number = semitone + (octave + 1) * 12
    distance_from_A4 = midi_number - 69
    return float(A4) * 2 ** (distance_from_A4 / 12)


# --------------------------------------------------------------------------
# py2max/core/common.py
# --------------------------------------------------------------------------


class Rect(NamedTuple):
    """Rectangle data structure for object positioning.

    Represents a rectangular area in Max patch coordinates using four coordinates:
    x (horizontal position), y (vertical position), w (width), and h (height).
    """

    x: float
    y: float
    w: float
    h: float


# --------------------------------------------------------------------------
# py2max/core/colors.py
# --------------------------------------------------------------------------


# A color may be given as a name, a hex string, or an [r, g, b(, a)] sequence.
ColorLike = Union[str, Sequence[float]]

# Named colors as Max RGBA floats (0..1).
MAX_COLORS: Dict[str, List[float]] = {
    "black": [0.0, 0.0, 0.0, 1.0],
    "white": [1.0, 1.0, 1.0, 1.0],
    "red": [0.85, 0.0, 0.0, 1.0],
    "green": [0.0, 0.6, 0.0, 1.0],
    "blue": [0.0, 0.0, 1.0, 1.0],
    "yellow": [1.0, 0.9, 0.0, 1.0],
    "cyan": [0.0, 0.8, 0.9, 1.0],
    "magenta": [0.9, 0.0, 0.9, 1.0],
    "orange": [1.0, 0.6, 0.0, 1.0],
    "purple": [0.6, 0.2, 0.8, 1.0],
    "gray": [0.5, 0.5, 0.5, 1.0],
    "grey": [0.5, 0.5, 0.5, 1.0],
    "lightgray": [0.83, 0.83, 0.83, 1.0],
    "lightgrey": [0.83, 0.83, 0.83, 1.0],
    "darkgray": [0.27, 0.27, 0.27, 1.0],
    "darkgrey": [0.27, 0.27, 0.27, 1.0],
    "clear": [0.0, 0.0, 0.0, 0.0],
}


def _hex_to_rgba(hex_color: str) -> List[float]:
    """Convert ``#rrggbb`` or ``#rrggbbaa`` to a Max RGBA float list."""
    s = hex_color.lstrip("#")
    if len(s) == 6:
        s += "ff"
    if len(s) != 8:
        raise ValueError(f"invalid hex color {hex_color!r}")
    try:
        return [int(s[i : i + 2], 16) / 255.0 for i in (0, 2, 4, 6)]
    except ValueError as exc:
        raise ValueError(f"invalid hex color {hex_color!r}") from exc


def resolve_color(color: ColorLike) -> List[float]:
    """Resolve a color to a Max ``[r, g, b, a]`` float list.

    Accepts a named color (see ``MAX_COLORS``), a hex string (``"#rrggbb"`` or
    ``"#rrggbbaa"``), or an ``[r, g, b]`` / ``[r, g, b, a]`` sequence of floats.
    """
    if isinstance(color, str):
        key = color.strip().lower()
        if key in MAX_COLORS:
            return list(MAX_COLORS[key])
        if key.startswith("#"):
            return _hex_to_rgba(key)
        raise ValueError(f"unknown color name {color!r}")
    seq = [float(c) for c in color]
    if len(seq) == 3:
        seq.append(1.0)
    if len(seq) != 4:
        raise ValueError(f"color sequence must have 3 or 4 components, got {color!r}")
    return seq


# Box-color themes applied to every box by Patcher.apply_theme.
THEMES: Dict[str, Dict[str, ColorLike]] = {
    "light": {"bg": "lightgray", "text": "black", "border": "gray"},
    "dark": {
        "bg": [0.15, 0.15, 0.15, 1.0],
        "text": "white",
        "border": [0.4, 0.4, 0.4, 1.0],
    },
    "blue": {
        "bg": [0.85, 0.9, 1.0, 1.0],
        "text": [0.05, 0.1, 0.3, 1.0],
        "border": "blue",
    },
    "high-contrast": {"bg": "black", "text": "yellow", "border": "yellow"},
}


# --------------------------------------------------------------------------
# py2max/core/props.py
# --------------------------------------------------------------------------


#: A Max atom: the loosest useful value type.
Atom = Union[str, int, float]

#: A Max time value: milliseconds, or notation such as "4n".
TimeValue = Union[int, float, str]


class BoxProps(TypedDict, total=False):
    """Properties accepted by ``Box.__init__`` beyond its structural args."""

    accentcolor: Sequence[float]
    accum: int
    accum_desat: float
    active: int
    active1: Sequence[float]
    activebgcolor: Sequence[float]
    activebgoncolor: Sequence[float]
    activecolor: Sequence[float]
    activedialcolor: Sequence[float]
    activefgdialcolor: Sequence[float]
    activeneedlecolor: Sequence[float]
    activesafe: int
    activeslidercolor: Sequence[float]
    activetextcolor: Sequence[float]
    activetextoncolor: Sequence[float]
    activetricolor: Sequence[float]
    activetricolor2: Sequence[float]
    addpoints: Sequence[Any]
    align: Atom
    allowdisabled: int
    allowdrag: int
    allowreorder: int
    allwindowsactive: int
    alpha: float
    amountcolor: Sequence[float]
    amxdtype: int
    annotation: str
    annotation_name: str
    appearance: int
    appicon_mac: str
    appicon_win: str
    applycolors: int
    applyfont: int
    arrow: int
    arrow_orientation: int
    arrowcolor: Sequence[float]
    arrows: int
    assistance: int
    attack: Union[float, int]
    attr: str
    attr_bpm: float
    attr_comment: str
    attr_display: int
    attrfilter: Sequence[str]
    audioframerate: float
    audioframesize: int
    auto_handle: int
    autoboxedit_patching: int
    autocompletionspace: int
    autoconnectusesmouseposition: int
    autoexport: int
    autofit: int
    autohint: int
    autolockunselected: int
    automatic: int
    automation: str
    automationon: str
    automouse: int
    autoout: int
    autopopulate: int
    autosave: int
    autoscroll: int
    autosize: int
    autosustain: int
    autowatch: int
    autowrite: int
    background: int
    bangmode: int
    basictuning: int
    bblend: int
    beats: int
    bgcolor: Sequence[float]
    bgcolor2: Sequence[float]
    bgfillcolor: Sequence[float]
    bgmode: int
    bgoncolor: Sequence[float]
    bgrulercolor: Sequence[float]
    bgstepcolor: Sequence[float]
    bgstepcolor2: Sequence[float]
    bgtransparent: int
    bgunitcolor: Sequence[float]
    bkgnddrag: int
    bkgndpict: str
    bkgndsize: int
    blackkeycolor: Sequence[float]
    blanksym: str
    blinkcolor: Sequence[float]
    blinktime: int
    border: int
    bordercolor: Sequence[float]
    bordercolor2: Sequence[float]
    bottommargin: int
    bottomvalue: int
    boundmode: int
    browsertext: str
    bubble: int
    bubble_bgcolor: Sequence[float]
    bubble_outlinecolor: Sequence[float]
    bubblepoint: float
    bubbleside: int
    bubblesize: int
    bubbletextmargin: int
    bubbleusescolors: int
    buffername: str
    bufsize: int
    bundleidentifier: str
    button: int
    bypass: int
    calccount: int
    candicane2: Sequence[float]
    candicane3: Sequence[float]
    candicane4: Sequence[float]
    candicane5: Sequence[float]
    candicane6: Sequence[float]
    candicane7: Sequence[float]
    candicane8: Sequence[float]
    candycane: int
    candycane2: Sequence[float]
    candycane3: Sequence[float]
    candycane4: Sequence[float]
    candycane5: Sequence[float]
    candycane6: Sequence[float]
    candycane7: Sequence[float]
    candycane8: Sequence[float]
    candymode: int
    cantchange: int
    cantclosetoplevelpatchers: int
    cefsupport: int
    cellheight: int
    cellpict: str
    cellwidth: int
    channelcount: int
    channels: int
    chanoffset: int
    chans: int
    checkedcolor: Sequence[float]
    checkforupdates: int
    classic_curve: int
    clearcolor: Sequence[float]
    clefs: int
    clickadd: int
    clickedimage: int
    clickinactive: int
    clickincrement: int
    clickmode: int
    clickmove: int
    clickmoveinactive: int
    clicksustain: int
    clickthrough: int
    client_rect: Sequence[float]
    clip: int
    clip_size: int
    clipdraw: int
    clipheight: float
    code: str
    coldcolor: Sequence[float]
    colhead: int
    collection: str
    color: Sequence[float]
    colorlabels: int
    colormode: str
    colorselectedtext: int
    colortheme: Atom
    colortitlebar: int
    cols: int
    columns: int
    colwidth: int
    comment: Any
    compatibility: int
    connectacrossdividers: int
    constrainduplicates: int
    constrainpointchanges: int
    contdata: int
    contrast: float
    contrastactivetab: int
    convertobj: int
    cool: int
    coolcolor: Sequence[float]
    copysupport: int
    crashrecovery: str
    curvecolor: Sequence[float]
    data: Any
    database: int
    datadirty: int
    dbdisplay: int
    dbperled: int
    debugqueuesize: int
    decodemode: int
    default_template: str
    defaultcachesize: float
    defaultglcontext: str
    defaultm4ldevicesfolder: str
    defaultpatchersize: int
    defaultprojectsfolder: str
    defer: int
    degrees: int
    delay: Union[float, int]
    depth: Union[float, int]
    description: str
    devpath: str
    devpathtype: int
    dialcolor: Sequence[float]
    dialmode: int
    dialtracking: int
    digest: str
    dimmedconnectionalpha: float
    direction: int
    direction_height: float
    directioncolor: Sequence[float]
    dirty: int
    disabledalpha: float
    disabledcolor: Sequence[float]
    disablefind: int
    display_flat: int
    display_range: Sequence[float]
    displayamount: int
    displaychan: int
    displayknob: int
    displaymode: int
    displaysinglechannel: int
    dividercolor: Sequence[float]
    dividers: Atom
    dividersize: int
    domain: float
    domainlabel: str
    dontreplace: int
    downarrow: int
    drag_window: int
    dragtrack: int
    drawline: int
    drawoffcolor: int
    drawpeakhold: int
    drawpeaks: int
    drawstyle: int
    drawto: str
    dsp_cpulimit: str
    dsp_driver: int
    dsp_inputdevice: str
    dsp_iovectorsize: str
    dsp_option1: str
    dsp_option2: str
    dsp_outputdevice: str
    dsp_overdrive: str
    dsp_samplerate: str
    dsp_siai: str
    dsp_signalvectorsize: str
    dstrect: Sequence[int]
    duration_active: int
    dynamic: int
    editing_bgcolor: Sequence[float]
    editlocked: int
    editlooponly: int
    editor_rect: Sequence[float]
    elementcolor: Sequence[float]
    embed: int
    emptycolor: Sequence[float]
    enable: int
    enabled: int
    enablednotes: Sequence[Atom]
    enabledrag: int
    enableglobalcontext: int
    enablehscroll: int
    enablesprites: int
    enablevscroll: int
    erase_color: Sequence[float]
    exclusive: int
    expansion: str
    export_dpi: int
    exportfolder: str
    exportname: str
    exportnotifier: str
    exportscript: str
    exportscriptargs: str
    externaleditor: str
    extra1_active: int
    extra1_max: int
    extra1_min: int
    extra1_signed: int
    extra2_active: int
    extra2_max: int
    extra2_min: int
    extra2_signed: int
    extra_thickness: float
    factorycontent: int
    fblend: int
    fgcolor: Sequence[float]
    fgdialcolor: Sequence[float]
    file: str
    filekind: str
    filename: str
    fillhorizontalspace: int
    filternodeschanges: int
    filtertext: str
    flagmode: int
    floateditorwindow: int
    floatoutput: int
    focusbordercolor: Sequence[float]
    folderslash: int
    followglobaltempo: int
    followlivetheme: Atom
    fontface: int
    fontlink: int
    fontname: str
    fontsize: float
    forceaspect: int
    forcejwebrendermode: int
    formant: float
    formantcorrection: int
    format: int
    fps: float
    frames: int
    freezecolor: Sequence[float]
    ft1: float
    fullspect: int
    gaincaption: int
    gaindragmode: int
    gainradius: float
    gainstyle: int
    genericeditor: int
    gensupport: int
    gfxengine: str
    ghostbar: int
    gizmos: int
    globalpatchername: str
    globalzoomfactor: int
    gradient: float
    graphcolor: Sequence[float]
    graphmode: str
    grid: Union[float, int]
    gridcolor: Sequence[float]
    gridlinecolor: Sequence[float]
    gridorigincolor: Sequence[float]
    gridstep_x: float
    gridstep_y: float
    hbgcolor: Sequence[float]
    hcellcolor: Sequence[float]
    hcurvecolor: Sequence[float]
    headercolor: Sequence[float]
    headerheight: int
    headerlabel: str
    hgraphcolor: Sequence[float]
    hidden: int
    hideloop: int
    hiderwff: int
    hilite: int
    hint: str
    hires: int
    hkeycolor: Sequence[float]
    hltcolor: Sequence[float]
    hlttextcolor: Sequence[float]
    horizontal_direction: int
    horizontalmargin: int
    horizontalspacing: int
    horizontaltracking: float
    hotcolor: Sequence[float]
    hscroll: int
    hsync: int
    htabcolor: Sequence[float]
    htextcolor: Sequence[float]
    htricolor: Sequence[float]
    idle: int
    idlemouse: int
    ignoreclick: int
    ignoreconnected: int
    ignoreemptyinterp: int
    illustrationspeed: int
    imagemask: int
    inactive: int
    inactivealpha: float
    inactivecoldcolor: Sequence[float]
    inactiveimage: int
    inactivelcdcolor: Sequence[float]
    inactivetextoffcolor: Sequence[float]
    inactivetextoncolor: Sequence[float]
    inactivewarmcolor: Sequence[float]
    inc: float
    includepackages: int
    incolormap: Atom
    increment: float
    index: int
    initial: Sequence[Atom]
    initialgain: float
    inlabels: Atom
    inputmode: int
    inputrangemode: int
    inputs: int
    inspectreadonly: int
    int: int
    interp: Union[float, int]
    interpinlet: int
    interval: Union[float, int]
    invert: int
    invisiblebkgnd: int
    items: Sequence[Any]
    jsarguments: Sequence[Atom]
    jump: int
    just: int
    justification: int
    jwebremotedebuggingport: int
    keymode: int
    keynavigate: int
    knobcolor: Sequence[float]
    knobpict: str
    knobshape: int
    knobsize: float
    labelclick: int
    labelheight: float
    labels: int
    labeltextcolor: Sequence[float]
    labelwidth: float
    lastchannelcount: int
    latency: Union[float, int]
    layoutbubbles: int
    lcdbgcolor: Sequence[float]
    lcdcolor: Sequence[float]
    leftarrow: int
    leftmargin: int
    leftvalue: int
    legacy: int
    legacyoutputorder: int
    legacytextcolor: int
    legacytransport: int
    legend: Union[int, str]
    linecolor: Sequence[float]
    linecount: int
    linenumbers: int
    linenumberwidth: int
    lines: int
    linethickness: float
    link: int
    linmarkers: Sequence[float]
    listmode: int
    listresize: int
    livemode: int
    loadbangonpaste: int
    local: int
    lock: int
    locked_bgcolor: Sequence[float]
    lockeddragscroll: int
    lockedsize: int
    logamp: int
    logfreq: int
    loglevel: int
    logmarkers: Sequence[float]
    logtosystemconsole: int
    loop: int
    loopbordercolor: Sequence[float]
    loopreport: int
    loopruler: int
    lsbfirst: int
    margin: int
    margins: Sequence[float]
    marker_horizontal: int
    marker_vertical: int
    markercolor: Sequence[float]
    markers: Sequence[int]
    markersused: int
    matrixmode: int
    maxdynamicnodes: int
    maxgain: float
    maximum: Atom
    maxurlproxyname: str
    maxwindow_dequeuesize: int
    maxwindow_fontname: str
    maxwindow_fontsize: int
    maxwindow_queuesize: int
    mcisolate: int
    mctrigchan: int
    menu_display: int
    menumode: int
    metering: int
    min: float
    minimum: Atom
    mode: Union[int, str]
    modulationcolor: Sequence[float]
    monitormode: int
    monochrome: int
    monotone: int
    mousefilter: int
    mousemode: int
    mousereport: int
    mouseup: int
    movehorizontal: int
    movevertical: int
    mult: float
    multiline: int
    multiplier: int
    multiselect: int
    multislider: int
    n4m_debug_log_enabled: int
    n4m_debug_log_folder: str
    n4m_debug_log_name: str
    n4m_external_node_binary: str
    n4m_process_manager_path: str
    name: str
    needlecolor: Sequence[float]
    needlemode: int
    neverdirty: int
    nfilters: int
    nhotleds: int
    nodecolor: Sequence[float]
    nodenumber: int
    nodesnames: Sequence[str]
    nofsaa: int
    noloadbangdefeating: int
    normalized: int
    norulerclick: int
    nosymquotes: int
    notebase: int
    notelist: Sequence[str]
    notename: int
    nseq: int
    nsize: Sequence[float]
    ntepidleds: int
    numdecimalplaces: int
    numdisplay: int
    numins: int
    numleds: int
    numouts: int
    numplots: int
    numpoints: int
    nwarmleds: int
    offcolor: Sequence[float]
    offset: Union[Sequence[float], float, int]
    oncolor: Sequence[float]
    onscreen: int
    orientation: int
    originallength: TimeValue
    originaltempo: float
    oscdefer: int
    oscparamenableddefault: int
    oscprefix: str
    oscprefixmode: int
    oscqueryenable: int
    oscqueryport: int
    oscreceivemode: int
    oscreceivequantize: TimeValue
    oscreceivethreshold: TimeValue
    oscreceiveudpport: int
    oscsendmode: int
    oscsendthreshold: TimeValue
    oscsendudpaddr: str
    oscsendudpport: int
    oscuseparamprefix: int
    oscvaluemode: int
    outcolormap: Atom
    outlabels: Atom
    outlettype: Any
    outlinecolor: Sequence[float]
    outmode: int
    output_texture: int
    outputalpha: int
    outputformat: str
    outputmode: int
    outputonclick: int
    outputs: int
    overdrive: int
    overgaincolor: Sequence[float]
    overloadcolor: Sequence[float]
    panelcolor: Sequence[float]
    param_connect: str
    parameter_enable: int
    parameter_mappable: int
    paramonly: int
    patcher: Any
    patcher_boxsnapmargin: Atom
    patcherinspector: int
    patchername: str
    patchingmargin: int
    patchingmarginpercent: float
    patchingmechanics: int
    patchline_curved: int
    patchlinecolor: Sequence[float]
    pattrmode: int
    pconstrain: int
    peakcolor: Sequence[float]
    permissive: int
    phasespect: int
    pic: str
    pickray: int
    pictures: Sequence[str]
    pitch_active: int
    pitchcorrection: int
    pitchdetection: int
    pitchshift: float
    pitchshiftcent: int
    planemap: Sequence[int]
    pointalign: float
    pointcolor: Sequence[float]
    pointsize: float
    polezerocolor: Sequence[float]
    poll: int
    popupbrowserbar: int
    precision: int
    prefer: str
    preffilename: str
    prefix: str
    prefix_mode: int
    presentation: int
    presentation_rect: Sequence[float]
    preservegain: int
    preset_data: Sequence[Any]
    preview: int
    prioritizeexterns: int
    prioritizepatchlines: int
    prototypename: str
    quality: str
    quiet: int
    range: Sequence[Atom]
    rangelabel: str
    ratio: int
    readonly: int
    realtime_params: int
    reflection: int
    reflectioncolor: Sequence[float]
    refreshrate: float
    relative: int
    release: Union[float, int]
    remapsvgcolors: int
    rendermode: int
    reportprogress: int
    restorewindows: int
    retune: int
    rightarrow: int
    rightmargin: int
    rightvalue: int
    rnbo_classname: str
    rnbo_extra_attributes: Dict[str, Any]
    rnbo_log_file: str
    rnbo_log_folder: str
    rnbo_log_level: int
    rnbo_server_autostart: int
    rounded: float
    rowhead: int
    rowheight: int
    rows: int
    running: int
    saturation: float
    saved_attribute_attributes: Dict[str, Any]
    saved_object_attributes: Dict[str, Any]
    savedependencies: int
    savemode: int
    savesingletons: int
    scale: Union[float, int]
    scaleknob: int
    sccolor: Sequence[float]
    scroll: int
    searchformissingfiles: int
    segmented: int
    segpatchcords: int
    selectalpha: float
    selectedclick: int
    selectioncolor: Sequence[float]
    selector: str
    selecttextonclick_patching: int
    selmode: int
    selsync: int
    separator: str
    setarrowkeysscrollpatcher: int
    seteventinterval: int
    setminmax: Sequence[float]
    setmixergbitmode: int
    setmixerlatency: float
    setmixerparallel: int
    setmixerramptime: float
    setmode: int
    setnativefontpanel: int
    setpollthrottle: int
    setqueuethrottle: int
    setresizes: int
    setscrollbarmode: int
    setslop: float
    setstyle: int
    setsysqelemthrottle: int
    settype: int
    setunit: int
    sgcolor: Sequence[float]
    shadow: int
    shadowactive: int
    shadowalpha: float
    shadowblend: float
    shadowline: int
    shadoworientation: int
    shadowperbar: int
    shadowproportion: float
    shadowreflectionpoint: float
    shadowsigned: int
    shape: int
    showcaption: int
    showcluebar: int
    showdotfiles: int
    showeditor: int
    showgain: int
    showgetonly: int
    showheader: int
    showlabels: int
    showname: int
    shownumber: int
    signalmode: str
    signalusecols: int
    signed: int
    sigoutmode: int
    size: float
    slidercolor: Sequence[float]
    slurtime: float
    smoothing: float
    snap: int
    snap2grid: int
    snapto: int
    snaptopixelbydefault: int
    sono: int
    sonohicolor: Sequence[float]
    sonolocolor: Sequence[float]
    sonomedcolor: Sequence[float]
    sonomedhicolor: Sequence[float]
    sonomedlocolor: Sequence[float]
    sonomonobgcolor: Sequence[float]
    sonomonofgcolor: Sequence[float]
    sortmode: int
    spacing: Union[float, int]
    spacing_x: float
    spacing_y: float
    srcrect: Sequence[int]
    staffs: int
    statusvisible: int
    stay: int
    stcolor: Sequence[float]
    stepcolor: Sequence[float]
    stepcolor2: Sequence[float]
    storage_rect: Sequence[float]
    stored1: Sequence[float]
    storeinpreset: int
    stripe2: Sequence[float]
    stripecolor: Sequence[float]
    style: str
    suppressinlet: int
    svg: str
    switchcolor: Sequence[float]
    sync: int
    syntax: str
    syntax_attrargcolor: Sequence[float]
    syntax_attributecolor: Sequence[float]
    syntax_objargcolor: Sequence[float]
    syntax_objectcolor: Sequence[float]
    syntaxcoloring: int
    syntaxcolorset: Atom
    systimerearlywake: int
    tabcolor: Sequence[float]
    table_data: Sequence[float]
    tabmode: int
    tabs: Sequence[str]
    tags: str
    template: str
    tepidcolor: Sequence[float]
    text: str
    text_width: float
    textcolor: Sequence[float]
    textcolor_inverse: Sequence[float]
    textjustification: int
    textoffcolor: Sequence[float]
    texton: str
    textoncolor: Sequence[float]
    textovercolor: Sequence[float]
    thickness: Union[float, int]
    thinmode: str
    thinthresh: int
    thinto: float
    threshold: float
    threshold_db: float
    threshold_linear: float
    ticks: int
    timestretch: int
    toggle: int
    tool: int
    toolbarcluemode: int
    toolbarquickrecord_format: int
    toolbarquickrecord_redbutton: int
    topmargin: int
    topvalue: int
    tosymbol: int
    trackcircular: int
    trackhorizontal: int
    tracking: int
    trackvertical: int
    transition: int
    translation: str
    triangle: int
    tribordercolor: Sequence[float]
    tricolor: Sequence[float]
    tricolor2: Sequence[float]
    trigger: int
    triglevel: float
    trioncolor: Sequence[float]
    triscale: float
    truncate: int
    types: Union[Atom, str]
    uncheckedcolor: Sequence[float]
    underline: int
    unitruler: int
    uparrow: int
    url: str
    use_16bit: int
    usebgoncolor: int
    usedstrect: int
    useexternaleditor: int
    useoffcolor: int
    usepicture: int
    usesearchpath: int
    useselectioncolor: int
    usespacesforjed: int
    usesrcrect: int
    usestepcolor2: int
    usesvgviewbox: int
    usetextovercolor: int
    usewebeditor: int
    valign: int
    valuemode: int
    valuepopup: int
    valuepopuplabel: int
    varname: str
    velocity_active: int
    vertical_direction: int
    verticalmargin: int
    verticalspacing: int
    verticaltracking: float
    videoengine: str
    viewvisibility: Any
    vlabels: int
    voffset: float
    vscroll: int
    vstscanmode: int
    vsync: int
    vticks: int
    vtracking: int
    vzoom: float
    warmcolor: Sequence[float]
    waveformcolor: Sequence[float]
    waveformdisplay: int
    wheelzoomdirection: int
    wheelzoomfactor: float
    whitekeycolor: Sequence[float]
    wiggletime: int
    wordwrap: int
    xoffset: float
    xplace: Sequence[float]
    yoffset: float
    yplace: Sequence[float]
    zoom_orientation: int
    zoomstyle: int
    zoomthresh: float


class TextboxProps(TypedDict, total=False):
    """As :class:`BoxProps`, minus the names the factory takes as parameters."""

    accentcolor: Sequence[float]
    accum: int
    accum_desat: float
    active: int
    active1: Sequence[float]
    activebgcolor: Sequence[float]
    activebgoncolor: Sequence[float]
    activecolor: Sequence[float]
    activedialcolor: Sequence[float]
    activefgdialcolor: Sequence[float]
    activeneedlecolor: Sequence[float]
    activesafe: int
    activeslidercolor: Sequence[float]
    activetextcolor: Sequence[float]
    activetextoncolor: Sequence[float]
    activetricolor: Sequence[float]
    activetricolor2: Sequence[float]
    addpoints: Sequence[Any]
    align: Atom
    allowdisabled: int
    allowdrag: int
    allowreorder: int
    allwindowsactive: int
    alpha: float
    amountcolor: Sequence[float]
    amxdtype: int
    annotation: str
    annotation_name: str
    appearance: int
    appicon_mac: str
    appicon_win: str
    applycolors: int
    applyfont: int
    arrow: int
    arrow_orientation: int
    arrowcolor: Sequence[float]
    arrows: int
    assistance: int
    attack: Union[float, int]
    attr: str
    attr_bpm: float
    attr_comment: str
    attr_display: int
    attrfilter: Sequence[str]
    audioframerate: float
    audioframesize: int
    auto_handle: int
    autoboxedit_patching: int
    autocompletionspace: int
    autoconnectusesmouseposition: int
    autoexport: int
    autofit: int
    autohint: int
    autolockunselected: int
    automatic: int
    automation: str
    automationon: str
    automouse: int
    autoout: int
    autopopulate: int
    autosave: int
    autoscroll: int
    autosize: int
    autosustain: int
    autowatch: int
    autowrite: int
    background: int
    bangmode: int
    basictuning: int
    bblend: int
    beats: int
    bgcolor: Sequence[float]
    bgcolor2: Sequence[float]
    bgfillcolor: Sequence[float]
    bgmode: int
    bgoncolor: Sequence[float]
    bgrulercolor: Sequence[float]
    bgstepcolor: Sequence[float]
    bgstepcolor2: Sequence[float]
    bgtransparent: int
    bgunitcolor: Sequence[float]
    bkgnddrag: int
    bkgndpict: str
    bkgndsize: int
    blackkeycolor: Sequence[float]
    blanksym: str
    blinkcolor: Sequence[float]
    blinktime: int
    border: int
    bordercolor: Sequence[float]
    bordercolor2: Sequence[float]
    bottommargin: int
    bottomvalue: int
    boundmode: int
    browsertext: str
    bubble: int
    bubble_bgcolor: Sequence[float]
    bubble_outlinecolor: Sequence[float]
    bubblepoint: float
    bubbleside: int
    bubblesize: int
    bubbletextmargin: int
    bubbleusescolors: int
    buffername: str
    bufsize: int
    bundleidentifier: str
    button: int
    bypass: int
    calccount: int
    candicane2: Sequence[float]
    candicane3: Sequence[float]
    candicane4: Sequence[float]
    candicane5: Sequence[float]
    candicane6: Sequence[float]
    candicane7: Sequence[float]
    candicane8: Sequence[float]
    candycane: int
    candycane2: Sequence[float]
    candycane3: Sequence[float]
    candycane4: Sequence[float]
    candycane5: Sequence[float]
    candycane6: Sequence[float]
    candycane7: Sequence[float]
    candycane8: Sequence[float]
    candymode: int
    cantchange: int
    cantclosetoplevelpatchers: int
    cefsupport: int
    cellheight: int
    cellpict: str
    cellwidth: int
    channelcount: int
    channels: int
    chanoffset: int
    chans: int
    checkedcolor: Sequence[float]
    checkforupdates: int
    classic_curve: int
    clearcolor: Sequence[float]
    clefs: int
    clickadd: int
    clickedimage: int
    clickinactive: int
    clickincrement: int
    clickmode: int
    clickmove: int
    clickmoveinactive: int
    clicksustain: int
    clickthrough: int
    client_rect: Sequence[float]
    clip: int
    clip_size: int
    clipdraw: int
    clipheight: float
    code: str
    coldcolor: Sequence[float]
    colhead: int
    collection: str
    color: Sequence[float]
    colorlabels: int
    colormode: str
    colorselectedtext: int
    colortheme: Atom
    colortitlebar: int
    cols: int
    columns: int
    colwidth: int
    compatibility: int
    connectacrossdividers: int
    constrainduplicates: int
    constrainpointchanges: int
    contdata: int
    contrast: float
    contrastactivetab: int
    convertobj: int
    cool: int
    coolcolor: Sequence[float]
    copysupport: int
    crashrecovery: str
    curvecolor: Sequence[float]
    data: Any
    database: int
    datadirty: int
    dbdisplay: int
    dbperled: int
    debugqueuesize: int
    decodemode: int
    default_template: str
    defaultcachesize: float
    defaultglcontext: str
    defaultm4ldevicesfolder: str
    defaultpatchersize: int
    defaultprojectsfolder: str
    defer: int
    degrees: int
    delay: Union[float, int]
    depth: Union[float, int]
    description: str
    devpath: str
    devpathtype: int
    dialcolor: Sequence[float]
    dialmode: int
    dialtracking: int
    digest: str
    dimmedconnectionalpha: float
    direction: int
    direction_height: float
    directioncolor: Sequence[float]
    dirty: int
    disabledalpha: float
    disabledcolor: Sequence[float]
    disablefind: int
    display_flat: int
    display_range: Sequence[float]
    displayamount: int
    displaychan: int
    displayknob: int
    displaymode: int
    displaysinglechannel: int
    dividercolor: Sequence[float]
    dividers: Atom
    dividersize: int
    domain: float
    domainlabel: str
    dontreplace: int
    downarrow: int
    drag_window: int
    dragtrack: int
    drawline: int
    drawoffcolor: int
    drawpeakhold: int
    drawpeaks: int
    drawstyle: int
    drawto: str
    dsp_cpulimit: str
    dsp_driver: int
    dsp_inputdevice: str
    dsp_iovectorsize: str
    dsp_option1: str
    dsp_option2: str
    dsp_outputdevice: str
    dsp_overdrive: str
    dsp_samplerate: str
    dsp_siai: str
    dsp_signalvectorsize: str
    dstrect: Sequence[int]
    duration_active: int
    dynamic: int
    editing_bgcolor: Sequence[float]
    editlocked: int
    editlooponly: int
    editor_rect: Sequence[float]
    elementcolor: Sequence[float]
    embed: int
    emptycolor: Sequence[float]
    enable: int
    enabled: int
    enablednotes: Sequence[Atom]
    enabledrag: int
    enableglobalcontext: int
    enablehscroll: int
    enablesprites: int
    enablevscroll: int
    erase_color: Sequence[float]
    exclusive: int
    expansion: str
    export_dpi: int
    exportfolder: str
    exportname: str
    exportnotifier: str
    exportscript: str
    exportscriptargs: str
    externaleditor: str
    extra1_active: int
    extra1_max: int
    extra1_min: int
    extra1_signed: int
    extra2_active: int
    extra2_max: int
    extra2_min: int
    extra2_signed: int
    extra_thickness: float
    factorycontent: int
    fblend: int
    fgcolor: Sequence[float]
    fgdialcolor: Sequence[float]
    file: str
    filekind: str
    filename: str
    fillhorizontalspace: int
    filternodeschanges: int
    filtertext: str
    flagmode: int
    floateditorwindow: int
    floatoutput: int
    focusbordercolor: Sequence[float]
    folderslash: int
    followglobaltempo: int
    followlivetheme: Atom
    fontface: int
    fontlink: int
    fontname: str
    fontsize: float
    forceaspect: int
    forcejwebrendermode: int
    formant: float
    formantcorrection: int
    format: int
    fps: float
    frames: int
    freezecolor: Sequence[float]
    ft1: float
    fullspect: int
    gaincaption: int
    gaindragmode: int
    gainradius: float
    gainstyle: int
    genericeditor: int
    gensupport: int
    gfxengine: str
    ghostbar: int
    gizmos: int
    globalpatchername: str
    globalzoomfactor: int
    gradient: float
    graphcolor: Sequence[float]
    graphmode: str
    grid: Union[float, int]
    gridcolor: Sequence[float]
    gridlinecolor: Sequence[float]
    gridorigincolor: Sequence[float]
    gridstep_x: float
    gridstep_y: float
    hbgcolor: Sequence[float]
    hcellcolor: Sequence[float]
    hcurvecolor: Sequence[float]
    headercolor: Sequence[float]
    headerheight: int
    headerlabel: str
    hgraphcolor: Sequence[float]
    hidden: int
    hideloop: int
    hiderwff: int
    hilite: int
    hint: str
    hires: int
    hkeycolor: Sequence[float]
    hltcolor: Sequence[float]
    hlttextcolor: Sequence[float]
    horizontal_direction: int
    horizontalmargin: int
    horizontalspacing: int
    horizontaltracking: float
    hotcolor: Sequence[float]
    hscroll: int
    hsync: int
    htabcolor: Sequence[float]
    htextcolor: Sequence[float]
    htricolor: Sequence[float]
    idle: int
    idlemouse: int
    ignoreclick: int
    ignoreconnected: int
    ignoreemptyinterp: int
    illustrationspeed: int
    imagemask: int
    inactive: int
    inactivealpha: float
    inactivecoldcolor: Sequence[float]
    inactiveimage: int
    inactivelcdcolor: Sequence[float]
    inactivetextoffcolor: Sequence[float]
    inactivetextoncolor: Sequence[float]
    inactivewarmcolor: Sequence[float]
    inc: float
    includepackages: int
    incolormap: Atom
    increment: float
    index: int
    initial: Sequence[Atom]
    initialgain: float
    inlabels: Atom
    inputmode: int
    inputrangemode: int
    inputs: int
    inspectreadonly: int
    int: int
    interp: Union[float, int]
    interpinlet: int
    interval: Union[float, int]
    invert: int
    invisiblebkgnd: int
    items: Sequence[Any]
    jsarguments: Sequence[Atom]
    jump: int
    just: int
    justification: int
    jwebremotedebuggingport: int
    keymode: int
    keynavigate: int
    knobcolor: Sequence[float]
    knobpict: str
    knobshape: int
    knobsize: float
    labelclick: int
    labelheight: float
    labels: int
    labeltextcolor: Sequence[float]
    labelwidth: float
    lastchannelcount: int
    latency: Union[float, int]
    layoutbubbles: int
    lcdbgcolor: Sequence[float]
    lcdcolor: Sequence[float]
    leftarrow: int
    leftmargin: int
    leftvalue: int
    legacy: int
    legacyoutputorder: int
    legacytextcolor: int
    legacytransport: int
    legend: Union[int, str]
    linecolor: Sequence[float]
    linecount: int
    linenumbers: int
    linenumberwidth: int
    lines: int
    linethickness: float
    link: int
    linmarkers: Sequence[float]
    listmode: int
    listresize: int
    livemode: int
    loadbangonpaste: int
    local: int
    lock: int
    locked_bgcolor: Sequence[float]
    lockeddragscroll: int
    lockedsize: int
    logamp: int
    logfreq: int
    loglevel: int
    logmarkers: Sequence[float]
    logtosystemconsole: int
    loop: int
    loopbordercolor: Sequence[float]
    loopreport: int
    loopruler: int
    lsbfirst: int
    margin: int
    margins: Sequence[float]
    marker_horizontal: int
    marker_vertical: int
    markercolor: Sequence[float]
    markers: Sequence[int]
    markersused: int
    matrixmode: int
    maxdynamicnodes: int
    maxgain: float
    maximum: Atom
    maxurlproxyname: str
    maxwindow_dequeuesize: int
    maxwindow_fontname: str
    maxwindow_fontsize: int
    maxwindow_queuesize: int
    mcisolate: int
    mctrigchan: int
    menu_display: int
    menumode: int
    metering: int
    min: float
    minimum: Atom
    mode: Union[int, str]
    modulationcolor: Sequence[float]
    monitormode: int
    monochrome: int
    monotone: int
    mousefilter: int
    mousemode: int
    mousereport: int
    mouseup: int
    movehorizontal: int
    movevertical: int
    mult: float
    multiline: int
    multiplier: int
    multiselect: int
    multislider: int
    n4m_debug_log_enabled: int
    n4m_debug_log_folder: str
    n4m_debug_log_name: str
    n4m_external_node_binary: str
    n4m_process_manager_path: str
    name: str
    needlecolor: Sequence[float]
    needlemode: int
    neverdirty: int
    nfilters: int
    nhotleds: int
    nodecolor: Sequence[float]
    nodenumber: int
    nodesnames: Sequence[str]
    nofsaa: int
    noloadbangdefeating: int
    normalized: int
    norulerclick: int
    nosymquotes: int
    notebase: int
    notelist: Sequence[str]
    notename: int
    nseq: int
    nsize: Sequence[float]
    ntepidleds: int
    numdecimalplaces: int
    numdisplay: int
    numins: int
    numleds: int
    numouts: int
    numplots: int
    numpoints: int
    nwarmleds: int
    offcolor: Sequence[float]
    offset: Union[Sequence[float], float, int]
    oncolor: Sequence[float]
    onscreen: int
    orientation: int
    originallength: TimeValue
    originaltempo: float
    oscdefer: int
    oscparamenableddefault: int
    oscprefix: str
    oscprefixmode: int
    oscqueryenable: int
    oscqueryport: int
    oscreceivemode: int
    oscreceivequantize: TimeValue
    oscreceivethreshold: TimeValue
    oscreceiveudpport: int
    oscsendmode: int
    oscsendthreshold: TimeValue
    oscsendudpaddr: str
    oscsendudpport: int
    oscuseparamprefix: int
    oscvaluemode: int
    outcolormap: Atom
    outlabels: Atom
    outlinecolor: Sequence[float]
    outmode: int
    output_texture: int
    outputalpha: int
    outputformat: str
    outputmode: int
    outputonclick: int
    outputs: int
    overdrive: int
    overgaincolor: Sequence[float]
    overloadcolor: Sequence[float]
    panelcolor: Sequence[float]
    param_connect: str
    parameter_enable: int
    parameter_mappable: int
    paramonly: int
    patcher: Any
    patcher_boxsnapmargin: Atom
    patcherinspector: int
    patchername: str
    patchingmargin: int
    patchingmarginpercent: float
    patchingmechanics: int
    patchline_curved: int
    patchlinecolor: Sequence[float]
    pattrmode: int
    pconstrain: int
    peakcolor: Sequence[float]
    permissive: int
    phasespect: int
    pic: str
    pickray: int
    pictures: Sequence[str]
    pitch_active: int
    pitchcorrection: int
    pitchdetection: int
    pitchshift: float
    pitchshiftcent: int
    planemap: Sequence[int]
    pointalign: float
    pointcolor: Sequence[float]
    pointsize: float
    polezerocolor: Sequence[float]
    poll: int
    popupbrowserbar: int
    precision: int
    prefer: str
    preffilename: str
    prefix: str
    prefix_mode: int
    presentation: int
    presentation_rect: Sequence[float]
    preservegain: int
    preset_data: Sequence[Any]
    preview: int
    prioritizeexterns: int
    prioritizepatchlines: int
    prototypename: str
    quality: str
    quiet: int
    range: Sequence[Atom]
    rangelabel: str
    ratio: int
    readonly: int
    realtime_params: int
    reflection: int
    reflectioncolor: Sequence[float]
    refreshrate: float
    relative: int
    release: Union[float, int]
    remapsvgcolors: int
    rendermode: int
    reportprogress: int
    restorewindows: int
    retune: int
    rightarrow: int
    rightmargin: int
    rightvalue: int
    rnbo_classname: str
    rnbo_extra_attributes: Dict[str, Any]
    rnbo_log_file: str
    rnbo_log_folder: str
    rnbo_log_level: int
    rnbo_server_autostart: int
    rounded: float
    rowhead: int
    rowheight: int
    rows: int
    running: int
    saturation: float
    saved_attribute_attributes: Dict[str, Any]
    saved_object_attributes: Dict[str, Any]
    savedependencies: int
    savemode: int
    savesingletons: int
    scale: Union[float, int]
    scaleknob: int
    sccolor: Sequence[float]
    scroll: int
    searchformissingfiles: int
    segmented: int
    segpatchcords: int
    selectalpha: float
    selectedclick: int
    selectioncolor: Sequence[float]
    selector: str
    selecttextonclick_patching: int
    selmode: int
    selsync: int
    separator: str
    setarrowkeysscrollpatcher: int
    seteventinterval: int
    setminmax: Sequence[float]
    setmixergbitmode: int
    setmixerlatency: float
    setmixerparallel: int
    setmixerramptime: float
    setmode: int
    setnativefontpanel: int
    setpollthrottle: int
    setqueuethrottle: int
    setresizes: int
    setscrollbarmode: int
    setslop: float
    setstyle: int
    setsysqelemthrottle: int
    settype: int
    setunit: int
    sgcolor: Sequence[float]
    shadow: int
    shadowactive: int
    shadowalpha: float
    shadowblend: float
    shadowline: int
    shadoworientation: int
    shadowperbar: int
    shadowproportion: float
    shadowreflectionpoint: float
    shadowsigned: int
    shape: int
    showcaption: int
    showcluebar: int
    showdotfiles: int
    showeditor: int
    showgain: int
    showgetonly: int
    showheader: int
    showlabels: int
    showname: int
    shownumber: int
    signalmode: str
    signalusecols: int
    signed: int
    sigoutmode: int
    size: float
    slidercolor: Sequence[float]
    slurtime: float
    smoothing: float
    snap: int
    snap2grid: int
    snapto: int
    snaptopixelbydefault: int
    sono: int
    sonohicolor: Sequence[float]
    sonolocolor: Sequence[float]
    sonomedcolor: Sequence[float]
    sonomedhicolor: Sequence[float]
    sonomedlocolor: Sequence[float]
    sonomonobgcolor: Sequence[float]
    sonomonofgcolor: Sequence[float]
    sortmode: int
    spacing: Union[float, int]
    spacing_x: float
    spacing_y: float
    srcrect: Sequence[int]
    staffs: int
    statusvisible: int
    stay: int
    stcolor: Sequence[float]
    stepcolor: Sequence[float]
    stepcolor2: Sequence[float]
    storage_rect: Sequence[float]
    stored1: Sequence[float]
    storeinpreset: int
    stripe2: Sequence[float]
    stripecolor: Sequence[float]
    style: str
    suppressinlet: int
    svg: str
    switchcolor: Sequence[float]
    sync: int
    syntax: str
    syntax_attrargcolor: Sequence[float]
    syntax_attributecolor: Sequence[float]
    syntax_objargcolor: Sequence[float]
    syntax_objectcolor: Sequence[float]
    syntaxcoloring: int
    syntaxcolorset: Atom
    systimerearlywake: int
    tabcolor: Sequence[float]
    table_data: Sequence[float]
    tabmode: int
    tabs: Sequence[str]
    tags: str
    template: str
    tepidcolor: Sequence[float]
    text_width: float
    textcolor: Sequence[float]
    textcolor_inverse: Sequence[float]
    textjustification: int
    textoffcolor: Sequence[float]
    texton: str
    textoncolor: Sequence[float]
    textovercolor: Sequence[float]
    thickness: Union[float, int]
    thinmode: str
    thinthresh: int
    thinto: float
    threshold: float
    threshold_db: float
    threshold_linear: float
    ticks: int
    timestretch: int
    toggle: int
    tool: int
    toolbarcluemode: int
    toolbarquickrecord_format: int
    toolbarquickrecord_redbutton: int
    topmargin: int
    topvalue: int
    tosymbol: int
    trackcircular: int
    trackhorizontal: int
    tracking: int
    trackvertical: int
    transition: int
    translation: str
    triangle: int
    tribordercolor: Sequence[float]
    tricolor: Sequence[float]
    tricolor2: Sequence[float]
    trigger: int
    triglevel: float
    trioncolor: Sequence[float]
    triscale: float
    truncate: int
    types: Union[Atom, str]
    uncheckedcolor: Sequence[float]
    underline: int
    unitruler: int
    uparrow: int
    url: str
    use_16bit: int
    usebgoncolor: int
    usedstrect: int
    useexternaleditor: int
    useoffcolor: int
    usepicture: int
    usesearchpath: int
    useselectioncolor: int
    usespacesforjed: int
    usesrcrect: int
    usestepcolor2: int
    usesvgviewbox: int
    usetextovercolor: int
    usewebeditor: int
    valign: int
    valuemode: int
    valuepopup: int
    valuepopuplabel: int
    varname: str
    velocity_active: int
    vertical_direction: int
    verticalmargin: int
    verticalspacing: int
    verticaltracking: float
    videoengine: str
    viewvisibility: Any
    vlabels: int
    voffset: float
    vscroll: int
    vstscanmode: int
    vsync: int
    vticks: int
    vtracking: int
    vzoom: float
    warmcolor: Sequence[float]
    waveformcolor: Sequence[float]
    waveformdisplay: int
    wheelzoomdirection: int
    wheelzoomfactor: float
    whitekeycolor: Sequence[float]
    wiggletime: int
    wordwrap: int
    xoffset: float
    xplace: Sequence[float]
    yoffset: float
    yplace: Sequence[float]
    zoom_orientation: int
    zoomstyle: int
    zoomthresh: float


#: Every property name in :class:`BoxProps`, for runtime checks.
BOX_PROP_NAMES = frozenset(BoxProps.__annotations__)


# --------------------------------------------------------------------------
# py2max/core/abstract.py
# --------------------------------------------------------------------------


class AbstractLayoutManager(ABC):
    """Abstract base class for LayoutManager objects.

    This class defines the interface that layout managers expect from
    a LayoutManager object, allowing layout.py to reference LayoutManager without
    creating circular imports.
    """

    # Required attributes
    box_height: float

    @abstractmethod
    def get_rect_from_maxclass(self, maxclass: str) -> Optional[Rect]:
        """retrieves default patching_rect from defaults dictionary."""
        ...

    @abstractmethod
    def get_relative_pos(self, rect: Rect) -> Rect:
        """returns a relative position for the object"""
        ...

    @abstractmethod
    def get_absolute_pos(self, rect: Rect) -> Rect:
        """returns an absolute position for the object"""
        ...

    @abstractmethod
    def get_pos(self, maxclass: Optional[str] = None) -> Rect:
        """get box rect (position) via maxclass or layout_manager"""
        ...

    @abstractmethod
    def above(self, rect: Rect) -> Rect:
        """Return a position of a comment above the object"""
        ...


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
    numinlets: int
    numoutlets: int
    _kwds: Dict[str, Any]

    @abstractmethod
    def render(self) -> None:
        """Render the box object."""
        ...

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert the box to a dictionary representation."""
        ...

    @abstractmethod
    def __iter__(self) -> Iterator[Any]:
        """Make the box iterable."""
        ...


class AbstractPatchline(ABC):
    """Abstract base class for Patchline objects.

    This class defines the interface that layout managers expect from
    a Patchline object, allowing layout.py to reference Patchline without
    creating circular imports.
    """

    @property
    @abstractmethod
    def src(self) -> str:
        """Source object identifier."""
        ...

    @property
    @abstractmethod
    def dst(self) -> str:
        """Destination object identifier."""
        ...

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert the patchline to a dictionary representation."""
        ...


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
        ...

    @property
    @abstractmethod
    def height(self) -> float:
        """Height of patcher window."""
        ...

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
    _reset_on_render: bool
    _flow_direction: str
    _cluster_connected: bool
    _layout_mgr: AbstractLayoutManager
    _auto_hints: bool
    _validate_connections: bool
    _validate_attrs: bool
    _maxclass_methods: dict[str, Callable[..., Any]]
    _semantic_ids: bool
    _semantic_counters: dict[str, int]
    _device_type: str
    classnamespace: str
    _pending_comments: list[tuple[str, str, Optional[str]]]
    # Rendered (dict) forms, populated by render() and read by serialization.
    boxes: list[dict[str, Any]]
    lines: list[dict[str, Any]]

    # Core methods implemented by Patcher and relied on by the BoxFactory and
    # serialization mixins. Declared here (non-abstract) so each mixin can be
    # type-checked in isolation; Patcher provides the real implementations.
    def get_id(self, object_name: Optional[str] = None) -> str:
        """Generate an object id (implemented by Patcher)."""
        raise NotImplementedError

    def get_pos(self, maxclass: Optional[str] = None) -> Rect:
        """Get a box position from the layout manager (implemented by Patcher)."""
        raise NotImplementedError

    def render(self, reset: bool = False) -> None:
        """Render boxes/lines to dicts (implemented by Patcher)."""
        raise NotImplementedError

    def _process_pending_comments(self) -> None:
        """Position deferred associated comments (implemented by Patcher)."""
        raise NotImplementedError


# --------------------------------------------------------------------------
# py2max/maxref/legacy.py
# --------------------------------------------------------------------------


LEGACY_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "button": {
        "maxclass": "button",
        "numinlets": 1,
        "numoutlets": 1,
        "outlettype": ["bang"],
        "parameter_enable": 0,
        "patching_rect": Rect(x=0.0, y=0.0, w=24.0, h=24.0),
    },
    "codebox": {
        "maxclass": "codebox",
        "numinlets": 1,
        "numoutlets": 1,
        "outlettype": [""],
        "patching_rect": Rect(x=191.0, y=118.0, w=200.0, h=200.0),
    },
    "codebox~": {
        "maxclass": "codebox~",
        "numinlets": 1,
        "numoutlets": 1,
        "outlettype": [""],
        "patching_rect": Rect(x=191.0, y=118.0, w=200.0, h=200.0),
    },
    "gen.codebox~": {
        "maxclass": "gen.codebox~",
        "numinlets": 1,
        "numoutlets": 1,
        "outlettype": ["signal"],
        "patching_rect": Rect(x=60.0, y=107.0, w=688.0, h=471.0),
    },
    "dial": {
        "maxclass": "dial",
        "numinlets": 1,
        "numoutlets": 1,
        "outlettype": ["float"],
        "parameter_enable": 0,
        "patching_rect": Rect(x=0.0, y=0.0, w=40.0, h=40.0),
    },
    "ezadc~": {
        "maxclass": "ezadc~",
        "numinlets": 1,
        "numoutlets": 2,
        "outlettype": ["signal", "signal"],
        "patching_rect": Rect(x=0.0, y=0.0, w=45.0, h=45.0),
    },
    "ezdac~": {
        "maxclass": "ezdac~",
        "numinlets": 2,
        "numoutlets": 0,
        "patching_rect": Rect(x=0.1, y=1.0, w=45.0, h=45.0),
    },
    "filtergraph~": {
        "fontface": 0,
        "linmarkers": [0.0, 11025.0, 16537.5],
        "logmarkers": [0.0, 100.0, 1000.0, 10000.0],
        "maxclass": "filtergraph~",
        "nfilters": 1,
        "numinlets": 8,
        "numoutlets": 7,
        "outlettype": ["list", "float", "float", "float", "float", "list", "int"],
        "parameter_enable": 0,
        "patching_rect": Rect(x=1.0, y=1.0, w=256.0, h=128.0),
        "setfilter": [0, 5, 1, 0, 0, 40.0, 1.0, 2.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    },
    "function": {
        "maxclass": "function",
        "numinlets": 1,
        "numoutlets": 4,
        "outlettype": ["float", "", "", "bang"],
        "parameter_enable": 0,
        "patching_rect": Rect(x=0.0, y=0.0, w=200.0, h=100.0),
    },
    "gain~": {
        "maxclass": "gain~",
        "multichannelvariant": 0,
        "numinlets": 1,
        "numoutlets": 2,
        "outlettype": ["signal", ""],
        "parameter_enable": 0,
        "patching_rect": Rect(x=0.0, y=0.0, w=22.0, h=140.0),
    },
    "gswitch": {
        "maxclass": "gswitch",
        "numinlets": 3,
        "numoutlets": 1,
        "outlettype": [""],
        "parameter_enable": 0,
        "patching_rect": Rect(x=0.0, y=0.0, w=41.0, h=32.0),
    },
    "gswitch2": {
        "maxclass": "gswitch2",
        "numinlets": 2,
        "numoutlets": 2,
        "outlettype": ["", ""],
        "parameter_enable": 0,
        "patching_rect": Rect(x=0.0, y=0.0, w=39.0, h=32.0),
    },
    "incdec": {
        "maxclass": "incdec",
        "numinlets": 1,
        "numoutlets": 1,
        "outlettype": ["float"],
        "parameter_enable": 0,
        "patching_rect": Rect(x=0.0, y=0.0, w=20.0, h=24.0),
    },
    "kslider": {
        "maxclass": "kslider",
        "numinlets": 2,
        "numoutlets": 2,
        "outlettype": ["int", "int"],
        "parameter_enable": 0,
        "patching_rect": Rect(x=0.0, y=0.0, w=336.0, h=53.0),
    },
    "led": {
        "maxclass": "led",
        "numinlets": 1,
        "numoutlets": 1,
        "outlettype": ["int"],
        "parameter_enable": 0,
        "patching_rect": Rect(x=0.0, y=0.0, w=24.0, h=24.0),
    },
    "levelmeter~": {
        "markers": [-60, -48, -36, -24, -12, -6, 0, 6],
        "markersused": 8,
        "maxclass": "levelmeter~",
        "numinlets": 1,
        "numoutlets": 1,
        "outlettype": [""],
        "patching_rect": Rect(x=0.0, y=0.0, w=128.0, h=64.0),
    },
    "matrixctrl": {
        "maxclass": "matrixctrl",
        "numinlets": 1,
        "numoutlets": 2,
        "outlettype": ["list", "list"],
        "parameter_enable": 0,
        "patching_rect": Rect(x=0.0, y=0.0, w=130.0, h=66.0),
    },
    "meter~": {
        "maxclass": "meter~",
        "numinlets": 1,
        "numoutlets": 1,
        "outlettype": ["float"],
        "patching_rect": Rect(x=0.0, y=0.0, w=80.0, h=13.0),
    },
    "multislider": {
        "maxclass": "multislider",
        "numinlets": 1,
        "numoutlets": 2,
        "orientation": 1,
        "outlettype": ["", ""],
        "parameter_enable": 0,
        "patching_rect": Rect(x=0.0, y=0.0, w=20.0, h=140.0),
        "setstyle": 0,
        "size": 4,
    },
    "nodes": {
        "maxclass": "nodes",
        "nodesnames": ["1"],
        "nsize": [0.2],
        "numinlets": 1,
        "numoutlets": 3,
        "outlettype": ["", "", ""],
        "parameter_enable": 0,
        "patching_rect": Rect(x=231.0, y=478.0, w=100.0, h=100.0),
        "xplace": [0.083333333333333],
        "yplace": [0.083333333333333],
    },
    "nslider": {
        "maxclass": "nslider",
        "numinlets": 2,
        "numoutlets": 2,
        "outlettype": ["int", "int"],
        "parameter_enable": 0,
        "patching_rect": Rect(x=0.0, y=0.0, w=75.0, h=198.0),
    },
    "number~": {
        "fontface": 0,
        "fontname": "Arial",
        "fontsize": 12.0,
        "maxclass": "number~",
        "mode": 2,
        "numinlets": 2,
        "numoutlets": 2,
        "outlettype": ["signal", "float"],
        "patching_rect": Rect(x=0.0, y=0.0, w=56.0, h=22.0),
        "sig": 0.0,
    },
    "pictctrl": {
        "maxclass": "pictctrl",
        "numinlets": 1,
        "numoutlets": 1,
        "outlettype": ["int"],
        "parameter_enable": 0,
        "patching_rect": Rect(x=0.0, y=0.0, w=20.0, h=20.0),
    },
    "pictslider": {
        "maxclass": "pictslider",
        "numinlets": 2,
        "numoutlets": 2,
        "outlettype": ["int", "int"],
        "parameter_enable": 0,
        "patching_rect": Rect(x=0.0, y=0.0, w=100.0, h=100.0),
    },
    "playbar": {
        "maxclass": "playbar",
        "numinlets": 1,
        "numoutlets": 2,
        "outlettype": ["", "int"],
        "patching_rect": Rect(x=0.0, y=0.0, w=320.0, h=16.0),
    },
    "playlist~": {
        "basictuning": 0,
        "data": {"clips": []},
        "followglobaltempo": 0,
        "formantcorrection": 0,
        "maxclass": "playlist~",
        "mode": 0,
        "numinlets": 1,
        "numoutlets": 5,
        "originallength": [0],
        "originaltempo": 0,
        "outlettype": ["signal", "signal", "signal", "", "dictionary"],
        "parameter_enable": 0,
        "patching_rect": Rect(x=0.0, y=0.0, w=150.0, h=92.0),
        "pitchcorrection": 0,
        "quality": 0,
        "timestretch": [0],
    },
    "radiogroup": {
        "disabled": [0, 0],
        "itemtype": 0,
        "maxclass": "radiogroup",
        "numinlets": 1,
        "numoutlets": 1,
        "outlettype": [""],
        "parameter_enable": 0,
        "patching_rect": Rect(x=0.0, y=0.0, w=18.0, h=34.0),
        "size": 2,
        "value": 0,
    },
    "rslider": {
        "maxclass": "rslider",
        "numinlets": 2,
        "numoutlets": 2,
        "outlettype": ["", ""],
        "parameter_enable": 0,
        "patching_rect": Rect(x=0.0, y=0.0, w=20.0, h=140.0),
    },
    "scope~": {
        "maxclass": "scope~",
        "numinlets": 2,
        "numoutlets": 0,
        "patching_rect": Rect(x=0.0, y=0.0, w=130.0, h=130.0),
    },
    "slider": {
        "maxclass": "slider",
        "numinlets": 1,
        "numoutlets": 1,
        "outlettype": [""],
        "parameter_enable": 0,
        "patching_rect": Rect(x=0.0, y=0.0, w=20.0, h=140.0),
    },
    "spectroscope~": {
        "maxclass": "spectroscope~",
        "numinlets": 2,
        "numoutlets": 1,
        "outlettype": [""],
        "patching_rect": Rect(x=0.0, y=0.0, w=300.0, h=100.0),
    },
    "tab": {
        "maxclass": "tab",
        "numinlets": 1,
        "numoutlets": 3,
        "outlettype": ["int", "", ""],
        "parameter_enable": 0,
        "patching_rect": Rect(x=0.0, y=0.0, w=200.0, h=24.0),
    },
    "textbutton": {
        "maxclass": "textbutton",
        "numinlets": 1,
        "numoutlets": 3,
        "outlettype": ["", "", "int"],
        "parameter_enable": 0,
        "patching_rect": Rect(x=0.0, y=0.0, w=100.0, h=20.0),
    },
    "toggle": {
        "maxclass": "toggle",
        "numinlets": 1,
        "numoutlets": 1,
        "outlettype": ["int"],
        "parameter_enable": 0,
        "patching_rect": Rect(x=0.0, y=0.0, w=24.0, h=24.0),
    },
    "ubutton": {
        "handoff": "",
        "maxclass": "ubutton",
        "numinlets": 1,
        "numoutlets": 4,
        "outlettype": ["bang", "bang", "", "int"],
        "parameter_enable": 0,
        "patching_rect": Rect(x=0.0, y=0.0, w=33.0, h=42.0),
    },
    "waveform~": {
        "buffername": "",
        "maxclass": "waveform~",
        "numinlets": 5,
        "numoutlets": 6,
        "outlettype": ["float", "float", "float", "float", "list", ""],
        "patching_rect": Rect(x=0.0, y=0.0, w=256.0, h=64.0),
    },
    "zplane~": {
        "maxclass": "zplane~",
        "numinlets": 5,
        "numoutlets": 4,
        "outlettype": ["list", "list", "list", "list"],
        "patching_rect": Rect(x=0.0, y=0.0, w=256.0, h=256.0),
    },
}


# --------------------------------------------------------------------------
# py2max/maxref/category.py
# --------------------------------------------------------------------------


INPUT_OBJECTS = set(
    [
        "adc~",
        "bendin",
        "ctlin",
        "hi",
        "in",
        "in~",
        "inlet",
        "key",
        "keyup",
        "midiin",
        "mousestate",
        "notein",
        "param",
        "pgmin",
        "receive",
        "receive~",
        "r",
        "sel",
        "select",
        "touchin",
        "udpreceive",
    ]
)
# Note: ``route`` and ``unpack`` are message *processors*, not inputs -- they
# live in PROCESSOR_OBJECTS. ``adc~`` and ``receive~`` are signal *sources*, so
# they stay here (INPUT) and are intentionally absent from OUTPUT_OBJECTS. These
# used to be duplicated across sets; since INPUT is matched first the duplicates
# were dead. See _classify_object.

CONTROL_OBJECTS = set(
    [
        "attrui",
        "bendin",
        "button",
        "ctlin",
        "dial",
        "flonum",
        "key",
        "keyup",
        "loadbang",
        "loadmess",
        "message",
        "metro",
        "midiin",
        "mousestate",
        "notein",
        "number",
        "pcontrol",
        "pgmin",
        "preset",
        "slider",
        "toggle",
        "touchin",
        "umenu",
    ]
)

GENERATOR_OBJECTS = set(
    [
        "adsr~",
        "buffer~",
        "curve~",
        "cycle~",
        "drunk",
        "function",
        "groove~",
        "line~",
        "noise~",
        "phasor~",
        "pink~",
        "play~",
        "ramp~",
        "random",
        "rect~",
        "saw~",
        "sfplay~",
        "sig~",
        "tri~",
        "urn",
    ]
)

PROCESSOR_OBJECTS = set(
    [
        "%~",
        "*~",
        "+~",
        "-~",
        "/~",
        "abs~",
        "accum",
        "allpass~",
        "atan2~",
        "bag",
        "biquad~",
        "bucket",
        "cartopol~",
        "clip~",
        "comb~",
        "cos~",
        "counter",
        "cross~",
        "degrade~",
        "delay~",
        "expr",
        "filtergraph~",
        "gain~",
        "gate",
        "gate~",
        "if",
        "log~",
        "lores~",
        "overdrive~",
        "pack",
        "poltocar~",
        "pow~",
        "reson~",
        "route",
        "scale",
        "selector~",
        "slide~",
        "split",
        "sqrt~",
        "switch",
        "tanh~",
        "tapin~",
        "tapout~",
        "thresh~",
        "unpack",
    ]
)

OUTPUT_OBJECTS = set(
    [
        "bendout",
        "capture~",
        "ctlout",
        "dac~",
        "error",
        "ezadc~",
        "ezdac~",
        "levelmeter~",
        "meter~",
        "midiout",
        "noteout",
        "out~",
        "pgmout",
        "print",
        "record~",
        "scope~",
        "send~",
        "sfrecord~",
        "snapshot~",
        "spectroscope~",
        "touchout",
    ]
)


# ---------------------------------------------------------------------------
# Offline maxref data layer (generated)
#
# In the package this is XML parsing over a Max installation with a 1 MB
# documentation bundle as fallback. Here it is a distilled table: port types,
# method names and attribute names for 1175 objects, with all prose
# dropped. Enough for connection validation, port counts, object defaults and
# attribute checking; not enough for help() -- see get_object_help below.

_MAXREF_BLOB = (
    "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"
)

_MAXREF_TABLE: Optional[Dict[str, Any]] = None


def _maxref_table() -> Dict[str, Any]:
    """Decode the embedded table on first use."""
    global _MAXREF_TABLE
    if _MAXREF_TABLE is None:
        _MAXREF_TABLE = json.loads(gzip.decompress(base64.b64decode(_MAXREF_BLOB)))
    return _MAXREF_TABLE


def get_object_info(name: str) -> Optional[Dict[str, Any]]:
    """Structured info for a Max object, or None if it is unknown.

    Shaped like the package's parser output for the keys the included code
    reads. Prose keys (digest/description/examples/seealso) are absent.
    """
    entry = _maxref_table().get(name)
    if entry is None:
        return None
    return {
        "name": name,
        "inlets": [{"type": t} for t in entry["it"]],
        "outlets": [{"type": t} for t in entry["ot"]],
        "methods": {m: {} for m in entry["m"]},
        "attributes": {a: {} for a in entry["a"]},
    }


def get_available_objects() -> List[str]:
    """Every Max object the embedded table knows about."""
    return sorted(_maxref_table())


def get_object_help(name: str) -> str:
    """Documentation is not embedded; point at the full package."""
    known = name in _maxref_table()
    return (
        f"No documentation for {name!r} in the single-file edition of py2max"
        + ("" if known else " (unknown object)")
        + ".\nInstall the full package for help(): pip install py2max"
    )


# --------------------------------------------------------------------------
# py2max/maxref/parser.py (partial: MAXCLASS_DEFAULTS, MaxClassDefaults, get_inlet_count, get_inlet_types, get_legacy_defaults, get_outlet_count, get_outlet_types, validate_connection)
# --------------------------------------------------------------------------


# Module logger

# Prebuilt bundle shipped in the wheel; used as a fallback when no local Max
# installation is found (e.g. on Linux). Generated by
# scripts/build_maxref_bundle.py on a Max-equipped machine.

# Sentinel marking a refdict entry that lives in the bundle, not on disk.

# Matches an ampersand that does NOT begin a valid XML entity (named, decimal,
# or hex character reference).

# Global cache instance


# Legacy compatibility - generate defaults from .maxref.xml when available
def get_legacy_defaults(name: str) -> Dict[str, Any]:
    """Get legacy-compatible defaults for a Max object

    This function extracts basic information needed for backwards compatibility
    with the old MAXCLASS_DEFAULTS structure.
    """
    data = get_object_info(name)
    if not data:
        return {}

    # Only set maxclass to the object name for objects that had explicit
    # maxclass entries in the legacy database. All other objects should
    # use "newobj" as maxclass (handled by fallback in core.py)

    defaults: Dict[str, Any] = {}
    if name in LEGACY_DEFAULTS:
        defaults["maxclass"] = name

    # Extract inlet/outlet counts and types
    inlets = data.get("inlets", [])
    outlets = data.get("outlets", [])

    if inlets:
        defaults["numinlets"] = len(inlets)

    if outlets:
        defaults["numoutlets"] = len(outlets)
        outlet_types = []
        for outlet in outlets:
            outlet_type = outlet.get("type", "").replace("OUTLET_TYPE", "")
            if not outlet_type:
                outlet_type = ""
            outlet_types.append(outlet_type)
        if outlet_types:
            defaults["outlettype"] = outlet_types

    # Set a default patching rect - this could be improved by analyzing
    # the palette info or other attributes in the future
    defaults["patching_rect"] = Rect(x=0.0, y=0.0, w=60.0, h=22.0)

    return defaults


def validate_connection(
    src_maxclass: str,
    src_outlet: int,
    dst_maxclass: str,
    dst_inlet: int,
    src_text: Optional[str] = None,
    dst_text: Optional[str] = None,
) -> tuple[bool, str]:
    """Validate a connection between two Max objects using the port-type model.

    Checks (a) that the outlet/inlet indices are in range (arg-aware, so
    ``limi~ 2`` is understood to have two ports) and (b) that the outlet's
    message kind is compatible with the inlet -- catching a control outlet wired
    into a signal-only inlet (e.g. ``metro -> cycle~``), which Max rejects.

    The message-type check is deliberately conservative: only clearly-wrong
    connections fail; anything ambiguous (or involving a maxref-unknown object)
    is allowed, so validation never rejects a valid patch.

    Args:
        src_maxclass: Source object's maxclass.
        src_outlet: Source outlet index (0-based).
        dst_maxclass: Destination object's maxclass.
        dst_inlet: Destination inlet index (0-based).
        src_text: Source box text (enables arg-aware outlet counts).
        dst_text: Destination box text (enables arg-aware inlet counts).

    Returns:
        Tuple of (is_valid: bool, error_message: str). ``is_valid`` is ``False``
        only for a definite error.
    """

    # Index bounds (arg-aware). Out-of-range = hard error (Max deletes the cord).
    _, src_outlets = porttypes.port_counts(src_maxclass, src_text)
    if src_outlets is not None and src_outlet >= src_outlets:
        return (
            False,
            f"Object '{src_maxclass}' only has {src_outlets} outlet(s), "
            f"cannot connect from outlet {src_outlet}",
        )
    dst_inlets, _ = porttypes.port_counts(dst_maxclass, dst_text)
    if dst_inlets is not None and dst_inlet >= dst_inlets:
        return (
            False,
            f"Object '{dst_maxclass}' only has {dst_inlets} inlet(s), "
            f"cannot connect to inlet {dst_inlet}",
        )

    # Message-type compatibility.
    emit = porttypes.outlet_emits(src_maxclass, src_outlet)
    accepts, authoritative = porttypes.inlet_acceptance(dst_maxclass, dst_inlet)
    if emit == porttypes.BANG and porttypes.inlet_rejects_bang(dst_maxclass, dst_inlet):
        return (
            False,
            f"Cannot connect a bang from '{src_maxclass}' to the signal inlet "
            f"{dst_inlet} of '{dst_maxclass}'",
        )
    if porttypes.message_compatible(emit, accepts, authoritative) is False:
        return (
            False,
            f"Cannot connect {emit} outlet of '{src_maxclass}' to inlet "
            f"{dst_inlet} of '{dst_maxclass}' (accepts {sorted(accepts)})",
        )
    return True, ""


def get_inlet_count(maxclass: str) -> Optional[int]:
    """Get the number of inlets for a Max object.

    Args:
        maxclass: The Max object class name

    Returns:
        Number of inlets or None if unknown
    """
    info = get_object_info(maxclass)
    if info and "inlets" in info:
        return len(info["inlets"])
    return None


def get_outlet_count(maxclass: str) -> Optional[int]:
    """Get the number of outlets for a Max object.

    Args:
        maxclass: The Max object class name

    Returns:
        Number of outlets or None if unknown
    """
    info = get_object_info(maxclass)
    if info and "outlets" in info:
        return len(info["outlets"])
    return None


def get_inlet_types(maxclass: str) -> List[str]:
    """Get the inlet types for a Max object.

    Args:
        maxclass: The Max object class name

    Returns:
        List of inlet type strings
    """
    info = get_object_info(maxclass)
    if info and "inlets" in info:
        return [inlet.get("type", "") for inlet in info["inlets"]]
    return []


def get_outlet_types(maxclass: str) -> List[str]:
    """Get the outlet types for a Max object.

    Args:
        maxclass: The Max object class name

    Returns:
        List of outlet type strings
    """
    info = get_object_info(maxclass)
    if info and "outlets" in info:
        return [outlet.get("type", "") for outlet in info["outlets"]]
    return []


# Two-layer object-defaults lookup exposed under the historical
# MAXCLASS_DEFAULTS name.
class MaxClassDefaults:
    """Object-defaults lookup with two layers.

    1. Curated overrides (``legacy.MAXCLASS_DEFAULTS``) -- authoritative,
       hand-tuned defaults for common/UI objects, including the correct
       ``patching_rect`` geometry the XML cannot provide.
    2. Dynamic maxref discovery (``get_legacy_defaults`` over ``.maxref.xml``)
       -- the fallback for the long tail of objects not in layer 1.

    Curated overrides win on purpose: maxref-derived defaults use a generic
    60x22 box and cannot infer UI sizes, so an object present in both layers
    must use its curated entry.
    """

    def __contains__(self, key: str) -> bool:
        """True if the object has curated defaults or a known .maxref.xml entry."""

        return key in LEGACY_DEFAULTS or get_object_info(key) is not None

    def __getitem__(self, key: str) -> Dict[str, Any]:
        """Get defaults: curated override first, then dynamic maxref discovery."""

        if key in LEGACY_DEFAULTS:
            return LEGACY_DEFAULTS[key]

        # Fall back to defaults derived dynamically from .maxref.xml.
        derived_defaults = get_legacy_defaults(key)
        if derived_defaults:
            return derived_defaults

        raise KeyError(f"No defaults found for maxclass '{key}'")

    def get(self, key: str, default: Any = None) -> Any:
        """Get defaults with fallback"""
        try:
            return self[key]
        except KeyError:
            return default

    def keys(self) -> Set[str]:
        """Get all available keys"""

        legacy_keys = set(LEGACY_DEFAULTS.keys())
        maxref_keys = set(get_available_objects())
        return legacy_keys | maxref_keys


# Create the compatibility instance
MAXCLASS_DEFAULTS = MaxClassDefaults()


# --------------------------------------------------------------------------
# py2max/maxref/porttypes.py
# --------------------------------------------------------------------------


_Counts = Tuple[Optional[int], Optional[int]]

# --- message kinds ---------------------------------------------------------
SIGNAL = "signal"  # MSP audio signal
BANG = "bang"
INT = "int"
FLOAT = "float"
LIST = "list"
ANY = "any"  # unknown control inlet/outlet -> treat permissively

_PLACEHOLDERS = {"", "inlet_type", "outlet_type"}

# --- curated overrides -----------------------------------------------------
# Outlets that emit a specific control message (maxref reports a placeholder).
# Keyed by maxclass -> {outlet_index: kind}. Kept small and high-confidence.
_OUTLET_EMIT = {
    "metro": {0: BANG},
    "tempo": {0: BANG},
    "loadbang": {0: BANG},
    "button": {0: BANG},  # the bng UI object
    "bangbang": {0: BANG, 1: BANG},
    "flonum": {0: FLOAT},
    "number": {0: INT},
    "toggle": {0: INT},
}

# Inlets maxref mis-types as control that are really signal-only. Keyed by
# maxclass -> {inlet_index: accept-set}.
_INLET_ACCEPTS = {
    "noise~": {0: frozenset({SIGNAL})},
    "pink~": {0: frozenset({SIGNAL})},
}

# Signal/float inlets on pure DSP objects that do NOT accept a bang (unlike
# envelope/ramp objects such as adsr~ / line~, whose signal/float inlet *is*
# bang-triggerable). Keyed by maxclass -> set of inlet indices. A bang into one
# of these is a definite error; this lets us catch e.g. metro -> cycle~ without
# false-positiving adsr~.
_SIGNAL_INLET_REJECTS_BANG = {
    "cycle~": {0, 1},
    "saw~": {0, 1},
    "tri~": {0, 1, 2},
    "rect~": {0, 1, 2},
    "phasor~": {0},
    "+~": {0, 1},
    "*~": {0, 1},
    "-~": {0, 1},
    "/~": {0, 1},
}


def _args(text: Optional[str]) -> List[str]:
    """Tokens after the object name in a box's ``text``."""
    return text.split()[1:] if text else []


def _first_int(args: List[str]) -> Optional[int]:
    for tok in args:
        if re.fullmatch(r"-?\d+", tok):
            return int(tok)
    return None


# Per-object port-count resolvers. Each maps the argument tokens to
# ``(n_inlets, n_outlets)``; ``None`` for a dimension means "use the maxref
# default". Two common families: counts that scale with a leading integer *value*
# (``limi~ 2`` -> 2), and counts that scale with the *number* of arguments
# (``select a b c`` -> 4 outlets = args + 1 reject outlet).
def _scale_value_both(a: List[str]) -> _Counts:
    n = _first_int(a)
    return (n, n) if n and n > 0 else (None, None)


def _scale_value_out(a: List[str]) -> _Counts:
    n = _first_int(a)
    return (None, n) if n and n > 0 else (None, None)


def _selector_counts(a: List[str]) -> _Counts:
    n = _first_int(a)  # selector~ N: N signal inlets + 1 control inlet, 1 outlet
    return (n + 1, None) if n and n > 0 else (None, None)


def _switch_counts(a: List[str]) -> _Counts:
    n = _first_int(a)  # switch N: N signal inlets + 1 control inlet, 1 outlet
    return (n + 1, None) if n and n > 0 else (None, None)


def _select_counts(a: List[str]) -> _Counts:
    return (None, len(a) + 1) if a else (None, None)  # match outlets + 1 reject


def _unpack_counts(a: List[str]) -> _Counts:
    return (None, len(a)) if a else (None, None)


def _pack_counts(a: List[str]) -> _Counts:
    return (len(a), None) if a else (None, None)


_ARG_RESOLVERS = {
    "limi~": _scale_value_both,
    "matrix~": _scale_value_both,
    "mc.pack~": _scale_value_out,
    "gate": _scale_value_out,
    "selector~": _selector_counts,
    "switch": _switch_counts,
    "select": _select_counts,
    "sel": _select_counts,
    "route": _select_counts,  # N match outlets + 1 passthrough
    "unpack": _unpack_counts,
    "pack": _pack_counts,
}


def _accepts_from_type(type_str: str) -> FrozenSet[str]:
    """Classify a maxref inlet ``type`` string into an accept-set."""
    t = (type_str or "").strip().lower()
    if t in _PLACEHOLDERS:
        return frozenset({ANY})
    has_signal = "signal" in t
    has_number = "float" in t or "int" in t
    if has_signal and has_number:
        return frozenset({SIGNAL, FLOAT, INT})
    if has_signal:
        return frozenset({SIGNAL})  # signal-only inlet
    kinds = set()
    if "bang" in t:
        kinds.add(BANG)
    if "float" in t:
        kinds.add(FLOAT)
    if "int" in t:
        kinds.add(INT)
    if "list" in t:
        kinds.add(LIST)
    return frozenset(kinds) if kinds else frozenset({ANY})


def _emit_from_type(type_str: str) -> str:
    """Classify a maxref outlet ``type`` string into a single emitted kind."""
    t = (type_str or "").strip().lower()
    if "signal" in t:
        return SIGNAL
    return ANY  # control outlet -- unknown unless curated


# --- public API ------------------------------------------------------------
def port_counts(
    maxclass: str, text: Optional[str] = None
) -> tuple[Optional[int], Optional[int]]:
    """Return ``(inlet_count, outlet_count)`` for an object, arg-aware.

    Uses the leading integer argument for objects whose I/O scales with it
    (``limi~ 2`` -> 2 in / 2 out), otherwise the maxref default. ``None`` for a
    dimension means "unknown" (skip range checks).
    """
    info = get_object_info(maxclass)
    n_in = len(info["inlets"]) if info and "inlets" in info else None
    n_out = len(info["outlets"]) if info and "outlets" in info else None
    resolver = _ARG_RESOLVERS.get(maxclass)
    if resolver is not None:
        r_in, r_out = resolver(_args(text))
        if r_in is not None:
            n_in = r_in
        if r_out is not None:
            n_out = r_out
    return n_in, n_out


def subpatcher_counts(box: object) -> _Counts:
    """Port counts for a subpatcher/bpatcher box, from its nested patcher.

    A subpatcher's real inlet/outlet count is the number of ``inlet`` / ``outlet``
    objects it contains, not the maxref default. Returns ``(None, None)`` for a
    box with no nested patcher.
    """
    child = getattr(box, "_patcher", None)
    if child is None:
        return (None, None)

    boxes = getattr(child, "_boxes", [])
    n_in = sum(1 for b in boxes if object_name(b) == "inlet")
    n_out = sum(1 for b in boxes if object_name(b) == "outlet")
    return (n_in, n_out)


def outlet_emits(maxclass: str, index: int) -> str:
    """Message kind emitted by ``maxclass``'s outlet ``index`` (``ANY`` if unsure)."""
    override = _OUTLET_EMIT.get(maxclass, {}).get(index)
    if override is not None:
        return override
    info = get_object_info(maxclass)
    outlets = info.get("outlets", []) if info else []
    if 0 <= index < len(outlets):
        return _emit_from_type(outlets[index].get("type", ""))
    return ANY


# maxref <methodlist> message names -> message kinds
_METHOD_TO_KIND = {
    "signal": SIGNAL,
    "bang": BANG,
    "int": INT,
    "float": FLOAT,
    "list": LIST,
}


def _accepts_from_methods(maxclass: str) -> Optional[FrozenSet[str]]:
    """Accept-set derived from an object's ``<methodlist>``, or ``None``.

    The method list is the object's real message vocabulary (Max's own docs).
    An ``anything`` method is a wildcard -> the inlet takes anything. Objects
    with no method list (e.g. ``+~``, ``noise~``) return ``None`` so the caller
    falls back to the type attribute / curated overrides.
    """
    info = get_object_info(maxclass)
    methods = info.get("methods", {}) if info else {}
    if not methods:
        return None
    if "anything" in methods:
        return frozenset({ANY})
    kinds = {kind for name, kind in _METHOD_TO_KIND.items() if name in methods}
    return frozenset(kinds) if kinds else None


def inlet_acceptance(maxclass: str, index: int) -> Tuple[FrozenSet[str], bool]:
    """``(accept-set, authoritative)`` for ``maxclass``'s inlet ``index``.

    ``authoritative`` means the set is the inlet's *complete* vocabulary, so a
    message outside it is a definite error. The left inlet's vocabulary is taken
    from the ``<methodlist>`` (real data); a signal-only inlet is authoritative
    by its type; everything else is non-authoritative (conservative / skip).
    """
    override = _INLET_ACCEPTS.get(maxclass, {}).get(index)
    if override is not None:
        return override, True
    info = get_object_info(maxclass)
    inlets = info.get("inlets", []) if info else []
    type_set = (
        _accepts_from_type(inlets[index].get("type", ""))
        if 0 <= index < len(inlets)
        else frozenset({ANY})
    )
    if index == 0:
        from_methods = _accepts_from_methods(maxclass)
        if from_methods is not None:
            if ANY in from_methods:
                return frozenset({ANY}), True
            # union with the type-derived set so a signal/float inlet keeps its
            # signal capability even if the method list omits it
            return frozenset(from_methods | type_set), True
    if type_set == frozenset({SIGNAL}):
        return type_set, True  # signal-only inlets are strict
    return type_set, False


def inlet_accepts(maxclass: str, index: int) -> FrozenSet[str]:
    """Message kinds accepted by ``maxclass``'s inlet ``index`` (``{ANY}`` if unsure)."""
    return inlet_acceptance(maxclass, index)[0]


def inlet_rejects_bang(maxclass: str, index: int) -> bool:
    """True if a bang into this signal inlet is a known error (pure DSP objects)."""
    return index in _SIGNAL_INLET_REJECTS_BANG.get(maxclass, set())


def message_compatible(
    emit: str, accepts: FrozenSet[str], authoritative: bool = False
) -> Optional[bool]:
    """Whether an outlet emitting ``emit`` may connect to an inlet accepting ``accepts``.

    Returns ``True`` (fine), ``False`` (definite error), or ``None`` (ambiguous
    -- skip). When ``authoritative`` is set, ``accepts`` is the inlet's complete
    vocabulary, so a message outside it is a definite error (this is how a bang
    into ``cycle~`` is caught while a bang into ``adsr~`` -- which has an
    ``anything`` method -- is allowed). Otherwise the check stays conservative so
    on-by-default validation never rejects a valid patch.
    """
    if ANY in accepts:
        return True  # inlet takes anything
    if emit == ANY:
        return None  # unknown outlet -- cannot judge
    if emit == SIGNAL:
        # a signal needs a signal-capable inlet; a known non-signal inlet errors
        return SIGNAL in accepts
    # control message (bang / int / float / list)
    if emit in accepts:
        return True
    if emit in (INT, FLOAT) and (INT in accepts or FLOAT in accepts):
        return True  # int/float coerce
    if authoritative:
        return False  # full vocabulary known and it excludes this message
    if accepts == frozenset({SIGNAL}):
        return False  # control message into a signal-only inlet
    return None  # ambiguous -- skip


# --------------------------------------------------------------------------
# py2max/core/box.py
# --------------------------------------------------------------------------


# Annotations are postponed so ``Unpack[BoxProps]`` can be written in signatures
# without importing ``typing_extensions`` at runtime -- the library ships zero
# runtime dependencies, and PEP 692 is only a 3.12 runtime feature.


def _scrub(value: Any) -> Any:
    """Recursively drop None-valued keys from any dicts inside `value`.

    Lists are walked but not filtered: a None *element* is positional (an
    `outlettype` slot, say) and dropping it would change the arity. Tuples are
    left alone so `Rect`, a NamedTuple, survives as itself.
    """
    if isinstance(value, Mapping):
        return _scrub_mapping(value)
    if isinstance(value, list):
        return [_scrub(item) for item in value]
    return value


def _scrub_mapping(mapping: Mapping[str, Any]) -> Dict[str, Any]:
    return {k: _scrub(v) for k, v in mapping.items() if v is not None}


class Box(AbstractBox):
    """Represents a Max object in a patch.

    The Box class encapsulates a single Max object with its properties,
    position, and connections. It provides methods for introspection
    and help information.

    Args:
        maxclass: Max object class name (e.g., 'newobj', 'flonum').
        numinlets: Number of input connections.
        numoutlets: Number of output connections.
        id: Unique identifier for the object.
        patching_rect: Position and size rectangle.
        **kwds: Additional Max object properties.

    Attributes:
        id: Unique identifier for the object.
        maxclass: Max object class name.
        numinlets: Number of input connections.
        numoutlets: Number of output connections.
        patching_rect: Position and size as Rect.
    """

    def __init__(
        self,
        maxclass: Optional[str] = None,
        numinlets: Optional[int] = None,
        numoutlets: Optional[int] = None,
        id: Optional[str] = None,
        patching_rect: Optional[Rect] = None,
        **kwds: "Unpack[BoxProps]",
    ) -> None:
        self.id = id
        self.maxclass = maxclass or "newobj"
        # `x if x is not None else default`, not `x or default`: an explicit 0 is
        # meaningful (an object with no outlets cannot be a connection source,
        # and a subpatcher with no `outlet` objects genuinely has none), but it
        # is falsy, so `or` silently promoted it to the default.
        self.numinlets = numinlets if numinlets is not None else 0
        self.numoutlets = numoutlets if numoutlets is not None else 1
        # self.outlettype = outlettype
        self.patching_rect = patching_rect or Rect(0, 0, 62, 22)

        self._kwds = self._remove_none_entries(kwds)
        self._patcher: Optional["Patcher"] = self._kwds.pop("patcher", None)

    def _remove_none_entries(self, kwds: Mapping[str, Any]) -> Dict[str, Any]:
        """Drop keys whose value is None, at any depth.

        Max distinguishes an absent key from a null one, and an unset optional
        argument arrives here as None -- so a key that was never asked for must
        not be written as ``"key": null``.

        Nested dicts are scrubbed too: `saved_attribute_attributes` is built
        with optional members, so a shallow pass left `"parameter_mmax": null`
        one level down where nothing would ever remove it.

        Takes a ``Mapping`` rather than a ``dict`` so a ``BoxProps`` TypedDict
        can be passed straight in; TypedDicts are ``Mapping[str, object]``, not
        ``dict[str, Any]``.
        """
        return _scrub_mapping(kwds)

    def __iter__(self) -> Iterator[Any]:
        yield self
        if self._patcher:
            yield from iter(self._patcher)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id='{self.id}', maxclass='{self.maxclass}')"

    def __pt_repr__(self) -> Any:
        """Custom representation for ptpython REPL.

        Provides rich colored output when displaying objects in the ptpython REPL.
        Shows object type, ID, position, and text content in a readable format.

        prompt_toolkit is not a dependency of py2max core; this hook only fires
        under ptpython (which provides it). Fall back to plain repr otherwise.
        """
        try:
            from prompt_toolkit.formatted_text import HTML  # type: ignore[import-not-found]
        except ImportError:
            return repr(self)

        # Get object details
        obj_type = self.maxclass or "newobj"
        obj_id = self.id or "unknown"
        text = getattr(self, "text", None) or ""

        # Get position
        rect = self.patching_rect
        if rect:
            pos = f"[{rect.x:.0f}, {rect.y:.0f}]"
        else:
            pos = "[?, ?]"

        # Build colored representation
        if text:
            return HTML(
                f"<ansigreen>{obj_type}</ansigreen> "
                f"<ansicyan>{obj_id}</ansicyan> "
                f"at {pos}: <ansiyellow>'{text}'</ansiyellow>"
            )
        else:
            return HTML(
                f"<ansigreen>{obj_type}</ansigreen> "
                f"<ansicyan>{obj_id}</ansicyan> "
                f"at {pos}"
            )

    def render(self) -> None:
        """convert self and children to dictionary."""
        if self._patcher:
            self._sync_subpatcher_ports()
            self._patcher.render()
            self.patcher = self._patcher.to_dict()

    def _sync_subpatcher_ports(self) -> None:
        """Match this box's port counts to the ``inlet``/``outlet`` objects inside.

        A subpatcher box's real port count is however many ``inlet`` / ``outlet``
        objects its nested patcher holds, and those are usually added *after* the
        box itself, so the counts fixed at construction time go stale. Max shows
        a box's declared ports, so a two-outlet subpatcher declaring one outlet
        emits a patch whose second outlet cannot be connected.

        Deliberately conservative: the counts are only overwritten for a
        dimension that actually found objects to count. A nested patcher can hold
        I/O this cannot interpret -- ``gen~`` and ``rnbo~`` declare theirs with
        ``in``/``out`` objects, and an empty subpatcher is a stub the caller has
        yet to fill -- and zeroing those boxes' ports would be worse than leaving
        the constructed default alone.
        """

        n_in, n_out = subpatcher_counts(self)
        if n_in:
            self.numinlets = n_in
        if n_out:
            self.numoutlets = n_out
            self._kwds["outlettype"] = [""] * n_out

    def to_dict(self) -> Dict[str, Any]:
        """create dict from object with extra kwds included"""
        d = vars(self).copy()
        to_del = [k for k in d if k.startswith("_")]
        for k in to_del:
            del d[k]
        d.update(self._kwds)
        return dict(box=d)

    @classmethod
    def from_dict(cls, obj_dict: Dict[str, Any]) -> "Box":
        """create instance from dict"""
        box = cls()
        box.__dict__.update(obj_dict)
        if hasattr(box, "patcher"):
            # Lazy import to avoid circular dependency

            box._patcher = Patcher.from_dict(getattr(box, "patcher"))
        return box

    @property
    def oid(self) -> Optional[int]:
        """Trailing numeric part of the object id, or None if it has none.

        Works for numeric ids (``obj-5`` -> 5) and semantic ids
        (``cycle_1`` -> 1).
        """
        if not self.id:
            return None
        match = re.search(r"\d+$", self.id)
        return int(match.group()) if match else None

    @property
    def subpatcher(self) -> Optional["Patcher"]:
        """synonym for parent patcher object"""
        return self._patcher

    @property
    def text(self) -> Any:
        """Get the text content of the box."""
        # Check if text is stored as a direct attribute (from file loading)
        if "text" in self.__dict__:
            return self.__dict__["text"]
        # Otherwise get from _kwds (from programmatic creation)
        return self._kwds.get("text", "")

    def set_color(
        self,
        bg: Optional["ColorLike"] = None,
        text: Optional["ColorLike"] = None,
        border: Optional["ColorLike"] = None,
    ) -> "Box":
        """Set this box's colors, returning self for chaining.

        Each argument accepts a named color (e.g. ``"red"``), a hex string
        (``"#ff8800"``), or an ``[r, g, b(, a)]`` float sequence (0..1). Sets the
        ``bgcolor`` / ``textcolor`` / ``bordercolor`` attributes respectively.

        Example:
            >>> p.add_textbox("toggle").set_color(bg="blue", text="white")
        """

        if bg is not None:
            self._kwds["bgcolor"] = resolve_color(bg)
        if text is not None:
            self._kwds["textcolor"] = resolve_color(text)
        if border is not None:
            self._kwds["bordercolor"] = resolve_color(border)
        return self

    def add_to_presentation(
        self,
        rect: Any,
        *,
        strict: bool = False,
    ) -> "Box":
        """Mark this box as a presentation-mode UI element (Max for Live).

        Sets ``presentation=1`` and ``presentation_rect`` on the box. Rounds
        fractional coordinates to integers with a warning. Raises if the box
        is M4L infrastructure (``live.remote~``, ``live.map``, etc.) that
        must stay hidden from the device strip.

        Args:
            rect: [x, y, width, height] in device-strip coordinates.
            strict: if True, warn when this isn't a known UI class.
        """

        return add_to_presentation(self, rect, strict=strict)

    def help_text(self) -> str:
        """Get formatted help documentation for this Max object.

        Returns:
            Formatted help string with object documentation from .maxref.xml files.
        """

        return maxref.get_object_help(self.maxclass)

    def help(self) -> None:
        """Print formatted help documentation for this Max object."""
        print(self.help_text())

    def get_info(self) -> Optional[Dict[str, Any]]:
        """Get complete object information from .maxref.xml files.

        Returns:
            Dictionary with complete object information or None if not found.
        """

        return maxref.get_object_info(self.maxclass)

    def get_inlet_count(self) -> Optional[int]:
        """Get the number of inlets for this object from maxref data.

        Returns:
            Number of inlets or None if unknown.
        """

        object_name = self._get_object_name()
        return get_inlet_count(object_name)

    def get_outlet_count(self) -> Optional[int]:
        """Get the number of outlets for this object from maxref data.

        Returns:
            Number of outlets or None if unknown.
        """

        object_name = self._get_object_name()
        return get_outlet_count(object_name)

    def get_inlet_types(self) -> List[str]:
        """Get the inlet types for this object from maxref data

        Returns:
            List of inlet type strings
        """

        object_name = self._get_object_name()
        return get_inlet_types(object_name)

    def get_outlet_types(self) -> List[str]:
        """Get the outlet types for this object from maxref data

        Returns:
            List of outlet type strings
        """

        object_name = self._get_object_name()
        return get_outlet_types(object_name)

    def _get_object_name(self) -> str:
        """Get the actual Max object name for this Box (see utils.object_name)."""

        return object_name(self)


# --------------------------------------------------------------------------
# py2max/core/patchline.py
# --------------------------------------------------------------------------


class Patchline(AbstractPatchline):
    """Represents a connection between two Max objects.

    A Patchline connects an outlet of one object to an inlet of another,
    enabling signal or message flow between objects in a patch.

    Args:
        source: Source connection as [object_id, outlet_index].
        destination: Destination connection as [object_id, inlet_index].
        **kwds: Additional patchline properties.

    Attributes:
        source: Source object ID and outlet index.
        destination: Destination object ID and inlet index.
    """

    def __init__(
        self,
        source: Optional[List[Any]] = None,
        destination: Optional[List[Any]] = None,
        **kwds: Any,
    ) -> None:
        self.source = source or []
        self.destination = destination or []
        self._kwds = kwds

    def __repr__(self) -> str:
        return f"Patchline({self.source} -> {self.destination})"

    @property
    def src(self) -> str:
        """first object from source list"""
        return cast(str, self.source[0])

    @property
    def dst(self) -> str:
        """first object from destination list"""
        return cast(str, self.destination[0])

    def to_tuple(self) -> Tuple[str, str, str, str, Union[str, int]]:
        """Return a tuple describing the patchline."""
        return (
            self.source[0],
            self.source[1],
            self.destination[0],
            self.destination[1],
            self._kwds.get("order", 0),
        )

    def to_dict(self) -> Dict[str, Any]:
        """create dict from object with extra kwds included"""
        d = vars(self).copy()
        to_del = [k for k in d if k.startswith("_")]
        for k in to_del:
            del d[k]
        d.update(self._kwds)
        return dict(patchline=d)

    @classmethod
    def from_dict(cls, obj_dict: Dict[str, Any]) -> "Patchline":
        """convert to`Patchline` object from dict"""
        patchline = cls()
        patchline.__dict__.update(obj_dict)
        return patchline


# --------------------------------------------------------------------------
# py2max/core/serialization.py
# --------------------------------------------------------------------------


logger = get_logger(__name__)


class SerializationMixin(AbstractPatcher):
    """Instance serialization (to dict/json and saving to disk) for Patcher."""

    def to_dict(self) -> Dict[str, Any]:
        """create dict from object with extra kwds included"""
        d = vars(self).copy()
        to_del = [k for k in d if k.startswith("_")]
        for k in to_del:
            del d[k]
        if not self._parent:
            return dict(patcher=d)
        return d

    def to_json(self) -> str:
        """cascade convert to json"""
        self.render()
        return json.dumps(self.to_dict(), indent=4)

    def save_as(self, path: Union[str, Path]) -> None:
        """Save the patch to a specified file path.

        Renders all objects and connections, then saves the patch as a
        .maxpat JSON file (or a binary .amxd) that can be opened in Max/MSP.

        Args:
            path: File path where the patch should be saved.

        Raises:
            PatcherIOError: If file cannot be written or path is invalid.
        """
        logger.debug(f"Saving patcher to: {path}")
        path = Path(path)

        # Resolve to an absolute, normalized path. This is an offline file
        # generator that writes wherever the caller asks; we deliberately do not
        # police the destination (the previous ".."/"/etc" allowlist was trivially
        # bypassable and gave a false sense of safety). We still surface genuinely
        # unresolvable paths as a clear error rather than letting them fail later.
        try:
            resolved_path = path.resolve()
        except (OSError, RuntimeError) as e:
            raise PatcherIOError(
                f"Invalid file path: {path}", file_path=str(path), operation="validate"
            ) from e

        try:
            # Create parent directories if needed
            if resolved_path.parent:
                resolved_path.parent.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created parent directories: {resolved_path.parent}")

            with log_operation(
                logger, "render patcher", boxes=len(self._boxes), lines=len(self._lines)
            ):
                self.render()

            self._lint_on_save()

            # Use resolved path for writing
            if resolved_path.suffix.lower() == ".amxd":
                # Lazy import: m4l is a feature layer, kept off core's import path.

                patcher_dict = self.to_dict()
                ensure_amxd_project_block(patcher_dict, device_type=self._device_type)
                payload = json.dumps(patcher_dict, indent=4)
                resolved_path.write_bytes(
                    pack_amxd(
                        payload,
                        device_type=self._device_type,
                        patcher_filename=resolved_path.stem + ".maxpat",
                    )
                )
            else:
                with open(resolved_path, "w", encoding="utf8") as f:
                    json.dump(self.to_dict(), f, indent=4)

            logger.info(
                f"Saved patcher to: {resolved_path} ({len(self._boxes)} objects, {len(self._lines)} connections)"
            )

        except IOError as e:
            logger.error(f"Failed to write patcher to: {resolved_path}")
            raise PatcherIOError(
                "Failed to write patcher file",
                file_path=str(resolved_path),
                operation="write",
            ) from e

    def _lint_on_save(self) -> None:
        """Lint the top-level patch on save.

        Error-severity findings (bad connections, out-of-range ports, orphaned
        lines, duplicate IDs) are logged. When the patcher was created with
        ``strict=True`` they are raised as ``InvalidPatchError`` instead. Layout
        warnings (overlaps / off-canvas / unknown objects) are left to an
        explicit ``lint()`` call or ``py2max validate`` to keep saves quiet.
        """
        if self._parent:  # only lint the top-level patcher
            return

        errors = [f for f in _lint_patch(self) if f.severity == "error"]
        if not errors:
            return
        for finding in errors:
            logger.warning("lint: %s", finding)
        if getattr(self, "_strict", False):
            raise InvalidPatchError(
                f"patch has {len(errors)} validation error(s); first: {errors[0]}"
            )

    def save(self) -> None:
        """Save the patch to the default file path.

        Uses the path specified during Patcher creation. If no path
        was specified, this method will do nothing. Pending associated
        comments are flushed during ``render`` (called by ``save_as``), so
        every serialization path emits them.
        """
        if self._path:
            self.save_as(self._path)


# --------------------------------------------------------------------------
# py2max/core/factory.py
# --------------------------------------------------------------------------


# Postponed annotations: lets ``Unpack[...]`` appear in signatures without a
# runtime typing_extensions import (PEP 692 is a 3.12 runtime feature).

logger = get_logger(__name__)

# Cache of "name of the first positional parameter", keyed by the *function*
# rather than the bound method so this never keeps a Patcher alive.
_FIRST_PARAM_CACHE: Dict[Any, Optional[str]] = {}


def _first_param_name(method: Callable[..., Any]) -> Optional[str]:
    """Return the name of `method`'s first positional parameter, or None.

    Used by the `add()` dispatcher to detect when a caller keyword names the
    same parameter the dispatcher is about to fill positionally. Derived by
    introspection rather than from a table so that adding a new entry to
    `Patcher._maxclass_methods` cannot silently reintroduce the collision.
    """
    func = getattr(method, "__func__", method)
    if func not in _FIRST_PARAM_CACHE:
        params = list(inspect.signature(func).parameters.values())
        if params and params[0].name == "self":
            params = params[1:]
        name = None
        for param in params:
            if param.kind in (param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD):
                name = param.name
                break
        _FIRST_PARAM_CACHE[func] = name
    return _FIRST_PARAM_CACHE[func]


# Max objects whose inlet/outlet counts are determined by their code rather
# than by a fixed maxref entry. Connection validation for these consults the
# box's own declared numinlets/numoutlets instead of the static maxref data.
DYNAMIC_IO_MAXCLASSES = frozenset({"gen.codebox~", "codebox", "codebox~"})


def _max_gen_io_index(code: str, kind: str) -> int:
    """Highest ``in<N>`` / ``out<N>`` index referenced in gen ``code``.

    gen codeboxes derive their inlet/outlet count from the code: ``in1``,
    ``in2``, ... and ``out1``, ``out2``, .... Returns at least 1 since a gen
    codebox always has one signal inlet and one signal outlet.
    """
    indices = [int(m) for m in re.findall(rf"\b{kind}(\d+)\b", code)]
    return max([1, *indices])


# Box attributes valid on (nearly) every Max object, independent of an object's
# own maxref attribute set. Used by add_box when validate_attrs is enabled to
# whitelist universal/jbox attributes plus the structural keys py2max emits, so
# only genuinely unknown keys (typically typos) are flagged.
UNIVERSAL_BOX_ATTRS = frozenset(
    {
        # structural keys py2max sets on boxes
        "text",
        "maxclass",
        "numinlets",
        "numoutlets",
        "outlettype",
        "id",
        "patching_rect",
        "presentation_rect",
        "presentation",
        "code",
        "data",
        "table_data",
        "editor_rect",
        "embed",
        "hint",
        "minimum",
        "maximum",
        "parameter_enable",
        "saved_attribute_attributes",
        "saved_object_attributes",
        # common universal jbox attributes
        "varname",
        "prototypename",
        "hidden",
        "ignoreclick",
        "bgcolor",
        "bgfillcolor",
        "bordercolor",
        "textcolor",
        "color",
        "elementcolor",
        "accentcolor",
        "fontname",
        "fontsize",
        "fontface",
        "annotation",
        "annotation_name",
        "rounded",
        "border",
        "style",
        "comment",
    }
)


class BoxFactoryMixin(AbstractPatcher):
    """Object creation (boxes, patchlines, and the add_* factory) for Patcher."""

    def _validate_box_attrs(self, box: "Box") -> None:
        """Warn when a box carries keywords that are not known attributes.

        Best-effort lint, enabled by ``Patcher(validate_attrs=True)``. The known
        set is the object's maxref attributes plus ``UNIVERSAL_BOX_ATTRS``;
        objects with no maxref entry are skipped (cannot be checked).
        """
        name = self._get_object_name(box)
        info = maxref.get_object_info(name)
        if not info:
            return
        known = UNIVERSAL_BOX_ATTRS | set(info.get("attributes", {}).keys())
        for key in box._kwds:
            if key not in known:
                warnings.warn(
                    f"Unknown attribute {key!r} for Max object {name!r} "
                    f"(possible typo?)",
                    UserWarning,
                    stacklevel=3,
                )

    def _get_object_name(self, obj: AbstractBox) -> str:
        """Get the actual object name for validation purposes.

        See ``utils.object_name``. Uses the box ``text`` property so it resolves
        correctly for both programmatic and file-loaded boxes.
        """

        return object_name(obj)

    def add_box(
        self,
        box: "Box",
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
    ) -> "Box":
        """registers the box and adds it to the patcher"""

        assert box.id, f"object {box} must have an id"
        if self._validate_attrs:
            self._validate_box_attrs(box)
        self._node_ids.append(box.id)
        self._objects[box.id] = box
        self._boxes.append(box)
        if comment:
            self.add_associated_comment(box, comment, comment_pos)
        return box

    def add_associated_comment(
        self, box: "Box", comment: str, comment_pos: Optional[str] = None
    ) -> None:
        """Store a comment association to be processed later during layout optimization or save.

        This defers the actual comment positioning until after layout optimization,
        ensuring comments stay properly positioned relative to their associated boxes.
        """

        if comment_pos:
            assert comment_pos in [
                "above",
                "below",
                "right",
                "left",
            ], f"comment:{comment} / comment_pos: {comment_pos}"

        # Store the association for deferred processing
        if box.id is None:
            raise AssertionError("associated comment requires box with id")
        self._pending_comments.append((box.id, comment, comment_pos))

    def _process_pending_comments(self) -> None:
        """Process all pending comment associations and position comments relative to their boxes.

        This method is called during layout optimization and save operations to ensure
        comments are positioned correctly after any layout changes.
        """
        for box_id, comment_text, comment_pos in self._pending_comments:
            if box_id not in self._objects:
                continue  # Skip if box was removed

            box = self._objects[box_id]
            rect = box.patching_rect
            x, y, w, h = rect

            # Adjust rect height if needed
            if h != self._layout_mgr.box_height:
                if box.maxclass in maxref.MAXCLASS_DEFAULTS:
                    dh: float = 0.0
                    _, _, _, dh = maxref.MAXCLASS_DEFAULTS[box.maxclass][
                        "patching_rect"
                    ]
                    rect = Rect(x, y, w, dh)
                else:
                    h = self._layout_mgr.box_height
                    rect = Rect(x, y, w, h)

            # Calculate comment position
            if comment_pos:
                patching_rect = getattr(self._layout_mgr, comment_pos)(rect)
            else:
                patching_rect = self._layout_mgr.above(rect)

            # Create the comment with appropriate justification
            if comment_pos == "left":  # special case
                self.add_comment(comment_text, patching_rect, justify="right")
            else:
                self.add_comment(comment_text, patching_rect)

        # Clear pending comments after processing
        self._pending_comments.clear()

    def add_patchline_by_index(
        self, src_id: str, dst_id: str, dst_inlet: int = 0, src_outlet: int = 0
    ) -> "Patchline":
        """Patchline creation between two objects using stored indexes"""

        src = self._objects[src_id]
        dst = self._objects[dst_id]
        assert src.id and dst.id, f"object {src} and {dst} require ids"
        return self.add_patchline(src.id, src_outlet, dst.id, dst_inlet)

    def add_patchline(
        self, src_id: str, src_outlet: int, dst_id: str, dst_inlet: int
    ) -> "Patchline":
        """Primary patchline creation method with validation and logging.

        Args:
            src_id: Source object ID.
            src_outlet: Source outlet index.
            dst_id: Destination object ID.
            dst_inlet: Destination inlet index.

        Returns:
            Created Patchline object.

        Raises:
            InvalidConnectionError: If connection validation fails.
        """
        logger.debug(
            f"Adding patchline: {src_id}[{src_outlet}] -> {dst_id}[{dst_inlet}]"
        )

        # Validate connection if validation is enabled
        if self._validate_connections:
            src_obj = self._objects.get(src_id)
            dst_obj = self._objects.get(dst_id)

            if not src_obj:
                raise InvalidConnectionError(
                    f"Source object not found: {src_id}",
                    src=src_id,
                    dst=dst_id,
                    outlet=src_outlet,
                    inlet=dst_inlet,
                )

            if not dst_obj:
                raise InvalidConnectionError(
                    f"Destination object not found: {dst_id}",
                    src=src_id,
                    dst=dst_id,
                    outlet=src_outlet,
                    inlet=dst_inlet,
                )

            # Get the actual object names for validation
            src_name = self._get_object_name(src_obj)
            dst_name = self._get_object_name(dst_obj)

            src_dynamic = src_obj.maxclass in DYNAMIC_IO_MAXCLASSES
            dst_dynamic = dst_obj.maxclass in DYNAMIC_IO_MAXCLASSES

            if src_dynamic or dst_dynamic:
                # Codeboxes derive their inlet/outlet counts from their code,
                # so bound-check indices against the box's own declared counts
                # rather than the fixed maxref entry. Type checking is skipped
                # because codebox I/O is always signal.
                src_outlets = (
                    src_obj.numoutlets
                    if src_dynamic
                    else maxref.get_outlet_count(src_name)
                )
                dst_inlets = (
                    dst_obj.numinlets
                    if dst_dynamic
                    else maxref.get_inlet_count(dst_name)
                )
                error_msg = ""
                if src_outlets is not None and src_outlet >= src_outlets:
                    error_msg = (
                        f"Object '{src_name}' only has {src_outlets} outlet(s), "
                        f"cannot connect from outlet {src_outlet}"
                    )
                elif dst_inlets is not None and dst_inlet >= dst_inlets:
                    error_msg = (
                        f"Object '{dst_name}' only has {dst_inlets} inlet(s), "
                        f"cannot connect to inlet {dst_inlet}"
                    )
                is_valid = not error_msg
            else:
                is_valid, error_msg = maxref.validate_connection(
                    src_name,
                    src_outlet,
                    dst_name,
                    dst_inlet,
                    src_text=getattr(src_obj, "text", None),
                    dst_text=getattr(dst_obj, "text", None),
                )

            if not is_valid:
                logger.warning(
                    f"Connection validation failed: {src_name}[{src_outlet}] -> {dst_name}[{dst_inlet}]: {error_msg}"
                )
                raise InvalidConnectionError(
                    f"Invalid connection from {src_name}[{src_outlet}] to {dst_name}[{dst_inlet}]: {error_msg}",
                    src=src_id,
                    dst=dst_id,
                    outlet=src_outlet,
                    inlet=dst_inlet,
                )

        # Order of lines between the same pair of objects: Max uses it to fan
        # parallel wires apart. Derive it from the connections that currently
        # exist for this (src, dst) pair rather than a single-slot memo of the
        # last link -- the memo reset ``order`` to 0 whenever any other
        # connection intervened, collapsing parallel wires (and it also could
        # not account for lines restored from a loaded patch).
        order = sum(1 for pl in self._lines if pl.src == src_id and pl.dst == dst_id)
        src, dst = [src_id, src_outlet], [dst_id, dst_inlet]
        patchline = Patchline(source=src, destination=dst, order=order)
        self._lines.append(patchline)
        self._edge_ids.append((src_id, dst_id))

        logger.debug(
            f"Created patchline (order={order}): {src_id}[{src_outlet}] -> {dst_id}[{dst_inlet}]"
        )
        return patchline

    def add_line(
        self, src_obj: "Box", dst_obj: "Box", inlet: int = 0, outlet: int = 0
    ) -> "Patchline":
        """Create a connection between two objects.

        Connects an outlet of the source object to an inlet of the destination
        object. Validates the connection if validation is enabled.

        Args:
            src_obj: Source object to connect from.
            dst_obj: Destination object to connect to.
            inlet: Destination inlet index (default: 0).
            outlet: Source outlet index (default: 0).

        Returns:
            The created Patchline object.

        Raises:
            InvalidConnectionError: If connection validation fails.

        Example:
            >>> osc = p.add_textbox('cycle~ 440')
            >>> gain = p.add_textbox('gain~')
            >>> p.add_line(osc, gain)  # Connect outlet 0 to inlet 0
        """
        assert src_obj.id and dst_obj.id, f"objects {src_obj} and {dst_obj} require ids"
        return self.add_patchline(src_obj.id, outlet, dst_obj.id, inlet)

    # alias for add_line
    link = add_line

    def add_textbox(
        self,
        text: str,
        maxclass: Optional[str] = None,
        numinlets: Optional[int] = None,
        numoutlets: Optional[int] = None,
        outlettype: Optional[List[str]] = None,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        **kwds: "Unpack[TextboxProps]",
    ) -> "Box":
        """Add a text-based Max object to the patch.

        Creates a Max object from a text specification (e.g., 'cycle~ 440').
        Automatically looks up default attributes and applies appropriate
        maxclass based on the object type.

        Args:
            text: Max object specification (e.g., 'cycle~ 440', 'gain~').
            maxclass: Override the automatically determined maxclass.
            numinlets: Number of input connections.
            numoutlets: Number of output connections.
            outlettype: Types of outputs (e.g., ['signal', 'int']).
            patching_rect: Position and size rectangle.
            id: Unique identifier for the object.
            comment: Optional comment text.
            comment_pos: Comment position ('above', 'below', etc.).
            **kwds: Additional Max object properties.

        Returns:
            The created Box object.

        Example:
            >>> osc = p.add_textbox('cycle~ 440')
            >>> gain = p.add_textbox('gain~')
            >>> metro = p.add_textbox('metro 500')
        """
        _maxclass, *tail = text.split()

        defaults = maxref.MAXCLASS_DEFAULTS.get(_maxclass)

        if defaults:
            if maxclass is None and defaults.get("maxclass"):
                maxclass = defaults["maxclass"]

            if numinlets is None and "numinlets" in defaults:
                numinlets = defaults["numinlets"]

            if numoutlets is None and "numoutlets" in defaults:
                numoutlets = defaults["numoutlets"]

            if outlettype is None and "outlettype" in defaults:
                outlettype = defaults["outlettype"]

        kwds = self._textbox_helper(_maxclass, kwds)

        layout_rect = self.get_pos(maxclass) if maxclass else self.get_pos()
        if patching_rect is None and defaults and defaults.get("patching_rect"):
            default_rect = defaults["patching_rect"]
            patching_rect = Rect(
                layout_rect.x, layout_rect.y, default_rect.w, default_rect.h
            )
        elif patching_rect is None:
            patching_rect = layout_rect

        return self.add_box(
            Box(
                id=id or self.get_id(_maxclass),
                text=text,
                maxclass=maxclass or "newobj",
                numinlets=numinlets if numinlets is not None else 1,
                # An object with no maxref entry gets one outlet by default (not
                # zero): a zero-outlet object cannot act as a connection source,
                # which is wrong for the hand-typed long-tail objects that land
                # here. Matches Box.__init__'s default.
                numoutlets=numoutlets if numoutlets is not None else 1,
                outlettype=outlettype if outlettype is not None else [""],
                patching_rect=patching_rect,
                **kwds,
            ),
            comment,
            comment_pos,
        )

    def _textbox_helper(self, maxclass: str, kwds: "TextboxProps") -> "TextboxProps":
        """adds special case support for textbox"""
        if self.classnamespace == "rnbo":
            kwds["rnbo_classname"] = maxclass
            if maxclass in ["codebox", "codebox~"]:
                code = kwds.get("code")
                if code is not None and "rnbo_extra_attributes" not in kwds:
                    if "\r" not in code:
                        code = code.replace("\n", "\r\n")
                        kwds["code"] = code
                    kwds["rnbo_extra_attributes"] = dict(
                        code=code,
                        hot=0,
                    )
        return kwds

    def _dispatch(
        self, method: Callable[..., Any], value: Any, kwds: Dict[str, Any]
    ) -> "Box":
        """Call `method(value, **kwds)`, letting a caller keyword win.

        `add()` derives `method`'s first argument from the value it was handed
        (the text tail, the number). A caller naming that same parameter used
        to be a hard `TypeError` -- "got multiple values for argument" -- so
        the explicit value now takes precedence over the derived one.
        """
        name = _first_param_name(method)
        if name is not None and name in kwds:
            value = kwds.pop(name)
        return cast("Box", method(value, **kwds))

    def _add_param(
        self,
        method: Callable[..., Any],
        value: Union[int, float],
        args: Tuple[Any, ...],
        kwds: Dict[str, Any],
    ) -> "Box":
        """Shared body for `_add_float`/`_add_int`.

        The parameter name may be given positionally or as `name=`; either way
        it is consumed here rather than left in `kwds` to leak into the emitted
        box as a stray `name` property.
        """
        longname: Any = kwds.pop("name", None)
        if args:
            longname = args[0]
        if longname is None:
            longname = ""
        if not isinstance(longname, str):
            kind = "int" if isinstance(value, int) else "float"
            raise ValueError(
                f"should be: .add(<{kind}>, '<name>') OR .add(<{kind}>, name='<name>')"
            )
        # explicit keywords win over the values derived from the call
        return cast(
            "Box",
            method(
                longname=kwds.pop("longname", longname),
                initial=kwds.pop("initial", value),
                **kwds,
            ),
        )

    def _add_float(self, value: float, *args: Any, **kwds: Any) -> "Box":
        """type-handler for float values in `add`"""

        assert isinstance(value, float)
        return self._add_param(self.add_floatparam, value, args, kwds)

    def _add_int(self, value: int, *args: Any, **kwds: Any) -> "Box":
        """type-handler for int values in `add`"""

        assert isinstance(value, int)
        return self._add_param(self.add_intparam, value, args, kwds)

    def _add_str(self, value: str, *args: Any, **kwds: Any) -> "Box":
        """type-handler for str values in `add`"""

        assert isinstance(value, str)

        maxclass, *text = value.split()
        txt = " ".join(text)

        # first check _maxclass_methods
        # these methods don't need the maxclass, just the `text` tail of value
        if maxclass in self._maxclass_methods:
            return self._dispatch(self._maxclass_methods[maxclass], txt, kwds)
        # next two require value as a whole
        if maxclass == "p":
            return self._dispatch(self.add_subpatcher, value, kwds)
        if maxclass == "gen~":
            return self.add_gen_tilde(**kwds)
        if maxclass == "gen.codebox~":
            # Tail is the gen code. value.split() collapses whitespace, so this
            # shortcut suits single-line/`;`-terminated code; for multi-line
            # source pass it to add_gen_codebox() directly.
            return self._dispatch(self.add_gen_codebox, txt, kwds)
        if maxclass == "rnbo~":
            return self._dispatch(self.add_rnbo, value, kwds)
        return self._dispatch(self.add_textbox, value, kwds)

    def add(self, value: Any, *args: Any, **kwds: Any) -> "Box":
        """generic adder: value can be a number or a list or text for an object."""

        if isinstance(value, float):
            return self._add_float(value, *args, **kwds)

        if isinstance(value, int):
            return self._add_int(value, *args, **kwds)

        if isinstance(value, str):
            return self._add_str(value, *args, **kwds)

        raise NotImplementedError

    def add_codebox(
        self,
        code: str,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        tilde: bool = False,
        **kwds: Any,
    ) -> "Box":
        """Add a codebox."""

        _maxclass = "codebox~" if tilde else "codebox"
        if "\r" not in code:
            code = code.replace("\n", "\r\n")

        if self.classnamespace == "rnbo":
            kwds["rnbo_classname"] = _maxclass
            if "rnbo_extra_attributes" not in kwds:
                kwds["rnbo_extra_attributes"] = dict(
                    code=code,
                    hot=0,
                )

        return self.add_box(
            Box(
                id=id or self.get_id(_maxclass),
                code=code,
                maxclass=_maxclass,
                outlettype=[""],
                patching_rect=patching_rect or self.get_pos(),
                **kwds,
            ),
            comment,
            comment_pos,
        )

    def add_codebox_tilde(
        self,
        code: str,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        **kwds: Any,
    ) -> "Box":
        """Add a codebox_tilde"""
        return self.add_codebox(
            code, patching_rect, id, comment, comment_pos, tilde=True, **kwds
        )

    def add_gen_codebox(
        self,
        code: str,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        numinlets: Optional[int] = None,
        numoutlets: Optional[int] = None,
        outlettype: Optional[List[str]] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        **kwds: Any,
    ) -> "Box":
        """Add a standalone ``gen.codebox~`` object.

        Unlike :meth:`add_codebox` (which emits the ``codebox~`` object meant to
        live *inside* a ``gen~`` or ``rnbo~`` subpatcher), this creates the
        self-contained ``gen.codebox~`` object that lives directly in a regular
        Max patcher -- a complete gen patch in a single box, with no subpatcher
        wrapper. This is the form emitted by gen transpilers.

        A gen codebox's inlet/outlet counts are dynamic: they are determined by
        the highest ``inN`` / ``outN`` references in the code. They are derived
        automatically when ``numinlets`` / ``numoutlets`` are not given (each
        defaults to at least 1).
        """
        if "\r" not in code:
            code = code.replace("\n", "\r\n")

        if numinlets is None:
            numinlets = _max_gen_io_index(code, "in")
        if numoutlets is None:
            numoutlets = _max_gen_io_index(code, "out")

        kwds.setdefault("fontname", "<Monospaced>")
        kwds.setdefault("fontsize", 12.0)

        return self.add_box(
            Box(
                id=id or self.get_id("gen.codebox~"),
                code=code,
                maxclass="gen.codebox~",
                numinlets=numinlets,
                numoutlets=numoutlets,
                outlettype=outlettype or ["signal"] * numoutlets,
                patching_rect=patching_rect or self.get_pos(),
                **kwds,
            ),
            comment,
            comment_pos,
        )

    def add_message(
        self,
        text: Optional[str] = None,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        **kwds: "Unpack[TextboxProps]",
    ) -> "Box":
        """Add a max message."""

        return self.add_box(
            Box(
                id=id or self.get_id("message"),
                text=text or "",
                maxclass="message",
                numinlets=2,
                numoutlets=1,
                outlettype=[""],
                patching_rect=patching_rect or self.get_pos(),
                **kwds,
            ),
            comment,
            comment_pos,
        )

    def add_comment(
        self,
        text: str,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        justify: Optional[str] = None,
        **kwds: "Unpack[TextboxProps]",
    ) -> "Box":
        """Add a basic comment object."""
        if justify:
            kwds["textjustification"] = {"left": 0, "center": 1, "right": 2}[justify]
        return self.add_box(
            Box(
                id=id or self.get_id("comment"),
                text=text,
                maxclass="comment",
                patching_rect=patching_rect or self.get_pos(),
                **kwds,
            )
        )

    def add_intbox(
        self,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        **kwds: Any,
    ) -> "Box":
        """Add an int box object."""

        return self.add_box(
            Box(
                id=id or self.get_id("number"),
                maxclass="number",
                numinlets=1,
                numoutlets=2,
                outlettype=["", "bang"],
                patching_rect=patching_rect or self.get_pos(),
                **kwds,
            ),
            comment,
            comment_pos,
        )

    # alias
    add_int = add_intbox

    def add_floatbox(
        self,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        **kwds: Any,
    ) -> "Box":
        """Add an float box object."""

        return self.add_box(
            Box(
                id=id or self.get_id("flonum"),
                maxclass="flonum",
                numinlets=1,
                numoutlets=2,
                outlettype=["", "bang"],
                patching_rect=patching_rect or self.get_pos(),
                **kwds,
            ),
            comment,
            comment_pos,
        )

    # alias
    add_float = add_floatbox

    def add_floatparam(
        self,
        longname: str,
        initial: Optional[float] = None,
        minimum: Optional[float] = None,
        maximum: Optional[float] = None,
        shortname: Optional[str] = None,
        id: Optional[str] = None,
        rect: Optional[Rect] = None,
        hint: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        **kwds: Any,
    ) -> "Box":
        """Add a float parameter object."""

        return self.add_box(
            Box(
                id=id or self.get_id("flonum"),
                maxclass="flonum",
                numinlets=1,
                numoutlets=2,
                outlettype=["", "bang"],
                parameter_enable=1,
                saved_attribute_attributes=dict(
                    valueof=dict(
                        parameter_initial=[initial or 0.5],
                        parameter_initial_enable=1,
                        parameter_longname=longname,
                        # parameter_mmax=maximum,
                        parameter_shortname=shortname or "",
                        parameter_type=0,
                    )
                ),
                patching_rect=rect or self.get_pos(),
                hint=hint or (longname if self._auto_hints else ""),
                # kwds_filter, not `maximum=maximum`: these are Optional here and
                # an unset one must be absent from the patch, not present as null.
                **kwds_filter(kwds, maximum=maximum, minimum=minimum),
            ),
            comment or longname,  # units can also be added here
            comment_pos,
        )

    def add_intparam(
        self,
        longname: str,
        initial: Optional[int] = None,
        minimum: Optional[int] = None,
        maximum: Optional[int] = None,
        shortname: Optional[str] = None,
        id: Optional[str] = None,
        rect: Optional[Rect] = None,
        hint: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        **kwds: Any,
    ) -> "Box":
        """Add an int parameter object."""

        return self.add_box(
            Box(
                id=id or self.get_id("number"),
                maxclass="number",
                numinlets=1,
                numoutlets=2,
                outlettype=["", "bang"],
                parameter_enable=1,
                saved_attribute_attributes=dict(
                    valueof=dict(
                        parameter_initial=[initial or 1],
                        parameter_initial_enable=1,
                        parameter_longname=longname,
                        parameter_mmax=maximum,
                        parameter_shortname=shortname or "",
                        parameter_type=1,
                    )
                ),
                patching_rect=rect or self.get_pos(),
                hint=hint or (longname if self._auto_hints else ""),
                # kwds_filter, not `maximum=maximum`: these are Optional here and
                # an unset one must be absent from the patch, not present as null.
                **kwds_filter(kwds, maximum=maximum, minimum=minimum),
            ),
            comment or longname,  # units can also be added here
            comment_pos,
        )

    # -- Preset / parameter scaffolding --------------------------------------

    def add_pattrstorage(self, name: str = "presets", **kwds: Any) -> "Box":
        """Add a ``pattrstorage`` object for saving and recalling named presets.

        ``pattrstorage`` stores presets of every parameter-enabled and
        pattr-bound object in the patcher. Pair it with :meth:`add_autopattr`
        (or use :meth:`add_preset_system`) so named objects are exposed
        automatically.

        Args:
            name: the storage name (the pattrstorage argument).
            **kwds: extra attributes forwarded to the box.
        """
        return self.add_textbox(
            f"pattrstorage {name}".strip(),
            numinlets=1,
            numoutlets=1,
            outlettype=[""],
            saved_object_attributes=dict(
                client_rect=[0, 0, 0, 0],
                parameter_enable=0,
                parameter_mappable=0,
            ),
            **kwds,
        )

    def add_autopattr(self, **kwds: Any) -> "Box":
        """Add an ``autopattr`` object exposing named objects to the pattr system.

        Any object with a scripting name (``varname``) is bound automatically,
        so it participates in ``pattrstorage`` presets without a per-object
        ``pattr``.
        """
        return self.add_textbox(
            "autopattr",
            numinlets=1,
            numoutlets=4,
            outlettype=["", "", "", ""],
            **kwds,
        )

    def add_preset_system(
        self, name: str = "presets", **kwds: Any
    ) -> Tuple["Box", "Box"]:
        """Add a standard preset system: ``autopattr`` + ``pattrstorage``, wired.

        Connects ``autopattr`` to ``pattrstorage`` so that any object with a
        scripting name (``varname``) or ``parameter_enable=1`` participates in
        presets. Returns ``(autopattr_box, pattrstorage_box)``.
        """
        autopattr = self.add_autopattr()
        storage = self.add_pattrstorage(name, **kwds)
        self.add_line(autopattr, storage)
        return autopattr, storage

    def enable_parameter(
        self,
        box: "Box",
        longname: str,
        shortname: str = "",
        ptype: int = 0,
        initial: Optional[float] = None,
    ) -> "Box":
        """Mark an existing box as a Max parameter.

        Parameterized objects participate in ``pattrstorage`` presets and, in a
        Max for Live device, appear as automatable parameters. Use this to turn
        a plain UI object (toggle, dial, slider, ...) into a parameter without
        rebuilding it.

        Args:
            box: the box to parameterize.
            longname: parameter long name (its preset/automation name).
            shortname: optional short name.
            ptype: parameter type (0=float, 1=int, 2=enum, 3=blob).
            initial: optional initial value.

        Returns:
            The same box, for chaining.
        """
        box._kwds["parameter_enable"] = 1
        valueof: Dict[str, Any] = dict(
            parameter_longname=longname,
            parameter_shortname=shortname,
            parameter_type=ptype,
        )
        if initial is not None:
            valueof["parameter_initial"] = [initial]
            valueof["parameter_initial_enable"] = 1
        box._kwds["saved_attribute_attributes"] = dict(valueof=valueof)
        return box

    def add_attr(
        self,
        name: str,
        value: float,
        shortname: Optional[str] = None,
        id: Optional[str] = None,
        rect: Optional[Rect] = None,
        hint: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        autovar: bool = True,
        show_label: bool = False,
        **kwds: Any,
    ) -> "Box":
        """create a param-linke attrui entry"""
        if autovar:
            kwds["varname"] = name

        return self.add_box(
            Box(
                id=id or self.get_id("attrui"),
                text="attrui",
                maxclass="attrui",
                attr=name,
                parameter_enable=1,
                attr_display=show_label,
                saved_attribute_attributes=dict(
                    valueof=dict(
                        parameter_initial=[name, value],
                        parameter_initial_enable=1,
                        parameter_longname=name,
                        parameter_shortname=shortname or "",
                    )
                ),
                patching_rect=rect or self.get_pos(),
                hint=name if self._auto_hints else hint or "",
                **kwds,
            ),
            comment or name,  # units can also be added here
            comment_pos,
        )

    def add_subpatcher(
        self,
        text: str,
        maxclass: Optional[str] = None,
        numinlets: Optional[int] = None,
        numoutlets: Optional[int] = None,
        outlettype: Optional[List[str]] = None,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        patcher: Optional["Patcher"] = None,
        **kwds: Any,
    ) -> "Box":
        """Add a subpatcher object."""

        # For subpatchers, use the text (e.g., "p subpatch") for semantic ID
        obj_name = text.split()[0] if text else "newobj"
        return self.add_box(
            Box(
                id=id or self.get_id(obj_name),
                text=text,
                maxclass=maxclass or "newobj",
                # Stated explicitly rather than relying on `Box.__init__` to
                # promote a falsy 0 to 1, which is what the old `numoutlets or 0`
                # actually did. A freshly created subpatcher has no `inlet` /
                # `outlet` objects yet, so one of each is the useful starting
                # point; `Box.render` replaces these with the real counts once
                # the nested patcher has ports to count. This path also serves
                # `add_gen`/`add_rnbo`, whose boxes must keep their outlet.
                numinlets=numinlets if numinlets is not None else 1,
                numoutlets=numoutlets if numoutlets is not None else 1,
                outlettype=outlettype or [""],
                patching_rect=patching_rect or self.get_pos(),
                patcher=patcher or Patcher(parent=self),
                **kwds,
            )
        )

    def _drop_line(self, line: AbstractPatchline) -> None:
        """Remove a patchline (and its edge id) from this patcher."""
        if line in self._lines:
            self._lines.remove(line)
        edge = (line.src, line.dst)
        if edge in self._edge_ids:
            self._edge_ids.remove(edge)

    @staticmethod
    def _as_box_id(box: "Union[Box, str]") -> str:
        """Resolve a Box or id string to its id."""
        return box.id if isinstance(box, Box) else box  # type: ignore[return-value]

    def remove_line(self, line: "Patchline") -> None:
        """Remove a specific patchline connection from the patcher."""
        self._drop_line(line)

    def disconnect(
        self,
        src: "Union[Box, str]",
        dst: "Union[Box, str]",
        outlet: int = 0,
        inlet: int = 0,
    ) -> int:
        """Remove connection(s) between ``src`` and ``dst``.

        Removes every patchline from ``src[outlet]`` to ``dst[inlet]`` and
        returns how many were removed (0 if none matched). ``src``/``dst`` may be
        Box objects or their ids.

        Example:
            >>> p.add_line(osc, gain)
            >>> p.disconnect(osc, gain)
            1
        """
        src_id = self._as_box_id(src)
        dst_id = self._as_box_id(dst)
        matches = [
            cast(Patchline, pl)
            for pl in self._lines
            if pl.src == src_id
            and pl.dst == dst_id
            and cast(Patchline, pl).source[1] == outlet
            and cast(Patchline, pl).destination[1] == inlet
        ]
        for line in matches:
            self._drop_line(line)
        return len(matches)

    def remove_box(self, box: "Union[Box, str]") -> Optional["Box"]:
        """Remove a box and every patchline connected to it.

        Accepts a Box or its id. Drops all incident patchlines, the box's entry
        in the object map / node index, and any pending associated comment for
        it. Returns the removed Box, or None if it was not present.

        Example:
            >>> osc = p.add_textbox('cycle~ 440')
            >>> p.remove_box(osc)
        """
        box_id = self._as_box_id(box)

        for line in [pl for pl in self._lines if pl.src == box_id or pl.dst == box_id]:
            self._drop_line(line)

        removed = self._objects.pop(box_id, None)
        target = box if isinstance(box, Box) else removed
        if target in self._boxes:
            self._boxes.remove(target)
        if box_id in self._node_ids:
            self._node_ids.remove(box_id)
        self._pending_comments = [
            pc for pc in self._pending_comments if pc[0] != box_id
        ]
        return cast(Optional["Box"], target)

    # alias for remove_box
    remove = remove_box

    def replace(
        self,
        old: "Union[Box, str]",
        new: "Union[Box, str]",
        **kwds: Any,
    ) -> "Box":
        """Replace a box in place, preserving its position and connections.

        ``old`` (a Box or its id) is swapped for ``new`` -- either the text for a
        replacement object (created with its Max-class defaults) or an
        already-built Box. The replacement takes ``old``'s slot and window
        position, and every patchline incident to ``old`` is rewired to it,
        keeping the same outlet/inlet indices and connection order. Any pending
        associated comment for ``old`` transfers to the replacement. Returns the
        new Box.

        Ports are preserved by index: if the replacement has fewer inlets/outlets
        than the original, wires to the now-missing ports are kept as-is rather
        than silently dropped here (Max drops them on load).

        Example:
            >>> osc = p.add('cycle~ 440')
            >>> p.add_line(osc, gain)
            >>> saw = p.replace(osc, 'saw~ 220')  # saw~ inherits osc's wiring
        """
        old_id = self._as_box_id(old)
        old_box = self._objects.get(old_id)
        if old_box is None:
            raise KeyError(f"cannot replace unknown box {old_id!r}")

        box_idx = self._boxes.index(old_box)
        node_idx = self._node_ids.index(old_id) if old_id in self._node_ids else None
        ox, oy, _, _ = old_box.patching_rect

        # Build the replacement. add_box/add_textbox appends it at the end; it is
        # relocated into old's slot after rewiring. Keep the replacement's own
        # width/height but move it to old's window position.
        if isinstance(new, Box):
            if new.id is None:
                new.id = self.get_id(new.maxclass)
            _, _, nw, nh = new.patching_rect
            new.patching_rect = Rect(ox, oy, nw, nh)
            new_box = self.add_box(new)
        else:
            new_box = self.add_textbox(new, **kwds)
            _, _, nw, nh = new_box.patching_rect
            new_box.patching_rect = Rect(ox, oy, nw, nh)

        new_id = new_box.id
        assert new_id

        # Rewire every incident patchline to the new box, preserving port indices
        # and order, then rebuild the edge index to match.
        for line in self._lines:
            pl = cast(Patchline, line)
            if pl.source and pl.source[0] == old_id:
                pl.source = [new_id, pl.source[1]]
            if pl.destination and pl.destination[0] == old_id:
                pl.destination = [new_id, pl.destination[1]]
        self._edge_ids = [(pl.src, pl.dst) for pl in self._lines]

        # Transfer any pending associated comment from old to new.
        self._pending_comments = [
            (new_id if bid == old_id else bid, text, pos)
            for (bid, text, pos) in self._pending_comments
        ]

        # Drop the old box and move the replacement into its original slot so
        # ordering is preserved (add_* had appended it at the end).
        del self._objects[old_id]
        self._boxes.remove(new_box)  # drop the end-appended copy
        self._boxes[box_idx] = new_box  # overwrite old_box in its slot
        if node_idx is not None:
            self._node_ids.remove(new_id)
            self._node_ids[node_idx] = new_id

        return new_box

    def encapsulate(
        self, boxes: "Iterable[Box]", text: str = "p subpatch", **kwds: Any
    ) -> "Box":
        """Wrap the given boxes into a subpatcher, auto-generating inlet/outlet
        objects for connections that cross the selection boundary.

        - Connections wholly inside the selection move into the subpatcher.
        - Connections crossing in/out are rewired through generated ``inlet`` /
          ``outlet`` objects and the new subpatcher box's ports.
        - Connections wholly outside the selection are left untouched.

        Inlets/outlets are de-duplicated by source port, so multiple wires from
        the same outlet share a single port, matching how patches are usually
        built by hand.

        Args:
            boxes: boxes belonging to this patcher to move into a subpatcher.
            text: the subpatcher box text (e.g. ``"p voice"``).
            **kwds: forwarded to ``add_subpatcher`` (e.g. ``patching_rect``).

        Returns:
            The new subpatcher Box added to this patcher.
        """

        selected = list(boxes)
        id_set = {b.id for b in selected if b.id}
        if not id_set:
            raise ValueError("encapsulate() requires at least one box with an id")

        # Partition existing connections relative to the selection.
        internal: List[Patchline] = []
        incoming: List[Patchline] = []
        outgoing: List[Patchline] = []
        for raw in list(self._lines):
            line = cast(Patchline, raw)
            s_in, d_in = line.src in id_set, line.dst in id_set
            if s_in and d_in:
                internal.append(line)
            elif d_in:
                incoming.append(line)
            elif s_in:
                outgoing.append(line)

        sub = Patcher(parent=self)
        # Avoid id collisions between moved boxes and objects created in the sub.
        moved_oids = [b.oid for b in selected if b.oid is not None]
        if moved_oids:
            sub._id_counter = max(moved_oids)

        # Move the selected boxes into the subpatcher.
        for b in selected:
            if b in self._boxes:
                self._boxes.remove(b)
            if b.id:
                self._objects.pop(b.id, None)
                if b.id in self._node_ids:
                    self._node_ids.remove(b.id)
            child = getattr(b, "_patcher", None)
            if child is not None:
                child._parent = sub
            sub.add_box(b)

        # Move fully-internal connections into the subpatcher.
        for line in internal:
            self._drop_line(line)
            sub._lines.append(line)
            sub._edge_ids.append((line.src, line.dst))

        # Generated connections are correct by construction; skip validation.
        saved = (self._validate_connections, sub._validate_connections)
        self._validate_connections = sub._validate_connections = False
        try:
            # Crossing-in: one inlet per unique external (source_id, outlet).
            inlets: Dict[Tuple[Any, Any], Tuple[int, str]] = {}
            for line in incoming:
                key = (line.source[0], line.source[1])
                if key not in inlets:
                    idx = len(inlets)
                    ibox = sub.add_textbox(
                        "inlet",
                        numinlets=0,
                        numoutlets=1,
                        outlettype=[""],
                        patching_rect=Rect(20.0 + idx * 60, 20.0, 30.0, 30.0),
                    )
                    inlets[key] = (idx, cast(str, ibox.id))
                sub.add_patchline(inlets[key][1], 0, line.dst, int(line.destination[1]))

            # Crossing-out: one outlet per unique internal (source_id, outlet).
            outlets: Dict[Tuple[Any, Any], Tuple[int, str]] = {}
            for line in outgoing:
                key = (line.source[0], line.source[1])
                if key not in outlets:
                    idx = len(outlets)
                    obox = sub.add_textbox(
                        "outlet",
                        numinlets=1,
                        numoutlets=0,
                        outlettype=[],
                        patching_rect=Rect(20.0 + idx * 60, 320.0, 30.0, 30.0),
                    )
                    outlets[key] = (idx, cast(str, obox.id))
                sub.add_patchline(
                    str(line.source[0]), int(line.source[1]), outlets[key][1], 0
                )

            # The crossing lines are now represented inside the sub; drop them.
            for line in incoming + outgoing:
                self._drop_line(line)

            n_in, n_out = len(inlets), len(outlets)
            sub_box = self.add_subpatcher(
                text,
                patcher=sub,
                numinlets=n_in or 1,
                numoutlets=n_out,
                outlettype=[""] * n_out if n_out else None,
                **kwds,
            )
            # add_subpatcher floors inlets at 1; set the exact crossing counts.
            sub_box.numinlets = n_in
            sub_box.numoutlets = n_out
            sub_box_id = cast(str, sub_box.id)

            # Rewire the parent through the new subpatcher box's ports.
            for line in incoming:
                idx = inlets[(line.source[0], line.source[1])][0]
                self.add_patchline(
                    str(line.source[0]), int(line.source[1]), sub_box_id, idx
                )
            for line in outgoing:
                idx = outlets[(line.source[0], line.source[1])][0]
                self.add_patchline(sub_box_id, idx, line.dst, int(line.destination[1]))
        finally:
            self._validate_connections, sub._validate_connections = saved

        return sub_box

    def add_gen(
        self, text: Optional[str] = None, tilde: bool = False, **kwds: Any
    ) -> "Box":
        """Add a gen object."""

        prefix = "gen~" if tilde else "gen"
        _text = f"{prefix} {text}" if text else prefix
        return self.add_subpatcher(
            _text, patcher=Patcher(parent=self, classnamespace="dsp.gen"), **kwds
        )

    def add_gen_tilde(self, text: Optional[str] = None, **kwds: Any) -> "Box":
        """Add a gen~ object."""
        return self.add_gen(text=text, tilde=True, **kwds)

    def add_rnbo(self, text: str = "rnbo~", **kwds: Any) -> "Box":
        """Add an rnbo~ object."""

        if "inletInfo" not in kwds:
            if "numinlets" in kwds:
                inletInfo: Dict[str, List[Any]] = {"IOInfo": []}
                for i in range(kwds["numinlets"]):
                    inletInfo["IOInfo"].append(
                        dict(comment="", index=i + 1, tag=f"in{i + 1}", type="signal")
                    )
                kwds["inletInfo"] = inletInfo
        if "outletInfo" not in kwds:
            if "numoutlets" in kwds:
                outletInfo: Dict[str, List[Any]] = {"IOInfo": []}
                for i in range(kwds["numoutlets"]):
                    outletInfo["IOInfo"].append(
                        dict(comment="", index=i + 1, tag=f"out{i + 1}", type="signal")
                    )
                kwds["outletInfo"] = outletInfo

        return self.add_subpatcher(
            text, patcher=Patcher(parent=self, classnamespace="rnbo"), **kwds
        )

    # -- Multichannel (mc.) / polyphony helpers ------------------------------

    def add_mc(self, text: str, chans: Optional[int] = None, **kwds: Any) -> "Box":
        """Add a multichannel (``mc.``) object.

        Prefixes ``mc.`` to the object name if not already present, and appends
        an ``@chans`` attribute when ``chans`` is given. A single patchline
        between two ``mc.`` objects carries all channels.

        Example:
            >>> p.add_mc("cycle~ 440", chans=4)   # -> "mc.cycle~ 440 @chans 4"
        """
        name = text if text.startswith("mc.") else f"mc.{text}"
        if chans is not None:
            name = f"{name} @chans {chans}"
        return self.add_textbox(name, **kwds)

    def add_poly(self, target: str, voices: int = 1, **kwds: Any) -> "Box":
        """Add a ``poly~`` object hosting ``voices`` instances of ``target``.

        ``target`` is the patch (or subpatcher) name loaded into each voice.

        Example:
            >>> p.add_poly("mysynth", 8)   # -> "poly~ mysynth 8"
        """
        return self.add_textbox(f"poly~ {target} {voices}", **kwds)

    def add_coll(
        self,
        name: Optional[str] = None,
        dictionary: Optional[Dict[Any, Any]] = None,
        embed: int = 1,
        patching_rect: Optional[Rect] = None,
        text: Optional[str] = None,
        id: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        **kwds: Any,
    ) -> "Box":
        """Add a coll object with option to pre-populate from a py dictionary."""
        extra = {"saved_object_attributes": {"embed": embed, "precision": 6}}
        if dictionary:
            extra["coll_data"] = {
                "count": len(dictionary.keys()),
                "data": [{"key": k, "value": v} for k, v in dictionary.items()],  # type: ignore
            }
        kwds.update(extra)
        return self.add_box(
            Box(
                id=id or self.get_id("coll"),
                text=text
                or (f"coll {name} @embed {embed}" if name else f"coll @embed {embed}"),
                maxclass="newobj",
                numinlets=1,
                numoutlets=4,
                outlettype=["", "", "", ""],
                patching_rect=patching_rect or self.get_pos(),
                **kwds,
            ),
            comment,
            comment_pos,
        )

    def add_dict(
        self,
        name: Optional[str] = None,
        dictionary: Optional[Dict[Any, Any]] = None,
        embed: int = 1,
        patching_rect: Optional[Rect] = None,
        text: Optional[str] = None,
        id: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        **kwds: Any,
    ) -> "Box":
        """Add a dict object with option to pre-populate from a py dictionary."""
        extra = {
            "saved_object_attributes": {
                "embed": embed,
                "parameter_enable": kwds.get("parameter_enable", 0),
                "parameter_mappable": kwds.get("parameter_mappable", 0),
            },
            "data": dictionary or {},
        }
        kwds.update(extra)
        return self.add_box(
            Box(
                id=id or self.get_id("dict"),
                text=text
                or (f"dict {name} @embed {embed}" if name else f"dict @embed {embed}"),
                maxclass="newobj",
                numinlets=2,
                numoutlets=4,
                outlettype=["dictionary", "", "", ""],
                patching_rect=patching_rect or self.get_pos(),
                **kwds,
            ),
            comment,
            comment_pos,
        )

    def add_table(
        self,
        name: Optional[str] = None,
        array: Optional[List[Union[int, float]]] = None,
        embed: int = 1,
        patching_rect: Optional[Rect] = None,
        text: Optional[str] = None,
        id: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        tilde: bool = False,
        **kwds: Any,
    ) -> "Box":
        """Add a table object with option to pre-populate from a py list."""

        extra = {
            "embed": embed,
            "saved_object_attributes": {
                "name": name,
                "parameter_enable": kwds.get("parameter_enable", 0),
                "parameter_mappable": kwds.get("parameter_mappable", 0),
                "range": kwds.get("range", 128),
                "showeditor": 0,
                "size": len(array) if array else 128,
            },
            # "showeditor": 0,
            # 'size': kwds.get('size', 128),
            "table_data": array or [],
            "editor_rect": [100.0, 100.0, 300.0, 300.0],
        }
        kwds.update(extra)
        table_type = "table~" if tilde else "table"
        return self.add_box(
            Box(
                id=id or self.get_id(table_type),
                text=text
                or (
                    f"{table_type} {name} @embed {embed}"
                    if name
                    else f"{table_type} @embed {embed}"
                ),
                maxclass="newobj",
                numinlets=2,
                numoutlets=2,
                outlettype=["int", "bang"],
                patching_rect=patching_rect or self.get_pos(),
                **kwds,
            ),
            comment,
            comment_pos,
        )

    def add_table_tilde(
        self,
        name: Optional[str] = None,
        array: Optional[List[Union[int, float]]] = None,
        embed: int = 1,
        patching_rect: Optional[Rect] = None,
        text: Optional[str] = None,
        id: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        **kwds: Any,
    ) -> "Box":
        """Add a table~ object with option to pre-populate from a py list."""

        return self.add_table(
            name,
            array,
            embed,
            patching_rect,
            text,
            id,
            comment,
            comment_pos,
            tilde=True,
            **kwds,
        )

    def add_itable(
        self,
        name: Optional[str] = None,
        array: Optional[List[Union[int, float]]] = None,
        patching_rect: Optional[Rect] = None,
        text: Optional[str] = None,
        id: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        **kwds: Any,
    ) -> "Box":
        """Add a itable object with option to pre-populate from a py list."""

        extra = {
            "range": kwds.get("range", 128),
            "size": len(array) if array else 128,
            "table_data": array or [],
        }
        kwds.update(extra)
        return self.add_box(
            Box(
                id=id or self.get_id("itable"),
                text=text or f"itable {name}",
                maxclass="itable",
                numinlets=2,
                numoutlets=2,
                outlettype=["int", "bang"],
                patching_rect=patching_rect or self.get_pos(),
                **kwds,
            ),
            comment,
            comment_pos,
        )

    def add_umenu(
        self,
        prefix: Optional[str] = None,
        autopopulate: int = 1,
        items: Optional[List[str]] = None,
        patching_rect: Optional[Rect] = None,
        depth: Optional[int] = None,
        id: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        **kwds: Any,
    ) -> "Box":
        """Add a umenu object with option to pre-populate items from a py list."""

        # interleave commas in a list
        def _commas(xs: List[str]) -> List[str]:
            return [i for pair in zip(xs, [","] * len(xs)) for i in pair]

        return self.add_box(
            Box(
                id=id or self.get_id("umenu"),
                maxclass="umenu",
                numinlets=1,
                numoutlets=3,
                outlettype=["int", "", ""],
                autopopulate=autopopulate or 1,
                depth=depth or 1,
                items=_commas(items) if items else [],
                prefix=prefix or "",
                patching_rect=patching_rect or self.get_pos(),
                **kwds,
            ),
            comment,
            comment_pos,
        )

    def add_bpatcher(
        self,
        name: str,
        numinlets: int = 1,
        numoutlets: int = 1,
        outlettype: Optional[List[str]] = None,
        bgmode: int = 0,
        border: int = 0,
        clickthrough: int = 0,
        enablehscroll: int = 0,
        enablevscroll: int = 0,
        lockeddragscroll: int = 0,
        offset: Optional[List[float]] = None,
        viewvisibility: int = 1,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        **kwds: Any,
    ) -> "Box":
        """Add a bpatcher object -- name or patch of bpatcher .maxpat is required."""

        return self.add_box(
            Box(
                id=id or self.get_id("bpatcher"),
                name=name,
                maxclass="bpatcher",
                numinlets=numinlets,
                numoutlets=numoutlets,
                bgmode=bgmode,
                border=border,
                clickthrough=clickthrough,
                enablehscroll=enablehscroll,
                enablevscroll=enablevscroll,
                lockeddragscroll=lockeddragscroll,
                viewvisibility=viewvisibility,
                outlettype=outlettype or ["float", "", ""],
                patching_rect=patching_rect or self.get_pos(),
                offset=offset or [0.0, 0.0],
                **kwds,
            ),
            comment,
            comment_pos,
        )

    def add_beap(self, name: str, **kwds: Any) -> "Box":
        """Add a beap bpatcher object."""

        _varname = name if ".maxpat" not in name else name.removesuffix(".maxpat")
        return self.add_bpatcher(name=name, varname=_varname, extract=1, **kwds)


# --------------------------------------------------------------------------
# py2max/layout/graph.py
# --------------------------------------------------------------------------


class PatchGraph:
    """A directed graph built from a patcher's boxes and patchlines.

    Args:
        lines: the patchlines (each exposing ``.src`` / ``.dst`` ids).
        nodes: optional explicit node ids to include as keys (isolated nodes
            kept). When given, edges are restricted to those whose endpoints are
            both in this set -- matching the ``if src in objects and dst in
            objects`` guard the managers used. When ``None``, the node set is the
            edge endpoints in first-appearance order (the flow-manager
            behaviour, which does not pre-seed disconnected boxes).
    """

    def __init__(
        self,
        lines: Iterable[AbstractPatchline],
        nodes: Optional[Iterable[str]] = None,
    ) -> None:
        edges: List[tuple[str, str]] = [
            (pl.src, pl.dst)
            for pl in lines
            if pl.src is not None and pl.dst is not None
        ]

        if nodes is not None:
            ordered_nodes = list(nodes)
            node_set = set(ordered_nodes)
            edges = [(s, d) for (s, d) in edges if s in node_set and d in node_set]
            self.nodes: List[str] = ordered_nodes
        else:
            seen: Dict[str, None] = {}
            for s, d in edges:
                seen.setdefault(s, None)
                seen.setdefault(d, None)
            self.nodes = list(seen)

        self.edges = edges

    # -- directed views -----------------------------------------------------

    def out_lists(self) -> Dict[str, List[str]]:
        """``{node: [successor, ...]}`` preserving edge order and duplicates."""
        out: Dict[str, List[str]] = {n: [] for n in self.nodes}
        for s, d in self.edges:
            out[s].append(d)
        return out

    def in_lists(self) -> Dict[str, List[str]]:
        """``{node: [predecessor, ...]}`` preserving edge order and duplicates."""
        inc: Dict[str, List[str]] = {n: [] for n in self.nodes}
        for s, d in self.edges:
            inc[d].append(s)
        return inc

    def io_lists(self) -> Dict[str, Dict[str, List[str]]]:
        """``{node: {'inputs': [...], 'outputs': [...]}}`` (flow manager shape)."""
        io: Dict[str, Dict[str, List[str]]] = {
            n: {"inputs": [], "outputs": []} for n in self.nodes
        }
        for s, d in self.edges:
            io[s]["outputs"].append(d)
            io[d]["inputs"].append(s)
        return io

    # -- undirected views ---------------------------------------------------

    def undirected_sets(self) -> Dict[str, Set[str]]:
        """``{node: {neighbour, ...}}`` (both directions, duplicates collapsed)."""
        adj: Dict[str, Set[str]] = {n: set() for n in self.nodes}
        for s, d in self.edges:
            adj[s].add(d)
            adj[d].add(s)
        return adj

    def neighbors_of(self, obj_ids: Iterable[str]) -> Set[str]:
        """All nodes directly connected (either direction) to any of ``obj_ids``."""
        targets = set(obj_ids)
        connected: Set[str] = set()
        for s, d in self.edges:
            if s in targets:
                connected.add(d)
            if d in targets:
                connected.add(s)
        return connected

    # -- traversals ---------------------------------------------------------

    def connected_components(self) -> List[Set[str]]:
        """Undirected connected components, via depth-first search."""
        adj = self.undirected_sets()
        visited: Set[str] = set()
        components: List[Set[str]] = []

        def dfs(start: str, component: Set[str]) -> None:
            stack = [start]
            while stack:
                node = stack.pop()
                if node in visited:
                    continue
                visited.add(node)
                component.add(node)
                for neighbour in adj.get(node, ()):
                    if neighbour not in visited:
                        stack.append(neighbour)

        for node in self.nodes:
            if node not in visited:
                component: Set[str] = set()
                dfs(node, component)
                if component:
                    components.append(component)
        return components

    def topological_order(self) -> List[str]:
        """Post-order DFS from source nodes, giving a signal-flow ordering.

        Sources (no incoming edge within the graph) are visited first; each
        node's successors (sorted for determinism) are emitted before the node
        itself; any nodes unreached by that pass are appended in node order.
        Mirrors the per-column ordering the matrix manager relied on.
        """
        out = {n: set(succ) for n, succ in self.out_lists().items()}
        indegree_targets: Set[str] = set()
        for succ in out.values():
            indegree_targets |= succ

        visited: Set[str] = set()
        result: List[str] = []

        def dfs(node: str) -> None:
            if node in visited:
                return
            visited.add(node)
            for succ in sorted(out.get(node, set())):
                dfs(succ)
            result.append(node)

        sources = [n for n in self.nodes if n not in indegree_targets]
        if not sources:
            sources = list(self.nodes)
        for source in sources:
            dfs(source)

        for node in self.nodes:
            if node not in result:
                result.append(node)
        return result


# --------------------------------------------------------------------------
# py2max/layout/base.py
# --------------------------------------------------------------------------


# Value/UI "param" objects: their role is to set a value on one object's inlet,
# so they read better docked next to that object than spread through the graph.
PARAM_MAXCLASSES = frozenset(
    {"flonum", "number", "message", "toggle", "slider", "dial"}
)


def _is_param(box: object) -> bool:
    """True for a value/UI control that parameterizes another object."""
    mc = getattr(box, "maxclass", "") or ""
    return mc in PARAM_MAXCLASSES or mc.startswith("live.")


class LayoutManager(AbstractLayoutManager):
    """Basic horizontal layout manager.

    Provides simple left-to-right object positioning with wrapping.
    This is a legacy layout manager; consider using GridLayoutManager
    for new projects.

    Args:
        parent: The parent patcher object.
        pad: Padding between objects (default: 48.0).
        box_width: Default object width (default: 66.0).
        box_height: Default object height (default: 22.0).
        comment_pad: Padding for comments (default: 2).
    """

    DEFAULT_PAD = 1.5 * 32.0
    DEFAULT_BOX_WIDTH = 66.0
    DEFAULT_BOX_HEIGHT = 22.0
    DEFAULT_COMMENT_PAD = 2

    def __init__(
        self,
        parent: AbstractPatcher,
        pad: Optional[int] = None,
        box_width: Optional[int] = None,
        box_height: Optional[int] = None,
        comment_pad: Optional[int] = None,
    ):
        self.parent = parent
        self.pad = pad or self.DEFAULT_PAD
        self.box_width = box_width or self.DEFAULT_BOX_WIDTH
        self.box_height = box_height or self.DEFAULT_BOX_HEIGHT
        self.comment_pad = comment_pad or self.DEFAULT_COMMENT_PAD
        self.x_layout_counter = 0
        self.y_layout_counter = 0
        self.prior_rect = None
        self.mclass_rect = None

    def get_rect_from_maxclass(self, maxclass: str) -> Optional[Rect]:
        """Retrieve default rectangle for a Max object class.

        Args:
            maxclass: The Max object class name.

        Returns:
            Default Rect for the object class, or None if not found.
        """
        try:
            return cast(Rect, MAXCLASS_DEFAULTS[maxclass]["patching_rect"])
        except KeyError:
            return None

    def box_dims(self, obj: object) -> tuple[float, float]:
        """Return an object's own (width, height) for repositioning.

        Optimizers place objects on a uniform grid sized by ``box_width`` /
        ``box_height``, but they must not *write back* those defaults as the
        object's size -- doing so squashes every UI object (``dial``, ``scope~``,
        ``function``, ``live.*``, comments) down to text-box dimensions (L2).
        Read the object's existing rect and keep its real w/h, falling back to
        the manager defaults only when it has no usable rect. Works whether the
        rect is a ``Rect`` namedtuple (programmatic) or a plain list (loaded).
        """
        rect = getattr(obj, "patching_rect", None)
        try:
            if rect is not None and len(rect) >= 4:
                w, h = float(rect[2]), float(rect[3])
                if w and h:
                    return w, h
        except (TypeError, ValueError):
            # A malformed patching_rect (e.g. a string from a misused add_*
            # call) must not crash layout; fall back to the manager defaults.
            pass
        return float(self.box_width), float(self.box_height)

    def get_absolute_pos(self, rect: Rect) -> Rect:
        """returns an absolute position for the object"""
        x, y, w, h = rect

        pad = self.pad

        if x > 0.5 * self.parent.width:
            x1 = x - (w + pad)
            x = x1 - (x1 - self.parent.width) if x1 > self.parent.width else x1
        else:
            x1 = x + pad

        y1 = y - (h + pad)
        y = y1 - (y1 - self.parent.height) if y1 > self.parent.height else y1

        return Rect(x, y, w, h)

    def get_relative_pos(self, rect: Rect) -> Rect:
        """returns a relative position for the object"""
        # Default implementation returns the same rect
        return rect

    def get_pos(self, maxclass: Optional[str] = None) -> Rect:
        """Get the next position for object placement.

        Calculates the next position for an object based on the current
        layout state and optional object class defaults.

        Args:
            maxclass: Optional Max object class for size defaults.

        Returns:
            Rect specifying the position and size for the next object.
        """
        x = 0.0
        y = 0.0
        w = self.box_width  # 66.0
        h = self.box_height  # 22.0

        if maxclass:
            mclass_rect = self.get_rect_from_maxclass(maxclass)
            if mclass_rect and (mclass_rect.x or mclass_rect.y):
                if mclass_rect.x:
                    x = float(mclass_rect.x * self.parent.width)
                if mclass_rect.y:
                    y = float(mclass_rect.y * self.parent.height)

                _rect = Rect(x, y, mclass_rect.w, mclass_rect.h)
                return self.get_absolute_pos(_rect)

        _rect = Rect(x, y, w, h)
        return self.get_relative_pos(_rect)

    @property
    def patcher_rect(self) -> Rect:
        """return rect coordinates of the parent patcher"""
        return self.parent.rect

    def above(self, rect: Rect) -> Rect:
        """Return a position of a comment above the object"""
        x, y, w, h = rect
        return Rect(x, y - h, w, h)

    def below(self, rect: Rect) -> Rect:
        """Return a position of a comment below the object"""
        x, y, w, h = rect
        return Rect(x, y + h, w, h)

    def left(self, rect: Rect) -> Rect:
        """Return a position of a comment left of the object"""
        x, y, w, h = rect
        return Rect(x - (w + self.comment_pad), y, w, h)

    def right(self, rect: Rect) -> Rect:
        """Return a position of a comment right of the object"""
        x, y, w, h = rect
        return Rect(x + (w + self.comment_pad), y, w, h)

    def prevent_overlaps(self, min_gap: float = 10.0, max_iterations: int = 50) -> int:
        """Iteratively push overlapping objects apart.

        This method should be called after layout optimization to ensure
        no objects overlap. It uses an iterative approach where overlapping
        objects are pushed apart in the direction of their center offset.

        Args:
            min_gap: Minimum gap between objects in pixels.
            max_iterations: Maximum number of iterations to prevent infinite loops.

        Returns:
            Number of iterations performed (0 if no overlaps found).
        """
        objects = [
            o for o in self.parent._objects.values() if hasattr(o, "patching_rect")
        ]
        if len(objects) < 2:
            return 0

        def overlapping(a: Rect, b: Rect) -> bool:
            return (
                a.x < b.x + b.w + min_gap
                and b.x < a.x + a.w + min_gap
                and a.y < b.y + b.h + min_gap
                and b.y < a.y + a.h + min_gap
            )

        iterations_performed = 0
        for iteration in range(max_iterations):
            # Sweep in reading order and push each object clear of any *earlier*
            # one it overlaps, along the axis of least penetration. Objects only
            # move away from earlier ones (never back into them), so the total
            # displacement is monotone and the sweep converges. A symmetric
            # pairwise push instead oscillates on dense clusters and never
            # settles. Real layout-manager output is already overlap-free, so
            # this is a safety net rather than the primary placement.
            objects.sort(key=lambda o: (o.patching_rect.y, o.patching_rect.x))
            moved = False
            for i in range(1, len(objects)):
                ri = objects[i].patching_rect
                original = ri
                for j in range(i):
                    rj = objects[j].patching_rect
                    if not overlapping(ri, rj):
                        continue
                    pen_x = min(ri.x + ri.w, rj.x + rj.w) - max(ri.x, rj.x) + min_gap
                    pen_y = min(ri.y + ri.h, rj.y + rj.h) - max(ri.y, rj.y) + min_gap
                    if pen_x <= pen_y:
                        if ri.x + ri.w / 2 >= rj.x + rj.w / 2:
                            nx = rj.x + rj.w + min_gap
                        else:
                            nx = max(self.pad, rj.x - ri.w - min_gap)
                        ri = Rect(nx, ri.y, ri.w, ri.h)
                    else:
                        if ri.y + ri.h / 2 >= rj.y + rj.h / 2:
                            ny = rj.y + rj.h + min_gap
                        else:
                            ny = max(self.pad, rj.y - ri.h - min_gap)
                        ri = Rect(ri.x, ny, ri.w, ri.h)
                if ri != original:
                    objects[i].patching_rect = ri
                    moved = True
            iterations_performed = iteration + 1
            if not moved:
                break

        return iterations_performed

    def place_params(self, direction: Optional[str] = None, gap: float = 8.0) -> None:
        """Dock value/UI 'param' objects next to the single object they drive.

        A param (number box, toggle, slider, dial, message, ``live.*``) whose
        outgoing connections all go to one non-param target is repositioned
        adjacent to that target, perpendicular to the signal flow -- above the
        target for a horizontal flow, to its left for a vertical flow -- and
        aligned to the inlet it feeds. This keeps value controls with their
        object instead of spread through the signal graph.

        Runs after the main layout as the final placement pass. ``direction``
        defaults to the manager's ``flow_direction``.
        """
        objects = self.parent._objects

        # outgoing edges per source: source_id -> [(inlet, target_id), ...]
        out_edges: Dict[str, List[Tuple[int, str]]] = {}
        for line in self.parent._lines:
            source = getattr(line, "source", None)
            destination = getattr(line, "destination", None)
            if not source or not destination:
                continue
            inlet = int(destination[1]) if len(destination) > 1 else 0
            out_edges.setdefault(source[0], []).append((inlet, destination[0]))

        # a param drives exactly one non-param target -> group by that target
        by_target: Dict[str, List[Tuple[int, Any]]] = {}
        for src_id, edges in out_edges.items():
            box = objects.get(src_id)
            if box is None or not _is_param(box):
                continue
            targets = {t for _, t in edges}
            if len(targets) != 1:
                continue
            target_id = next(iter(targets))
            target = objects.get(target_id)
            if target is None or _is_param(target):
                continue
            inlet = min(i for i, _ in edges)
            by_target.setdefault(target_id, []).append((inlet, box))

        if not by_target:
            return

        direction = direction or getattr(self, "flow_direction", "horizontal")
        left_side = direction in ("vertical", "column")
        for target_id, params in by_target.items():
            params.sort(key=lambda p: p[0])
            self._dock_params(objects[target_id], params, left_side, gap)

        self.prevent_overlaps()

    def _dock_params(
        self,
        target: Any,
        params: List[Tuple[int, Any]],
        left_side: bool,
        gap: float,
    ) -> None:
        """Position a target's param satellites (params sorted by inlet).

        Docks on the perpendicular side that has room: left of the target when a
        vertical flow leaves space, otherwise right; above for a horizontal flow,
        otherwise below. This keeps params clear of a flow that hugs an edge.
        """
        tr = target.patching_rect
        tx, ty, tw, th = float(tr[0]), float(tr[1]), float(tr[2]), float(tr[3])
        n_inlets = int(getattr(target, "numinlets", 1) or 1)

        if left_side:
            max_w = max(float(b.patching_rect[2]) for _, b in params)
            x = tx - max_w - gap
            if x < self.pad:  # no room on the left -> dock on the right
                x = tx + tw + gap
            y = ty
            for _, box in params:
                bw, bh = float(box.patching_rect[2]), float(box.patching_rect[3])
                box.patching_rect = Rect(x, y, bw, bh)
                y += bh + gap
            return

        max_h = max(float(b.patching_rect[3]) for _, b in params)
        y = ty - max_h - gap
        if y < self.pad:  # no room above -> dock below
            y = ty + th + gap
        if len(params) == 1:
            inlet, box = params[0]
            bw = float(box.patching_rect[2])
            cx = self._inlet_center_x(tx, tw, n_inlets, inlet)
            box.patching_rect = Rect(
                max(self.pad, cx - bw / 2), y, bw, box.patching_rect[3]
            )
        else:
            # pack params as a centered row, in inlet order
            widths = [float(b.patching_rect[2]) for _, b in params]
            row_w = sum(widths) + gap * (len(params) - 1)
            x = max(self.pad, tx + tw / 2 - row_w / 2)
            for (_, box), bw in zip(params, widths):
                box.patching_rect = Rect(x, y, bw, float(box.patching_rect[3]))
                x += bw + gap

    @staticmethod
    def _inlet_center_x(tx: float, tw: float, n_inlets: int, inlet: int) -> float:
        """Approximate x of the center of ``inlet`` on a box (Max spreads inlets
        edge-to-edge across the top)."""
        if n_inlets <= 1:
            return tx + tw / 2
        return tx + tw * min(inlet, n_inlets - 1) / (n_inlets - 1)

    def optimize_layout(self) -> None:
        """Arrange every object in the patch (batch, whole-patch layout).

        This is py2max's batch layout entry point: it always performs a full
        layout of the entire patch. Subclasses implement their algorithm in
        ``_full_layout()``.

        Interactive, per-edit ("incremental") relayout is intentionally out of
        scope for py2max; it belongs to the editor/server that owns the live
        editing session. See ``docs/auto-layout.md`` in py2max-server.
        """
        self._full_layout()

    def _full_layout(self) -> None:
        """Perform full layout optimization.

        Subclasses should override this method to implement their
        full layout algorithm.
        """
        pass


# --------------------------------------------------------------------------
# py2max/layout/grid.py
# --------------------------------------------------------------------------


class GridLayoutManager(LayoutManager):
    """Utility class to help with object layout in a grid pattern.

    This layout manager supports both horizontal and vertical grid layouts:
    - Horizontal: objects fill from left to right and wrap to next row
    - Vertical: objects fill from top to bottom and wrap to next column
    """

    def __init__(
        self,
        parent: AbstractPatcher,
        pad: Optional[int] = None,
        box_width: Optional[int] = None,
        box_height: Optional[int] = None,
        comment_pad: Optional[int] = None,
        flow_direction: str = "horizontal",
        cluster_connected: bool = False,
    ):
        super().__init__(parent, pad, box_width, box_height, comment_pad)
        self.flow_direction = flow_direction  # "horizontal" or "vertical"
        self.cluster_connected = (
            cluster_connected  # Whether to cluster connected objects
        )

    def get_relative_pos(self, rect: Rect) -> Rect:
        """Returns a relative position for the object based on flow direction."""
        # Always use simple grid positioning during object creation
        # Clustering will be applied later via optimize_layout()
        if self.flow_direction == "vertical":
            return self._get_vertical_position(rect)
        else:
            return self._get_horizontal_position(rect)

    def _get_horizontal_position(self, rect: Rect) -> Rect:
        """Returns a relative horizontal position for the object.
        Objects fill from left to right and wrap horizontally.
        """
        x, y, w, h = rect
        pad = self.pad

        x_shift = 3 * pad * self.x_layout_counter
        y_shift = 1.5 * pad * self.y_layout_counter
        x = pad + x_shift

        self.x_layout_counter += 1
        if x + w + 2 * pad > self.parent.width:
            self.x_layout_counter = 0
            self.y_layout_counter += 1

        y = pad + y_shift
        return Rect(x, y, w, h)

    def _get_vertical_position(self, rect: Rect) -> Rect:
        """Returns a relative vertical position for the object.
        Objects fill from top to bottom and wrap vertically.
        """
        x, y, w, h = rect
        pad = self.pad

        x_shift = 3 * pad * self.x_layout_counter
        y_shift = 1.5 * pad * self.y_layout_counter
        y = pad + y_shift

        self.y_layout_counter += 1
        if y + h + 2 * pad > self.parent.height:
            self.x_layout_counter += 1
            self.y_layout_counter = 0

        x = pad + x_shift
        return Rect(x, y, w, h)

    def _full_layout(self) -> None:
        """Perform full layout optimization."""
        if not self.cluster_connected or len(self.parent._objects) < 2:
            # Even without clustering, prevent overlaps
            self.prevent_overlaps()
            return

        # Analyze connections and create clusters of connected objects.
        clusters = PatchGraph(
            self.parent._lines, nodes=self.parent._objects
        ).connected_components()

        # Even single clusters can benefit from reorganization
        # Apply optimized positions to existing objects based on clusters
        self._apply_clustered_layout(clusters)

        # Prevent any remaining overlaps after clustering
        self.prevent_overlaps()

    def _apply_clustered_layout(self, clusters: List[Set[str]]) -> None:
        """Apply cluster-based positioning to all objects."""
        # pad = self.pad

        # If there's only one large cluster, try to create sub-clusters based on object types
        if len(clusters) == 1 and len(clusters[0]) > 6:
            clusters = self._subdivide_large_cluster(clusters[0])

        # Sort clusters by size (largest first) for better space utilization
        clusters = sorted(clusters, key=len, reverse=True)

        # Use flow_direction to determine cluster arrangement
        if self.flow_direction == "vertical":
            self._apply_vertical_clustered_layout(clusters)
        else:
            self._apply_horizontal_clustered_layout(clusters)

    def _apply_horizontal_clustered_layout(self, clusters: List[Set[str]]) -> None:
        """Apply horizontal cluster-based positioning (clusters arranged left-to-right)."""
        pad = self.pad
        num_clusters = len(clusters)

        # Calculate cluster layout for horizontal arrangement
        if num_clusters <= 2:
            cluster_cols = num_clusters
            cluster_rows = 1
        elif num_clusters <= 4:
            cluster_cols = 2
            cluster_rows = 2
        else:
            cluster_cols = min(3, num_clusters)
            cluster_rows = (num_clusters + cluster_cols - 1) // cluster_cols

        # Use float division for consistent spacing
        cluster_width = (self.parent.width - 2 * pad) / max(cluster_cols, 1)
        cluster_height = (self.parent.height - 2 * pad) / max(cluster_rows, 1)

        # Consistent spacing between objects (use float)
        object_spacing = pad * 0.5

        # Position each cluster in its designated area
        for cluster_idx, cluster_objects in enumerate(clusters):
            cluster_objects_list = sorted(list(cluster_objects))  # Consistent ordering

            # Calculate cluster's base position
            cluster_col = cluster_idx % cluster_cols
            cluster_row = cluster_idx // cluster_cols

            cluster_x_base = cluster_col * cluster_width + pad
            cluster_y_base = cluster_row * cluster_height + pad

            # Position objects within this cluster's designated area (horizontal priority)
            objects_per_row = max(
                1, int(cluster_width / (self.box_width + object_spacing))
            )

            for obj_idx, obj_id in enumerate(cluster_objects_list):
                if obj_id in self.parent._objects:
                    obj = self.parent._objects[obj_id]
                    if hasattr(obj, "patching_rect"):
                        # Calculate position within cluster (horizontal flow)
                        obj_col = obj_idx % objects_per_row
                        obj_row = obj_idx // objects_per_row

                        x = cluster_x_base + obj_col * (self.box_width + object_spacing)
                        y = cluster_y_base + obj_row * (
                            self.box_height + object_spacing
                        )

                        # Ensure bounds (stay within cluster area)
                        x = min(
                            max(x, cluster_x_base),
                            cluster_x_base + cluster_width - self.box_width - pad,
                        )
                        y = min(
                            max(y, cluster_y_base),
                            cluster_y_base + cluster_height - self.box_height - pad,
                        )

                        # Ensure overall patcher bounds
                        x = min(max(x, pad), self.parent.width - self.box_width - pad)
                        y = min(max(y, pad), self.parent.height - self.box_height - pad)

                        w, h = self.box_dims(obj)
                        obj.patching_rect = Rect(x, y, w, h)

    def _apply_vertical_clustered_layout(self, clusters: List[Set[str]]) -> None:
        """Apply vertical cluster-based positioning (clusters arranged top-to-bottom)."""
        pad = self.pad
        num_clusters = len(clusters)

        # Calculate cluster layout for vertical arrangement (prefer vertical stacking)
        if num_clusters <= 2:
            cluster_cols = 1
            cluster_rows = num_clusters
        elif num_clusters <= 4:
            cluster_cols = 2
            cluster_rows = 2
        else:
            cluster_rows = min(3, num_clusters)
            cluster_cols = (num_clusters + cluster_rows - 1) // cluster_rows

        # Use float division for consistent spacing
        cluster_width = (self.parent.width - 2 * pad) / max(cluster_cols, 1)
        cluster_height = (self.parent.height - 2 * pad) / max(cluster_rows, 1)

        # Consistent spacing between objects (use float)
        object_spacing = pad * 0.5

        # Position each cluster in its designated area
        for cluster_idx, cluster_objects in enumerate(clusters):
            cluster_objects_list = sorted(list(cluster_objects))  # Consistent ordering

            # Calculate cluster's base position (fill vertically first)
            cluster_row = cluster_idx % cluster_rows
            cluster_col = cluster_idx // cluster_rows

            cluster_x_base = cluster_col * cluster_width + pad
            cluster_y_base = cluster_row * cluster_height + pad

            # Position objects within this cluster's designated area (vertical priority)
            objects_per_col = max(
                1, int(cluster_height / (self.box_height + object_spacing))
            )

            for obj_idx, obj_id in enumerate(cluster_objects_list):
                if obj_id in self.parent._objects:
                    obj = self.parent._objects[obj_id]
                    if hasattr(obj, "patching_rect"):
                        # Calculate position within cluster (vertical flow)
                        obj_row = obj_idx % objects_per_col
                        obj_col = obj_idx // objects_per_col

                        x = cluster_x_base + obj_col * (self.box_width + object_spacing)
                        y = cluster_y_base + obj_row * (
                            self.box_height + object_spacing
                        )

                        # Ensure bounds (stay within cluster area)
                        x = min(
                            max(x, cluster_x_base),
                            cluster_x_base + cluster_width - self.box_width - pad,
                        )
                        y = min(
                            max(y, cluster_y_base),
                            cluster_y_base + cluster_height - self.box_height - pad,
                        )

                        # Ensure overall patcher bounds
                        x = min(max(x, pad), self.parent.width - self.box_width - pad)
                        y = min(max(y, pad), self.parent.height - self.box_height - pad)

                        w, h = self.box_dims(obj)
                        obj.patching_rect = Rect(x, y, w, h)

    def _subdivide_large_cluster(self, cluster: Set[str]) -> List[Set[str]]:
        """Subdivide a large cluster into smaller logical groups based on object types."""
        # Group objects by type
        type_groups: Dict[str, Set[str]] = {}

        for obj_id in cluster:
            obj = self.parent._objects.get(obj_id)
            if obj:
                # Group by maxclass
                obj_type = obj.maxclass
                if obj_type not in type_groups:
                    type_groups[obj_type] = set()
                type_groups[obj_type].add(obj_id)

        # Convert type groups to clusters, combining small ones
        subclusters = []
        small_cluster = set()

        for obj_type, obj_set in type_groups.items():
            if len(obj_set) >= 3:  # Large enough to be its own cluster
                subclusters.append(obj_set)
            else:  # Too small, add to combined cluster
                small_cluster.update(obj_set)

        # Add the small objects cluster if it exists
        if small_cluster:
            subclusters.append(small_cluster)

        # If we didn't create meaningful subdivisions, return original cluster
        return subclusters if len(subclusters) > 1 else [cluster]


# Legacy aliases for backward compatibility
class HorizontalLayoutManager(GridLayoutManager):
    """Legacy horizontal layout manager. Use GridLayoutManager with flow_direction="horizontal" instead."""

    def __init__(
        self,
        parent: AbstractPatcher,
        pad: Optional[int] = None,
        box_width: Optional[int] = None,
        box_height: Optional[int] = None,
        comment_pad: Optional[int] = None,
    ):
        super().__init__(
            parent, pad, box_width, box_height, comment_pad, flow_direction="horizontal"
        )


class VerticalLayoutManager(GridLayoutManager):
    """Legacy vertical layout manager. Use GridLayoutManager with flow_direction="vertical" instead."""

    def __init__(
        self,
        parent: AbstractPatcher,
        pad: Optional[int] = None,
        box_width: Optional[int] = None,
        box_height: Optional[int] = None,
        comment_pad: Optional[int] = None,
    ):
        super().__init__(
            parent, pad, box_width, box_height, comment_pad, flow_direction="vertical"
        )


# --------------------------------------------------------------------------
# py2max/layout/flow.py
# --------------------------------------------------------------------------


class FlowLayoutManager(LayoutManager):
    """Advanced layout manager that analyzes signal flow topology.

    This layout manager:
    - Analyzes patchline connections to understand signal flow
    - Groups related objects based on connection patterns
    - Uses hierarchical positioning with signal flow left-to-right or top-to-bottom
    - Minimizes line crossings and connection distances
    - Balances layout aesthetically while respecting functional relationships
    """

    def __init__(
        self,
        parent: AbstractPatcher,
        pad: Optional[int] = None,
        box_width: Optional[int] = None,
        box_height: Optional[int] = None,
        comment_pad: Optional[int] = None,
        flow_direction: str = "horizontal",
    ):
        super().__init__(parent, pad, box_width, box_height, comment_pad)
        self._object_positions: Dict[str, Rect] = {}  # Cache for calculated positions
        self._flow_levels: Dict[str, int] = {}  # Track hierarchical flow levels
        self._position_cache: Dict[
            str, Rect
        ] = {}  # Cache positions to avoid recalculation
        self.flow_direction = flow_direction  # "horizontal" or "vertical"

    def _analyze_connections(self) -> Dict[str, Dict[str, List[str]]]:
        """Analyze patchline connections to build a flow graph.

        Keys are the connected objects only (disconnected boxes are not seeded),
        in first-appearance order, matching the historical behaviour.
        """
        return PatchGraph(self.parent._lines).io_lists()

    def _calculate_flow_levels(
        self, connections: Dict[str, Dict[str, List[str]]]
    ) -> Dict[str, int]:
        """Calculate hierarchical flow levels for objects based on signal chain depth."""
        levels: Dict[str, int] = {}
        visited: Set[str] = set()

        # Find source objects (no inputs)
        sources = [obj_id for obj_id, conn in connections.items() if not conn["inputs"]]

        if not sources:
            # If no clear sources, find objects with minimal inputs
            min_inputs = (
                min(len(conn["inputs"]) for conn in connections.values())
                if connections
                else 0
            )
            sources = [
                obj_id
                for obj_id, conn in connections.items()
                if len(conn["inputs"]) == min_inputs
            ]

        # Assign levels using BFS-like traversal
        current_level = 0
        current_objects = sources

        while current_objects:
            next_objects = []
            for obj_id in current_objects:
                if obj_id not in visited:
                    levels[obj_id] = current_level
                    visited.add(obj_id)

                    # Add outputs to next level
                    if obj_id in connections:
                        for output_id in connections[obj_id]["outputs"]:
                            if output_id not in visited:
                                next_objects.append(output_id)

            current_objects = list(set(next_objects))
            current_level += 1

        # Handle disconnected objects
        for obj_id in self.parent._objects:
            if obj_id not in levels:
                levels[obj_id] = current_level

        return levels

    def _group_by_level(self, levels: Dict[str, int]) -> Dict[int, List[str]]:
        """Group objects by their flow level."""
        groups: Dict[int, List[str]] = {}
        for obj_id, level in levels.items():
            if level not in groups:
                groups[level] = []
            groups[level].append(obj_id)
        return groups

    def _minimize_crossings(
        self,
        groups: Dict[int, List[str]],
        connections: Dict[str, Dict[str, List[str]]],
    ) -> Dict[int, List[str]]:
        """Minimize line crossings using the barycenter heuristic.

        For each level (after the first), objects are reordered based on
        the average position (barycenter) of their connected objects in
        the previous level. This tends to place connected objects near
        each other, reducing line crossings.

        Args:
            groups: Objects grouped by level
            connections: Connection graph from _analyze_connections()

        Returns:
            Reordered groups with minimized crossings
        """
        if len(groups) < 2:
            return groups

        sorted_levels = sorted(groups.keys())
        result: Dict[int, List[str]] = {}

        # First level stays as-is (sorted for consistency)
        first_level = sorted_levels[0]
        result[first_level] = sorted(groups[first_level])

        # Process subsequent levels
        for i, level in enumerate(sorted_levels[1:], 1):
            prev_level = sorted_levels[i - 1]
            prev_objects = result[prev_level]
            current_objects = groups[level]

            # Create position map for previous level objects
            prev_positions = {obj_id: idx for idx, obj_id in enumerate(prev_objects)}

            # Calculate barycenter for each object in current level
            barycenters: Dict[str, float] = {}
            for obj_id in current_objects:
                # Find all connections to previous level
                connected_positions = []

                # Check inputs (connections from previous level)
                if obj_id in connections:
                    for input_id in connections[obj_id]["inputs"]:
                        if input_id in prev_positions:
                            connected_positions.append(prev_positions[input_id])

                if connected_positions:
                    # Barycenter is the average position of connected objects
                    barycenters[obj_id] = sum(connected_positions) / len(
                        connected_positions
                    )
                else:
                    # No connections to previous level - use a large value to push to end
                    barycenters[obj_id] = float("inf")

            # Sort objects by their barycenter values
            sorted_objects = sorted(
                current_objects,
                key=lambda obj_id: (
                    barycenters[obj_id],
                    obj_id,
                ),  # obj_id as tiebreaker
            )
            result[level] = sorted_objects

        return result

    def _calculate_positions(self) -> Dict[str, Rect]:
        """Calculate optimized positions for all objects."""
        connections = self._analyze_connections()
        levels = self._calculate_flow_levels(connections)
        groups = self._group_by_level(levels)

        # Apply crossing minimization to reorder objects within each level
        groups = self._minimize_crossings(groups, connections)

        pad = self.pad

        if self.flow_direction == "vertical":
            return self._calculate_vertical_positions(groups, pad)
        else:
            return self._calculate_horizontal_positions(groups, pad)

    def _calculate_horizontal_positions(
        self, groups: Dict[int, List[str]], pad: float
    ) -> Dict[str, Rect]:
        """Calculate positions for horizontal (left-to-right) flow."""
        positions: Dict[str, Rect] = {}
        num_levels = max(len(groups), 1)

        # Calculate available width per level
        available_width = self.parent.width - 2 * pad
        level_width = available_width / num_levels if groups else self.parent.width

        for level, obj_ids in groups.items():
            # Calculate x position based on level (left-to-right flow)
            x_base = pad + (level * level_width * 0.8)  # 0.8 factor for better spacing

            # Calculate y positions for objects in this level
            num_objects = len(obj_ids)
            level_height = num_objects * (self.box_height + pad)

            # Ensure y_start doesn't go negative - clamp to pad minimum
            available_height = self.parent.height - 2 * pad
            if level_height > available_height:
                # Scale down spacing if too many objects
                spacing = available_height / max(num_objects, 1)
                y_start = pad
            else:
                spacing = self.box_height + pad
                y_start = max(pad, (self.parent.height - level_height) / 2)

            for i, obj_id in enumerate(obj_ids):
                x = x_base
                y = y_start + i * spacing

                # Ensure positions stay within bounds
                x = max(pad, min(x, self.parent.width - self.box_width - pad))
                y = max(pad, min(y, self.parent.height - self.box_height - pad))

                positions[obj_id] = Rect(x, y, self.box_width, self.box_height)

        return positions

    def _calculate_vertical_positions(
        self, groups: Dict[int, List[str]], pad: float
    ) -> Dict[str, Rect]:
        """Calculate positions for vertical (top-to-bottom) flow."""
        positions: Dict[str, Rect] = {}
        num_levels = max(len(groups), 1)

        # Calculate available height per level
        available_height = self.parent.height - 2 * pad
        level_height = available_height / num_levels if groups else self.parent.height

        for level, obj_ids in groups.items():
            # Calculate y position based on level (top-to-bottom flow)
            y_base = pad + (level * level_height * 0.8)  # 0.8 factor for better spacing

            # Calculate x positions for objects in this level
            num_objects = len(obj_ids)
            level_width = num_objects * (self.box_width + pad)

            # Ensure x_start doesn't go negative - clamp to pad minimum
            available_width = self.parent.width - 2 * pad
            if level_width > available_width:
                # Scale down spacing if too many objects
                spacing = available_width / max(num_objects, 1)
                x_start = pad
            else:
                spacing = self.box_width + pad
                x_start = max(pad, (self.parent.width - level_width) / 2)

            for i, obj_id in enumerate(obj_ids):
                y = y_base
                x = x_start + i * spacing

                # Ensure positions stay within bounds
                x = max(pad, min(x, self.parent.width - self.box_width - pad))
                y = max(pad, min(y, self.parent.height - self.box_height - pad))

                positions[obj_id] = Rect(x, y, self.box_width, self.box_height)

        return positions

    def _get_object_position(self, obj_id: str) -> Rect:
        """Get the calculated position for a specific object."""
        if not self._position_cache:
            self._position_cache = self._calculate_positions()

        return self._position_cache.get(
            obj_id, Rect(self.pad, self.pad, self.box_width, self.box_height)
        )

    def get_relative_pos(self, rect: Rect) -> Rect:
        """Returns a flow-optimized position for the object."""
        x, y, w, h = rect

        # If we don't have enough information yet, fall back to simple grid
        if len(self.parent._objects) <= 1:
            pad = self.pad
            x_shift = 3 * pad * self.x_layout_counter
            y_shift = 1.5 * pad * self.y_layout_counter
            x = pad + x_shift
            y = pad + y_shift

            self.x_layout_counter += 1
            if x + w + 2 * pad > self.parent.width:
                self.x_layout_counter = 0
                self.y_layout_counter += 1

            return Rect(x, y, w, h)

        # For objects added after initial layout, try to maintain flow
        # This is a simplified approach - in practice we'd want to recalculate
        # the entire layout when significant changes occur
        return self._get_next_flow_position(rect)

    def _get_next_flow_position(self, rect: Rect) -> Rect:
        """Calculate next position maintaining flow principles."""
        x, y, w, h = rect
        pad = self.pad

        # Try to find a good position based on existing objects
        existing_positions = [
            (obj.patching_rect.x, obj.patching_rect.y)
            for obj in self.parent._boxes
            if hasattr(obj, "patching_rect")
        ]

        if existing_positions:
            if self.flow_direction == "vertical":
                # Find the bottommost object and place new object below it
                max_y = max(pos[1] for pos in existing_positions)
                avg_x = sum(pos[0] for pos in existing_positions) / len(
                    existing_positions
                )

                y = max_y + self.box_height + pad
                x = avg_x

                # Wrap if we exceed height
                if y + h + pad > self.parent.height:
                    y = pad
                    x = max(pos[0] for pos in existing_positions) + self.box_width + pad
            else:
                # Find the rightmost object and place new object to its right
                max_x = max(pos[0] for pos in existing_positions)
                avg_y = sum(pos[1] for pos in existing_positions) / len(
                    existing_positions
                )

                x = max_x + self.box_width + pad
                y = avg_y

                # Wrap if we exceed width
                if x + w + pad > self.parent.width:
                    x = pad
                    y = (
                        max(pos[1] for pos in existing_positions)
                        + self.box_height
                        + pad
                    )
        else:
            # First object - place at standard starting position
            x = pad
            y = pad

        # Ensure positions stay within bounds
        x = min(max(x, pad), self.parent.width - w - pad)
        y = min(max(y, pad), self.parent.height - h - pad)

        return Rect(x, y, w, h)

    def _full_layout(self) -> None:
        """Perform full layout optimization based on signal flow analysis."""
        if len(self.parent._objects) < 2:
            return  # Nothing to optimize

        positions = self._calculate_positions()

        # Apply optimized positions to existing objects. The computed position
        # carries the manager's uniform grid size; keep each object's own w/h so
        # UI objects aren't squashed to text-box size (L2).
        for obj_id, position in positions.items():
            if obj_id in self.parent._objects:
                obj = self.parent._objects[obj_id]
                w, h = self.box_dims(obj)
                obj.patching_rect = Rect(position[0], position[1], w, h)

        # Prevent any remaining overlaps after flow layout
        self.prevent_overlaps()

        # Clear cache so future positions use the optimized layout
        self._position_cache = positions


# --------------------------------------------------------------------------
# py2max/layout/matrix.py
# --------------------------------------------------------------------------


class MatrixLayoutManager(LayoutManager):
    """Unified matrix/columnar layout manager with configurable flow direction.

    This layout manager can organize objects in two different patterns based on flow_direction:

    When flow_direction="column" (Columnar Layout):
    ```
    Column 0: Controls/Inputs  | Column 1: Generators | Column 2: Processors | Column 3: Outputs
    [control0]                 | [gen0]               | [proc0]              | [output0]
    [input0]                   | [gen1]               | [proc1]              | [output1]
    [control1]                 | [gen2]               | [proc2]              | [output2]
    ```

    When flow_direction="row" (Matrix Layout):
    ```
    Row 0 (Inputs/Controls): [input0/control0] [input1/control1] [input2/control2] ...
    Row 1 (Generators):     [gen0]             [gen1]             [gen2]             ...
    Row 2 (Processors):     [proc0]            [proc1]            [proc2]            ...
    Row 3 (Outputs):        [output0]          [output1]          [output2]          ...
    ```

    In column mode, objects are grouped by functional category into vertical columns.
    In row mode, signal chains form columns while functional categories form rows.

    Args:
        parent: The parent patcher object.
        pad: Padding between objects (default: 48.0).
        box_width: Default object width (default: 66.0).
        box_height: Default object height (default: 22.0).
        comment_pad: Padding for comments (default: 2).
        flow_direction: Layout direction - "column" or "row" (default: "row").
        num_dimensions: Number of columns (in column mode) or rows (in row mode) (default: 4).
        dimension_spacing: Extra spacing between dimensions (default: 100.0).
    """

    def __init__(
        self,
        parent: AbstractPatcher,
        pad: Optional[int] = None,
        box_width: Optional[int] = None,
        box_height: Optional[int] = None,
        comment_pad: Optional[int] = None,
        flow_direction: str = "row",
        num_dimensions: int = 4,
        dimension_spacing: float = 100.0,
        # Legacy parameters for backward compatibility
        num_rows: Optional[int] = None,
        row_spacing: Optional[float] = None,
        column_spacing: Optional[float] = None,
    ):
        # Handle legacy parameters
        if num_rows is not None:
            num_dimensions = num_rows
        if row_spacing is not None:
            dimension_spacing = row_spacing
        elif column_spacing is not None:
            dimension_spacing = column_spacing

        # Initialize parent layout manager
        super().__init__(parent, pad, box_width, box_height, comment_pad)

        self.flow_direction = flow_direction
        self.num_dimensions = num_dimensions
        self.dimension_spacing = dimension_spacing

        # Legacy properties for backward compatibility
        self.num_rows = num_dimensions

        # Layout-specific properties
        self._signal_chains: List[
            List[str]
        ] = []  # Each inner list is a connected signal chain (used in row mode)
        self._chain_assignments: Dict[
            str, int
        ] = {}  # object_id -> chain_index (used in row mode)
        self._column_assignments: Dict[
            str, int
        ] = {}  # object_id -> column/category assignment (used in both modes)

    @property
    def num_columns(self) -> int:
        """Number of functional columns (column mode); alias of num_dimensions."""
        return self.num_dimensions

    @num_columns.setter
    def num_columns(self, value: int) -> None:
        self.num_dimensions = value

    @property
    def column_spacing(self) -> float:
        """Get column spacing (legacy property)."""
        return self.dimension_spacing

    @column_spacing.setter
    def column_spacing(self, value: float) -> None:
        """Set column spacing and update dimension_spacing (legacy property)."""
        self.dimension_spacing = value

    @property
    def row_spacing(self) -> float:
        """Get row spacing (legacy property)."""
        return self.dimension_spacing

    @row_spacing.setter
    def row_spacing(self, value: float) -> None:
        """Set row spacing and update dimension_spacing (legacy property)."""
        self.dimension_spacing = value

    def _analyze_signal_chains(self) -> List[List[str]]:
        """Analyze connections to identify separate signal chains.

        Returns:
            List of signal chains, where each chain is a list of connected object IDs.
        """
        # Build directed connection graph (obj_id -> outgoing / incoming lists).
        graph = PatchGraph(self.parent._lines, nodes=self.parent._objects)
        connections = graph.out_lists()
        reverse_connections = graph.in_lists()

        # Find signal chains by tracing from sources to sinks
        visited = set()
        chains = []

        def trace_chain(start_obj: str) -> List[str]:
            """Trace a signal chain from a starting object."""
            chain: List[str] = []
            current: Optional[str] = start_obj
            chain_visited: set[str] = set()

            while current and current not in chain_visited:
                if current in visited:
                    break
                chain.append(current)
                chain_visited.add(current)
                visited.add(current)

                # Find next object in chain (prefer single output connections)
                next_objects = connections.get(current, [])
                if len(next_objects) == 1:
                    current = next_objects[0]
                elif len(next_objects) > 1:
                    # Multiple outputs - choose based on object type priority
                    # Prefer continuing to processors/outputs over controls
                    next_current: Optional[str] = None
                    for next_obj in next_objects:
                        if next_obj in self.parent._objects:
                            next_obj_category = self._classify_object(
                                self.parent._objects[next_obj]
                            )
                            if next_obj_category >= 2:  # Processors or outputs
                                next_current = next_obj
                                break
                    current = next_current or next_objects[0]
                else:
                    current = None

            return chain

        # Start from true sources -- objects nothing feeds into.
        #
        # This used to accept `len(inputs) <= 1`, which made every mid-chain
        # object a chain start. Since `visited` stops a chain the moment it
        # reaches an object another chain already claimed, whichever mid-chain
        # object came first in iteration order consumed the tail and left the
        # real source stranded in a chain of its own: `cycle~ -> gain~ ->
        # ezdac~` became three one-object chains, hence three matrix columns,
        # purely because the boxes were added in reverse signal order.
        sources = [
            obj_id for obj_id, inputs in reverse_connections.items() if not inputs
        ]

        # If no clear sources, start from input/control objects
        if not sources:
            sources = [
                obj_id
                for obj_id, obj in self.parent._objects.items()
                if self._classify_object(obj) == 0
            ]  # Input/Control objects

        # Trace chains from sources
        for source in sources:
            if source not in visited:
                chain = trace_chain(source)
                if chain:
                    chains.append(chain)

        # Handle remaining unvisited objects (disconnected or in cycles)
        remaining = [obj_id for obj_id in self.parent._objects if obj_id not in visited]
        for obj_id in remaining:
            if obj_id not in visited:
                chain = trace_chain(obj_id)
                if chain:
                    chains.append(chain)
                else:
                    # Single disconnected object - create a chain with just this object
                    chains.append([obj_id])
                    visited.add(obj_id)

        return chains

    def _assign_objects_to_matrix_positions(self) -> Dict[str, Tuple[int, float]]:
        """Assign each object to a (row, column) position in the matrix.

        Returns:
            Dictionary mapping object_id -> (row, column) tuple.
        """
        positions: Dict[str, Tuple[int, float]] = {}

        # Group objects by signal chain and category
        for chain_idx, chain in enumerate(self._signal_chains):
            # Within each chain, group by category (row)
            chain_by_category: Dict[int, List[str]] = {
                i: [] for i in range(self.num_rows)
            }

            for obj_id in chain:
                if obj_id in self.parent._objects:
                    obj = self.parent._objects[obj_id]
                    obj_category = self._classify_object(obj)
                    obj_category = min(
                        obj_category, self.num_rows - 1
                    )  # Ensure valid row
                    chain_by_category[obj_category].append(obj_id)
                    self._chain_assignments[obj_id] = chain_idx

            # Assign positions within this chain (column)
            for cat, obj_ids in chain_by_category.items():
                for i, obj_id in enumerate(obj_ids):
                    # If multiple objects of same category in one chain, spread them slightly
                    col_offset = chain_idx + (
                        i * 0.1
                    )  # Small offset for multiple objects
                    positions[obj_id] = (cat, col_offset)

        return positions

    def get_relative_pos(self, rect: Rect) -> Rect:
        """Returns a position based on flow_direction setting."""
        x, y, w, h = rect

        # For initial positioning during object creation, use simple grid
        # Real positioning happens in optimize_layout()
        num_created = len(self.parent._objects)

        if self.flow_direction == "column":
            # Columnar layout: cycle through columns first
            column = num_created % self.num_dimensions
            row = num_created // self.num_dimensions

            # Calculate column-based position
            column_width = (
                self.parent.width
                - self.pad * 2
                - self.dimension_spacing * (self.num_dimensions - 1)
            ) / self.num_dimensions
            x = self.pad + column * (column_width + self.dimension_spacing)
            y = self.pad + row * (self.box_height + self.pad // 2)
        else:
            # Matrix layout: cycle through rows first
            row = num_created % self.num_dimensions
            col = num_created // self.num_dimensions

            x = self.pad + col * (self.box_width + self.dimension_spacing)
            y = self.pad + row * (self.box_height + self.dimension_spacing)

        return Rect(x, y, w, h)

    def _full_layout(self) -> None:
        """Arrange objects based on the ``flow_direction`` setting.

        The matrix layout always recomputes the full arrangement from the
        signal-chain analysis.
        """
        if len(self.parent._objects) < 1:
            return

        if self.flow_direction == "column":
            # Use columnar layout (functional categories as columns)
            self._optimize_columnar_layout()
        else:
            # Use matrix layout (signal chains as columns, categories as rows)
            self._optimize_matrix_layout()

    def _optimize_matrix_layout(self) -> None:
        """Optimize the layout by organizing objects into a signal chain matrix."""
        # Step 1: Classify all objects into categories
        for obj_id, obj in self.parent._objects.items():
            if obj_id not in self._column_assignments:
                self._column_assignments[obj_id] = self._classify_object(obj)

        # Step 2: Analyze signal chains
        self._signal_chains = self._analyze_signal_chains()

        # Step 3: Assign matrix positions
        matrix_positions = self._assign_objects_to_matrix_positions()

        # Step 4: Apply matrix layout
        self._apply_matrix_layout(matrix_positions)

        # Step 5: Prevent any remaining overlaps
        self.prevent_overlaps()

    def _optimize_columnar_layout(self) -> None:
        """Optimize the layout by organizing objects into functional columns."""
        # Step 1: Classify all objects into columns
        for obj_id, obj in self.parent._objects.items():
            if obj_id not in self._column_assignments:
                self._column_assignments[obj_id] = self._classify_object(obj)

        # Step 3: Apply columnar layout
        self._apply_columnar_layout()

        # Step 4: Prevent any remaining overlaps
        self.prevent_overlaps()

    def _apply_matrix_layout(self, positions: Dict[str, Tuple[int, float]]) -> None:
        """Apply the matrix layout to all objects.

        Args:
            positions: Dictionary mapping object_id -> (row, column) tuple.
        """
        if not positions:
            return

        # Calculate grid dimensions
        max_row = max(pos[0] for pos in positions.values()) if positions else 0
        max_col = max(pos[1] for pos in positions.values()) if positions else 0

        # Calculate spacing to fit in patcher window
        available_width = self.parent.width - 2 * self.pad
        available_height = self.parent.height - 2 * self.pad

        if max_col > 0:
            col_spacing = min(self.column_spacing, available_width / (max_col + 1))
        else:
            col_spacing = self.column_spacing

        if max_row > 0:
            row_spacing = min(self.row_spacing, available_height / (max_row + 1))
        else:
            row_spacing = self.row_spacing

        # Position each object
        for obj_id, (row, col) in positions.items():
            if obj_id in self.parent._objects:
                obj = self.parent._objects[obj_id]

                # Calculate position
                x = self.pad + col * col_spacing
                y = self.pad + row * row_spacing

                # Ensure bounds
                x = min(max(x, self.pad), self.parent.width - self.box_width - self.pad)
                y = min(
                    max(y, self.pad), self.parent.height - self.box_height - self.pad
                )

                w, h = self.box_dims(obj)
                obj.patching_rect = Rect(x, y, w, h)

    def get_signal_chain_info(self) -> Dict[str, Any]:
        """Get information about detected signal chains.

        Returns:
            Dictionary with signal chain analysis results.
        """
        return {
            "num_chains": len(self._signal_chains),
            "chains": self._signal_chains,
            "chain_assignments": self._chain_assignments,
            "matrix_size": (self.num_rows, len(self._signal_chains)),
        }

    def _apply_columnar_layout(self) -> None:
        """Apply the columnar layout to all objects."""
        # Group objects by column
        column_objects: Dict[int, List[str]] = {
            i: [] for i in range(self.num_dimensions)
        }

        for obj_id, column in self._column_assignments.items():
            column = min(column, self.num_dimensions - 1)  # Ensure valid column
            column_objects[column].append(obj_id)

        # Calculate column dimensions
        column_width = (
            self.parent.width
            - self.pad * 2
            - self.dimension_spacing * (self.num_dimensions - 1)
        ) / self.num_dimensions

        # Position objects within each column
        for column_idx in range(self.num_dimensions):
            objects_in_column = column_objects[column_idx]
            if not objects_in_column:
                continue

            # Calculate column base x position
            column_x = self.pad + column_idx * (column_width + self.dimension_spacing)

            # Sort objects within column by their connections to maintain flow
            objects_in_column = self._sort_objects_in_column(objects_in_column)

            # Handle horizontal replication if column has too many objects
            objects_per_column = max(
                1,
                int(
                    (self.parent.height - 2 * self.pad)
                    / (self.box_height + self.pad // 2)
                ),
            )

            for i, obj_id in enumerate(objects_in_column):
                if obj_id in self.parent._objects:
                    obj = self.parent._objects[obj_id]

                    # Calculate position within column
                    sub_column = i // objects_per_column  # Horizontal replication index
                    row_in_sub_column = i % objects_per_column

                    # Calculate x position (with horizontal replication)
                    sub_column_width = column_width / max(
                        1, (len(objects_in_column) - 1) // objects_per_column + 1
                    )
                    x = column_x + sub_column * sub_column_width

                    # Calculate y position (top-down flow)
                    y = self.pad + row_in_sub_column * (self.box_height + self.pad // 2)

                    # Ensure bounds
                    x = min(
                        max(x, self.pad), self.parent.width - self.box_width - self.pad
                    )
                    y = min(
                        max(y, self.pad),
                        self.parent.height - self.box_height - self.pad,
                    )

                    w, h = self.box_dims(obj)
                    obj.patching_rect = Rect(x, y, w, h)

    def _sort_objects_in_column(self, obj_ids: List[str]) -> List[str]:
        """Sort objects within a column to maintain logical flow order.

        Args:
            obj_ids: List of object IDs to sort.

        Returns:
            Sorted list of object IDs based on connection flow.
        """
        if not obj_ids:
            return []

        # Post-order DFS from sources over the intra-column connection graph, so
        # objects appear after the ones that feed them (signal-flow order).
        return PatchGraph(self.parent._lines, nodes=obj_ids).topological_order()

    def _classify_object(self, obj: AbstractBox) -> int:
        """Classify an object and assign it to the appropriate column/row.

        Args:
            obj: The Box object to classify.

        Returns:
            Category index (0-3) for the object.
        """
        # Get the actual object name for classification
        if obj.maxclass == "newobj":
            text = obj._kwds.get("text", "")
            if text:
                object_name = text.split()[0] if text.split() else obj.maxclass
            else:
                object_name = obj.maxclass
        else:
            object_name = obj.maxclass

        return self._classify_by_name(obj, object_name)

    def _signal_column(self, object_name: str) -> Optional[int]:
        """Classify by the shipped maxref signal typing (authoritative).

        Returns a column index for objects that carry signal I/O, else ``None``::

            signal out only  -> 1 (generator / source)
            signal in only   -> 3 (output / sink)
            signal both ways -> 2 (processor)
        """

        inlet_types = maxref.get_inlet_types(object_name) or []
        outlet_types = maxref.get_outlet_types(object_name) or []
        signal_in = any("signal" in t for t in inlet_types)
        signal_out = any("signal" in t for t in outlet_types)
        if not (signal_in or signal_out):
            return None
        if signal_out and not signal_in:
            return 1
        if signal_in and not signal_out:
            return 3
        return 2

    def _classify_by_name(self, obj: AbstractBox, object_name: str) -> int:
        """Classify an object into a functional column (0-3).

        The curated functional sets in :mod:`py2max.maxref.category` take
        precedence, then maxref signal typing, then name patterns. Curated must
        win because functional intent does NOT map to raw signal I/O typing:

        - Most generators expose a signal inlet for modulation (even ``cycle~``
          takes a signal-rate frequency / phase), so signal typing would call
          them processors.
        - Signal *sources* that are semantically inputs (``adc~``, ``in~``,
          ``receive~``) would look like generators.

        maxref signal typing is therefore used only for objects the curated sets
        do not list -- it replaces name guessing for the audio long tail with
        ground truth (signal out only -> generator, in only -> output/sink, both
        -> processor). Name patterns remain the final fallback.
        """
        if object_name in category.INPUT_OBJECTS:
            return 0
        if object_name in category.CONTROL_OBJECTS:
            return 0
        if object_name in category.GENERATOR_OBJECTS:
            return 1
        if object_name in category.PROCESSOR_OBJECTS:
            return 2
        if object_name in category.OUTPUT_OBJECTS:
            return 3

        signal_col = self._signal_column(object_name)
        if signal_col is not None:
            return signal_col

        return self._infer_by_name(object_name)

    def _infer_by_name(self, object_name: str) -> int:
        """Infer a column from name patterns for objects nothing else knows.

        Matched at word boundaries (start/end/exact) rather than as bare
        substrings, so ``"in"`` does not match inside ``line~`` / ``sine~``.
        """
        name = object_name.lower().rstrip("~")

        def matches(words: List[str]) -> bool:
            return any(
                name == w or name.startswith(w) or name.endswith(w) for w in words
            )

        # Output-like (checked first because such names can also end with ~)
        if matches(["out", "dac", "record", "write", "send", "print", "meter"]):
            return 3
        # Input-like
        if matches(
            [
                "adc",
                "in",
                "inlet",
                "receive",
                "midiin",
                "notein",
                "ctlin",
                "bendin",
                "pgmin",
                "touchin",
            ]
        ):
            return 0
        # UI/control-like
        if matches(["button", "slider", "dial", "knob", "fader", "param"]):
            return 0
        # Audio objects (end with ~) are likely processors unless clearly generators
        if object_name.endswith("~"):
            if matches(["osc", "cycle", "saw", "noise", "play", "sample"]):
                return 1
            return 2
        # Non-signal object nothing knows: default to controls.
        return 0


class ColumnarLayoutManager(MatrixLayoutManager):
    """Functional-column layout: Controls -> Generators -> Processors -> Outputs.

    A thin specialization of :class:`MatrixLayoutManager` pinned to column mode,
    where objects are grouped by functional category into vertical columns rather
    than by signal chain. Selected via ``Patcher(..., layout="columnar")``.
    """

    def __init__(
        self,
        parent: AbstractPatcher,
        pad: Optional[int] = None,
        box_width: Optional[int] = None,
        box_height: Optional[int] = None,
        comment_pad: Optional[int] = None,
        num_dimensions: int = 4,
        dimension_spacing: float = 100.0,
    ):
        super().__init__(
            parent,
            pad,
            box_width,
            box_height,
            comment_pad,
            flow_direction="column",
            num_dimensions=num_dimensions,
            dimension_spacing=dimension_spacing,
        )


# --------------------------------------------------------------------------
# py2max/core/patcher.py
# --------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# CONSTANTS

MAX_VER_MAJOR = 8
MAX_VER_MINOR = 5
MAX_VER_REVISION = 5

# Module logger
logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Primary Classes


class Patcher(BoxFactoryMixin, SerializationMixin, AbstractPatcher):
    """Core class for creating and managing Max/MSP patches.

    The Patcher class provides a high-level interface for creating Max/MSP patches
    programmatically. It handles object positioning, connection validation, and
    automatic layout management.

    Features:
        - Automatic object positioning with multiple layout managers
        - Connection validation using Max object metadata
        - Support for all major Max object types
        - Hierarchical patch organization with subpatchers
        - Export to .maxpat file format

    Args:
        path: Output file path for the patch.
        title: Optional title for the patch.
        parent: Parent patcher for hierarchical organization.
        classnamespace: Namespace for object classes (e.g., 'rnbo').
        reset_on_render: Whether to reset layout on render.
        layout: Layout manager type ('horizontal', 'vertical', 'grid', 'flow', 'matrix', 'columnar').
        auto_hints: Whether to automatically generate object hints.
        openinpresentation: Presentation mode setting.
        validate_connections: Whether to validate patchline connections.
        validate_attrs: Whether to warn (UserWarning) when an object is given a
            keyword that is not a known attribute for its Max class -- catches
            typos like ``inital=`` for ``initial=``. Off by default.
        flow_direction: Direction for flow-based layouts ('horizontal', 'vertical').
        cluster_connected: Whether to cluster connected objects in grid layout.
        num_dimensions: Number of rows used by the matrix layout (also treated as column count when flow_direction='column').
        dimension_spacing: Spacing between rows/columns for matrix layout variants.
        semantic_ids: Whether to generate semantic IDs based on object names (e.g., 'cycle_1')
                     instead of numeric IDs (e.g., 'obj-1'). Enables more readable debugging.

    Example:
        >>> p = Patcher('my-patch.maxpat', layout='grid')
        >>> osc = p.add_textbox('cycle~ 440')
        >>> gain = p.add_textbox('gain~')
        >>> p.add_line(osc, gain)
        >>> p.save()

        >>> # With semantic IDs
        >>> p = Patcher('my-patch.maxpat', semantic_ids=True)
        >>> osc1 = p.add_textbox('cycle~ 440')  # ID: 'cycle_1'
        >>> osc2 = p.add_textbox('cycle~ 220')  # ID: 'cycle_2'
        >>> gain = p.add_textbox('gain~')       # ID: 'gain_1'
    """

    def __init__(
        self,
        path: Optional[Union[str, Path]] = None,
        title: Optional[str] = None,
        parent: Optional["AbstractPatcher"] = None,
        classnamespace: Optional[str] = None,
        reset_on_render: bool = True,
        layout: str = "horizontal",
        auto_hints: bool = False,
        openinpresentation: int = 0,
        validate_connections: bool = False,
        validate_attrs: bool = False,
        strict: bool = False,
        flow_direction: str = "horizontal",
        cluster_connected: bool = False,
        # Matrix layout configuration parameters
        num_dimensions: int = 4,
        dimension_spacing: float = 100.0,
        semantic_ids: bool = False,
        device_type: str = "audio_effect",
        param_placement: bool = False,
    ):
        logger.debug(
            f"Initializing Patcher: path={path}, layout={layout}, "
            f"validate_connections={validate_connections}, semantic_ids={semantic_ids}"
        )
        self._path = path
        self._parent = parent
        self._node_ids: list[str] = []  # ids by order of creation
        self._objects: dict[str, AbstractBox] = {}  # dict of objects by id
        self._boxes: list[AbstractBox] = []  # store child objects (boxes, etc.)
        self._lines: list[AbstractPatchline] = []  # store patchline objects
        self._edge_ids: list[
            tuple[str, str]
        ] = []  # store edge-ids by order of creation
        self._id_counter = 0
        self._reset_on_render = reset_on_render
        self._semantic_ids = semantic_ids
        self._semantic_counters: dict[str, int] = {}  # Track counts per object type
        self._device_type = device_type  # M4L device type for .amxd writes
        self._flow_direction = flow_direction
        self._cluster_connected = cluster_connected
        self._num_dimensions = num_dimensions
        self._dimension_spacing = dimension_spacing
        self._layout_mgr: AbstractLayoutManager = self.set_layout_mgr(layout)
        self._auto_hints = auto_hints
        self._validate_connections = validate_connections
        self._validate_attrs = validate_attrs
        self._strict = strict
        self._param_placement = param_placement
        self._pending_comments: list[
            tuple[str, str, Optional[str]]
        ] = []  # [(box_id, comment_text, comment_pos), ...]
        self._maxclass_methods = {
            # specialized methods
            "m": self.add_message,  # custom -- like keyboard shortcut
            "c": self.add_comment,  # custom -- like keyboard shortcut
            "coll": self.add_coll,
            "dict": self.add_dict,
            "table": self.add_table,
            "itable": self.add_itable,
            "umenu": self.add_umenu,
            "bpatcher": self.add_bpatcher,
        }
        # --------------------------------------------------------------------
        # begin max attributes
        if title:  # not a default attribute
            self.title = title
        self.fileversion: int = 1
        self.appversion = {
            "major": MAX_VER_MAJOR,
            "minor": MAX_VER_MINOR,
            "revision": MAX_VER_REVISION,
            "architecture": "x64",
            "modernui": 1,
        }
        self.classnamespace = classnamespace or "box"
        self.rect = Rect(85.0, 104.0, 640.0, 480.0)
        self.bglocked = 0
        self.openinpresentation = openinpresentation
        self.default_fontsize = 12.0
        self.default_fontface = 0
        self.default_fontname = "Arial"
        self.gridonopen = 1
        self.gridsize = [15.0, 15.0]
        self.gridsnaponopen = 1
        self.objectsnaponopen = 1
        self.statusbarvisible = 2
        self.toolbarvisible = 1
        self.lefttoolbarpinned = 0
        self.toptoolbarpinned = 0
        self.righttoolbarpinned = 0
        self.bottomtoolbarpinned = 0
        self.toolbars_unpinned_last_save = 0
        self.tallnewobj = 0
        self.boxanimatetime = 200
        self.enablehscroll = 1
        self.enablevscroll = 1
        self.devicewidth = 0.0
        self.description = ""
        self.digest = ""
        self.tags = ""
        self.style = ""
        self.subpatcher_template = ""
        self.assistshowspatchername = 0
        self.boxes: List[Dict[str, Any]] = []
        self.lines: List[Dict[str, Any]] = []
        # self.parameters: dict = {}
        self.dependency_cache: List[Any] = []
        self.autosave = 0

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(path='{self._path}')"

    def __iter__(self) -> Iterator[Any]:
        yield self
        for box in self._boxes:
            yield from iter(box)

    def find_by_id(self, box_id: str) -> Optional["Box"]:
        """Find a box by its ID.

        Args:
            box_id: The ID of the box to find.

        Returns:
            The Box object if found, None otherwise.

        Example:
            >>> p = Patcher('patch.maxpat')
            >>> osc = p.add_textbox('cycle~ 440')
            >>> found = p.find_by_id(osc.id)
            >>> assert found is osc
        """
        return cast(Optional["Box"], self._objects.get(box_id))

    def find_by_type(self, maxclass: str) -> List["Box"]:
        """Find all boxes of a specific Max object type.

        Args:
            maxclass: The Max object class name (e.g., 'newobj', 'message', 'comment').

        Returns:
            List of Box objects matching the type.

        Example:
            >>> p = Patcher('patch.maxpat')
            >>> p.add_textbox('cycle~ 440')
            >>> p.add_textbox('saw~ 220')
            >>> p.add_message('bang')
            >>> oscillators = [b for b in p.find_by_type('newobj')
            ...                if 'cycle~' in b.text or 'saw~' in b.text]
            >>> assert len(oscillators) == 2
        """
        return cast(
            List["Box"],
            [box for box in self._boxes if getattr(box, "maxclass", None) == maxclass],
        )

    def find_by_text(self, pattern: str, case_sensitive: bool = False) -> List["Box"]:
        """Find all boxes whose text matches a pattern.

        Args:
            pattern: The text pattern to search for (substring match).
            case_sensitive: Whether the search should be case-sensitive (default: False).

        Returns:
            List of Box objects whose text contains the pattern.

        Example:
            >>> p = Patcher('patch.maxpat')
            >>> p.add_textbox('cycle~ 440')
            >>> p.add_textbox('saw~ 220')
            >>> p.add_textbox('gain~ 0.5')
            >>> oscillators = p.find_by_text('~')
            >>> assert len(oscillators) == 3
            >>> just_cycle = p.find_by_text('cycle')
            >>> assert len(just_cycle) == 1
        """
        results = []
        for box in self._boxes:
            text = getattr(box, "text", "") or ""
            if not case_sensitive:
                if pattern.lower() in text.lower():
                    results.append(box)
            else:
                if pattern in text:
                    results.append(box)
        return cast(List["Box"], results)

    def apply_theme(self, theme: Union[str, Dict[str, "ColorLike"]]) -> "Patcher":
        """Apply a color theme to every box in this patcher (and subpatchers).

        ``theme`` is a named theme (``"light"``, ``"dark"``, ``"blue"``,
        ``"high-contrast"``) or a dict with ``"bg"`` / ``"text"`` / ``"border"``
        color values (each a name, hex string, or float sequence). Returns self
        for chaining.

        Example:
            >>> Patcher('p.maxpat').apply_theme('dark')
        """

        if isinstance(theme, str):
            if theme not in THEMES:
                raise ValueError(f"unknown theme {theme!r}; known: {sorted(THEMES)}")
            spec: Dict[str, "ColorLike"] = THEMES[theme]
        else:
            spec = theme
        for obj in self:
            if isinstance(obj, Box):
                obj.set_color(
                    bg=spec.get("bg"),
                    text=spec.get("text"),
                    border=spec.get("border"),
                )
        return self

    @property
    def filepath(self) -> Union[str, Path]:
        """Path the patcher was created with, or ``""`` if none was set."""
        if self._path is None:
            return ""
        return self._path

    @property
    def width(self) -> float:
        """width of patcher window."""
        # ``rect`` is a Rect when built programmatically but a plain list when
        # loaded from JSON (from_dict preserves it as-is for round-trip
        # fidelity); index by position so both work.
        return self.rect[2]

    @property
    def height(self) -> float:
        """height of patcher windows."""
        return self.rect[3]

    @classmethod
    def from_dict(
        cls, patcher_dict: Dict[str, Any], save_to: Optional[str] = None
    ) -> "Patcher":
        """create a patcher instance from a dict"""

        if save_to:
            patcher = cls(save_to)
        else:
            patcher = cls()
        # __init__ seeds every Max patcher attribute with a default (bglocked,
        # gridsize, autosave, dependency_cache, ...). Real Max subpatchers omit
        # a few of these -- notably ``autosave`` and ``dependency_cache``, which
        # are top-level only. Leaving the defaults in place injects keys the
        # original never had, so load/save is not byte-faithful for any patch
        # containing subpatchers (C5). Drop each seeded public default the source
        # dict does not carry, then overlay the source so the result mirrors the
        # input exactly. (Private ``_``-prefixed infrastructure is preserved.)
        for key in [k for k in vars(patcher) if not k.startswith("_")]:
            if key not in patcher_dict:
                delattr(patcher, key)
        patcher.__dict__.update(patcher_dict)

        for box_dict in patcher.boxes:
            box = box_dict["box"]
            b = Box.from_dict(box)
            assert b.id, "box must have id"
            patcher._objects[b.id] = b
            # b = patcher.box_from_dict(box)
            patcher._boxes.append(b)

            # Set parent reference for nested subpatchers
            if hasattr(b, "_patcher") and b._patcher is not None:
                b._patcher._parent = patcher

        for line_dict in patcher.lines:
            line = line_dict["patchline"]
            pl = Patchline.from_dict(line)
            patcher._lines.append(pl)

        patcher._restore_generation_state()
        return patcher

    def _restore_generation_state(self) -> None:
        """Rebuild the id/edge bookkeeping after loading boxes and lines.

        ``from_dict`` populates ``_objects``/``_boxes``/``_lines`` directly but
        leaves the generation counters and index lists at their construction-time
        defaults. Without this, the first ``add_*`` on a loaded patch restarts
        numbering at ``obj-1`` and collides with existing ids, and the node/edge
        indexes consulted by layout are silently incomplete. Reconstruct them so
        a loaded patch can be edited safely.
        """
        self._node_ids = [b.id for b in self._boxes if b.id]
        self._edge_ids = [(pl.src, pl.dst) for pl in self._lines]

        max_numeric = 0
        for b in self._boxes:
            if not b.id:
                continue
            numeric = re.match(r"obj-(\d+)$", b.id)
            if numeric:
                max_numeric = max(max_numeric, int(numeric.group(1)))
                continue
            # Semantic ids look like ``cycle_1``; keep the per-type counter ahead
            # of any loaded id so semantic-id edits don't collide either.
            semantic = re.match(r"(.+)_(\d+)$", b.id)
            if semantic:
                name, count = semantic.group(1), int(semantic.group(2))
                self._semantic_counters[name] = max(
                    self._semantic_counters.get(name, 0), count
                )
        self._id_counter = max_numeric

    @classmethod
    def from_file(
        cls, path: Union[str, Path], save_to: Optional[str] = None
    ) -> "Patcher":
        """create a patcher instance from a .maxpat or .amxd file"""

        path = Path(path)
        device_type: Optional[str] = None
        if path.suffix.lower() == ".amxd":
            # Lazy import: m4l is a feature layer, kept off core's import path.

            payload, device_type = unpack_amxd(path.read_bytes())
            maxpat = json.loads(payload)
        else:
            with open(path, encoding="utf8") as f:
                maxpat = json.load(f)
        patcher = Patcher.from_dict(maxpat["patcher"], save_to)
        if device_type is not None:
            patcher._device_type = device_type
        return patcher

    @staticmethod
    def _matches(box: AbstractBox, text: str) -> bool:
        """True if a box matches ``text`` by exact maxclass or text prefix.

        Shared predicate for the ``find*`` methods, which differ only in scope
        (recursive vs flat) and return shape, not in match semantics.
        """
        if box.maxclass == text:
            return True
        box_text = getattr(box, "text", "")
        return bool(box_text and box_text.startswith(text))

    def find(self, text: str) -> Optional["Box"]:
        """Find box object by maxclass or text pattern.

        Recursively searches through all objects in the patch (including
        subpatchers) to find one matching the specified maxclass or text prefix.

        Args:
            text: The maxclass name or text pattern to search for.

        Returns:
            The first matching Box object, or None if not found.
        """
        for obj in self:
            if not isinstance(obj, Patcher) and self._matches(obj, text):
                return cast("Box", obj)
        return None

    def find_box(self, text: str) -> Optional["Box"]:
        """Find a box in this patcher (non-recursive) by maxclass or text prefix.

        returns box if found else None
        """
        for box in self._objects.values():
            if self._matches(box, text):
                return cast("Box", box)
        return None

    def find_box_with_index(self, text: str) -> Optional[Tuple[int, "Box"]]:
        """Find a box and its index by maxclass or text prefix (non-recursive).

        returns (index, box) if found
        """
        for i, box in enumerate(self._boxes):
            if self._matches(box, text):
                return (i, cast("Box", box))
        return None

    def render(self, reset: bool = False) -> None:
        """cascade convert py2max objects to dicts."""
        # Flush deferred associated comments here (not only in save()) so every
        # serialization entry point -- save, save_as, to_json -- emits them.
        # Idempotent: _process_pending_comments clears its queue after running.
        self._process_pending_comments()
        if reset or self._reset_on_render:
            self.boxes = []
            self.lines = []
        for box in self._boxes:
            box.render()
            self.boxes.append(box.to_dict())
        self.lines = [line.to_dict() for line in self._lines]

    def enable_presentation(self, devicewidth: Optional[int] = None) -> "Patcher":
        """Configure this patcher to open as a Max for Live device.

        Sets ``openinpresentation=1`` so Ableton Live renders the device
        strip instead of the patcher view, and optionally sets
        ``devicewidth``. Ableton's device strip height is fixed at ~170 px;
        only width is author-controlled.
        """

        return enable_presentation(self, devicewidth=devicewidth)

    def enforce_integer_coords(self) -> int:
        """Round all rect coordinates in this patcher tree to integers.

        Ableton renders fractional device-strip coordinates blurry on
        non-retina displays. Returns the number of rects that were
        non-integer and got rounded. Recurses into subpatchers.
        """

        return enforce_integer_coords(self)

    def to_svg(
        self,
        output_path: Union[str, Path],
        show_ports: bool = True,
        title: Optional[str] = None,
    ) -> None:
        """Export this patcher to SVG format.

        Args:
            output_path: Output file path for the SVG.
            show_ports: Whether to show inlet/outlet ports on boxes.
            title: Optional title to display at top of SVG.

        Example:
            >>> p = Patcher('my-patch.maxpat')
            >>> osc = p.add_textbox('cycle~ 440')
            >>> dac = p.add_textbox('ezdac~')
            >>> p.add_line(osc, dac)
            >>> p.to_svg('/tmp/my-patch.svg')
        """

        export_svg(self, output_path, show_ports=show_ports, title=title)

    def to_svg_string(
        self,
        show_ports: bool = True,
        title: Optional[str] = None,
    ) -> str:
        """Export this patcher to SVG format as a string.

        Args:
            show_ports: Whether to show inlet/outlet ports on boxes.
            title: Optional title to display at top of SVG.

        Returns:
            SVG content as a string.

        Example:
            >>> p = Patcher('my-patch.maxpat')
            >>> osc = p.add_textbox('cycle~ 440')
            >>> svg_content = p.to_svg_string()
        """

        return export_svg_string(self, show_ports=show_ports, title=title)

    def get_id(self, object_name: Optional[str] = None) -> str:
        """Generate object ID, optionally semantic based on object name.

        Args:
            object_name: Optional Max object name (e.g., 'cycle~', 'gain~').
                        Used to generate semantic IDs like 'cycle_1' when
                        semantic_ids mode is enabled.

        Returns:
            Object ID string (e.g., 'obj-5' or 'cycle_1').
        """
        if self._semantic_ids and object_name:
            # Sanitize object name (remove ~, spaces, special chars)
            clean_name = (
                object_name.replace("~", "")
                .replace(" ", "_")
                .replace(".", "_")
                .replace("-", "_")
                .replace("[", "")
                .replace("]", "")
                .replace("(", "")
                .replace(")", "")
            )

            # Get or increment counter for this object type
            count = self._semantic_counters.get(clean_name, 0) + 1
            self._semantic_counters[clean_name] = count
            return f"{clean_name}_{count}"
        else:
            # Standard numeric ID
            self._id_counter += 1
            return f"obj-{self._id_counter}"

    def set_layout_mgr(self, name: str) -> layout_module.LayoutManager:
        """takes a name and returns an instance of a layout manager"""
        if name == "horizontal":
            return layout_module.HorizontalLayoutManager(self)
        elif name == "vertical":
            return layout_module.VerticalLayoutManager(self)
        elif name == "flow":
            return layout_module.FlowLayoutManager(
                self, flow_direction=self._flow_direction
            )
        elif name == "grid":
            return layout_module.GridLayoutManager(
                self,
                flow_direction=self._flow_direction,
                cluster_connected=self._cluster_connected,
            )
        elif name == "matrix":
            return layout_module.MatrixLayoutManager(
                self,
                flow_direction=self._flow_direction,
                num_dimensions=self._num_dimensions,
                dimension_spacing=self._dimension_spacing,
            )
        elif name == "columnar":
            # Functional-column layout (Controls -> Generators -> Processors ->
            # Outputs). Always column mode regardless of flow_direction.
            return layout_module.ColumnarLayoutManager(
                self,
                num_dimensions=self._num_dimensions,
                dimension_spacing=self._dimension_spacing,
            )
        elif name.startswith("graph:"):
            # External graph-layout engines (optional `graph` extra), applied
            # on optimize_layout(); e.g. layout="graph:hola" / "graph:cola".
            return layout_module.GraphLayoutManager(
                self, algorithm=name[len("graph:") :]
            )
        else:
            raise NotImplementedError(f"layout '{name}' doesn't exist")

    def get_pos(self, maxclass: Optional[str] = None) -> Rect:
        """get box rect (position) via maxclass or layout_manager"""
        if maxclass:
            return self._layout_mgr.get_pos(maxclass)
        return self._layout_mgr.get_pos()

    def optimize_layout(self) -> None:
        """Arrange the whole patch based on the active layout manager.

        Calls the layout manager to lay out every object, then repositions any
        associated comments based on the new box positions. The effect depends
        on the layout manager:

        - FlowLayoutManager: Arranges objects by signal flow topology
        - GridLayoutManager: Clusters connected objects together
        - Other managers: May have limited or no effect

        This is a batch, whole-patch operation intended to be called once after
        all objects and connections have been added. Interactive, per-edit
        relayout is out of scope for py2max (see ``docs/auto-layout.md`` in
        py2max-server).
        """
        if hasattr(self._layout_mgr, "optimize_layout"):
            self._layout_mgr.optimize_layout()

        # Dock value/UI params next to the object they drive (opt-in).
        if self._param_placement and hasattr(self._layout_mgr, "place_params"):
            self._layout_mgr.place_params()

        # Process pending comments after layout optimization
        self._process_pending_comments()

    def lint(self) -> "List[Finding]":
        """Return patch-level lint findings (errors and warnings), errors first.

        Checks connection validity, out-of-range ports, orphaned patchlines,
        duplicate IDs, overlapping objects, off-canvas objects, and unknown
        object classes. See :mod:`py2max.lint`.
        """

        return _lint(self)


# --------------------------------------------------------------------------
# py2max/lint.py
# --------------------------------------------------------------------------


# --- severities ---
ERROR = "error"
WARNING = "warning"

# --- finding codes ---
E_DUP_ID = "E-DUP-ID"
E_ORPHAN_LINE = "E-ORPHAN-LINE"
E_OUTLET_RANGE = "E-OUTLET-RANGE"
E_INLET_RANGE = "E-INLET-RANGE"
E_BAD_CONNECTION = "E-BAD-CONNECTION"
W_OVERLAP = "W-OVERLAP"
W_OFFCANVAS = "W-OFFCANVAS"
W_UNKNOWN_OBJECT = "W-UNKNOWN-OBJECT"


@dataclass
class Finding:
    """A single lint result."""

    code: str
    severity: str
    message: str
    obj_id: Optional[str] = None
    #: (src_id, outlet, dst_id, inlet) for connection findings
    line: Optional[Tuple[str, int, str, int]] = None

    def __str__(self) -> str:
        where = ""
        if self.line is not None:
            s, so, d, di = self.line
            where = f" [{s}:{so} -> {d}:{di}]"
        elif self.obj_id is not None:
            where = f" [{self.obj_id}]"
        return f"{self.severity.upper()} {self.code}: {self.message}{where}"


def _overlap(a: Any, b: Any) -> bool:
    return bool(
        a[0] < b[0] + b[2]
        and b[0] < a[0] + a[2]
        and a[1] < b[1] + b[3]
        and b[1] < a[1] + a[3]
    )


def _port(pair: Any, idx: int) -> int:
    """Second element of a source/destination pair, defaulting to 0."""
    return int(pair[idx]) if len(pair) > idx else 0


def _effective_counts(box: Any, name: str) -> Tuple[Optional[int], Optional[int]]:
    """(inlet_count, outlet_count) for a box, subpatcher-aware."""
    sub_in, sub_out = porttypes.subpatcher_counts(box)
    n_in, n_out = porttypes.port_counts(name, getattr(box, "text", None))
    return (
        sub_in if sub_in is not None else n_in,
        sub_out if sub_out is not None else n_out,
    )


def lint(patcher: Any) -> List[Finding]:
    """Return all lint findings for ``patcher`` and its subpatchers, errors first."""
    findings: List[Finding] = []
    _lint_level(patcher, findings, path="")
    findings.sort(key=lambda f: 0 if f.severity == ERROR else 1)
    return findings


def _lint_level(patcher: Any, findings: List[Finding], path: str) -> None:
    """Lint one patcher level; recurse into subpatchers.

    ``path`` prefixes object ids so a finding inside ``p sub`` is reported as
    ``sub-box-id/obj-1`` rather than an ambiguous ``obj-1``.
    """

    def qid(box_id: str) -> str:
        return f"{path}{box_id}"

    boxes = list(patcher._boxes)
    by_id: dict[str, Any] = {}

    # duplicate IDs
    for b in boxes:
        if b.id in by_id:
            findings.append(
                Finding(
                    E_DUP_ID, ERROR, f"duplicate object id {b.id!r}", obj_id=qid(b.id)
                )
            )
        else:
            by_id[b.id] = b

    # unknown object classes
    for b in boxes:
        name = object_name(b)
        if name and get_object_info(name) is None:
            findings.append(
                Finding(
                    W_UNKNOWN_OBJECT,
                    WARNING,
                    f"object {name!r} is not in the Max reference",
                    obj_id=qid(b.id),
                )
            )

    # off-canvas: object extends outside the patcher window
    rect = patcher.rect
    win_w, win_h = float(rect[2]), float(rect[3])
    for b in boxes:
        r = b.patching_rect
        x, y, w, h = float(r[0]), float(r[1]), float(r[2]), float(r[3])
        if x < 0 or y < 0 or x + w > win_w or y + h > win_h:
            findings.append(
                Finding(
                    W_OFFCANVAS,
                    WARNING,
                    f"object {b.id!r} extends outside the patcher window "
                    f"({win_w:.0f}x{win_h:.0f})",
                    obj_id=qid(b.id),
                )
            )

    # overlaps (dimension-aware)
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            if _overlap(boxes[i].patching_rect, boxes[j].patching_rect):
                findings.append(
                    Finding(
                        W_OVERLAP,
                        WARNING,
                        f"objects {boxes[i].id!r} and {boxes[j].id!r} overlap",
                        obj_id=qid(boxes[i].id),
                    )
                )

    # patchlines: orphans, out-of-range ports, message-type compatibility
    for pl in patcher._lines:
        src_id, outlet = pl.source[0], _port(pl.source, 1)
        dst_id, inlet = pl.destination[0], _port(pl.destination, 1)
        line = (qid(src_id), outlet, qid(dst_id), inlet)
        sb, db = by_id.get(src_id), by_id.get(dst_id)
        if sb is None or db is None:
            findings.append(
                Finding(
                    E_ORPHAN_LINE,
                    ERROR,
                    "patchline references a missing object",
                    line=line,
                )
            )
            continue

        src_name, dst_name = object_name(sb), object_name(db)
        _, n_out = _effective_counts(sb, src_name)
        n_in, _ = _effective_counts(db, dst_name)
        if n_out is not None and outlet >= n_out:
            findings.append(
                Finding(
                    E_OUTLET_RANGE,
                    ERROR,
                    f"{src_name!r} has {n_out} outlet(s); outlet {outlet} is out of range",
                    line=line,
                )
            )
            continue
        if n_in is not None and inlet >= n_in:
            findings.append(
                Finding(
                    E_INLET_RANGE,
                    ERROR,
                    f"{dst_name!r} has {n_in} inlet(s); inlet {inlet} is out of range",
                    line=line,
                )
            )
            continue

        emit = porttypes.outlet_emits(src_name, outlet)
        accepts, authoritative = porttypes.inlet_acceptance(dst_name, inlet)
        bang_reject = emit == porttypes.BANG and porttypes.inlet_rejects_bang(
            dst_name, inlet
        )
        if (
            bang_reject
            or porttypes.message_compatible(emit, accepts, authoritative) is False
        ):
            findings.append(
                Finding(
                    E_BAD_CONNECTION,
                    ERROR,
                    f"cannot connect {emit} outlet {outlet} of {src_name!r} "
                    f"to inlet {inlet} of {dst_name!r}",
                    line=line,
                )
            )

    # recurse into subpatchers (each has its own coordinate space)
    for b in boxes:
        child = getattr(b, "_patcher", None)
        if child is not None:
            _lint_level(child, findings, path=f"{path}{b.id}/")


def has_errors(findings: List[Finding]) -> bool:
    """True if any finding is error-severity."""
    return any(f.severity == ERROR for f in findings)


# --------------------------------------------------------------------------
# py2max/m4l.py
# --------------------------------------------------------------------------


_MAGIC = b"ampf"
_VERSION = 4
_PTCH_TAG = b"ptch"
_MXAC_TAG = b"mx@c"
_HEADER_SIZE = 36

_MXAC_CONST = 16
_MXAC_FLAGS = 0
_MXAC_PREAMBLE = 16  # bytes between "mx@c" tag and start of JSON

# Trailer chunk constants observed in Max-exported files.
_OF32_VALUE = 16
_VERS_VALUE = 0
_FLAG_VALUE = 17
_TYPE_PAYLOAD = b"JSON"

# Difference in seconds between the Unix epoch (1970-01-01 UTC) and the
# classic Mac/HFS epoch (1904-01-01 UTC) used by Max for its mdat field
# and creation/modification dates inside the patcher JSON.
MAX_EPOCH_OFFSET = 2_082_844_800

# Max for Live device-type markers at header offset 8.
DEVICE_TYPES: dict[str, bytes] = {
    "audio_effect": b"aaaa",
    "instrument": b"iiii",
    "midi_effect": b"mmmm",
}
_TAG_TO_DEVICE_TYPE: dict[bytes, str] = {v: k for k, v in DEVICE_TYPES.items()}


def unix_to_max_time(unix_seconds: Optional[float] = None) -> int:
    """Convert a Unix timestamp to Max's seconds-since-1904 epoch."""
    if unix_seconds is None:
        unix_seconds = time.time()
    return int(unix_seconds) + MAX_EPOCH_OFFSET


def _amxdtype_for(device_type: str) -> int:
    """Return the project.amxdtype int for a device type.

    The value is the FOURCC tag reinterpreted as a big-endian uint32:
    "aaaa" -> 0x61616161, "iiii" -> 0x69696969, "mmmm" -> 0x6d6d6d6d.
    """
    return int(struct.unpack(">I", _tag_for(device_type))[0])


def ensure_amxd_project_block(
    patcher_dict: Dict[str, Any],
    device_type: str = "audio_effect",
    mtime: Optional[int] = None,
) -> Dict[str, Any]:
    """Ensure the patcher dict carries the embedded ``project`` block Max
    requires for self-contained .amxd devices.

    Without this block, Max emits the diagnostic
    "a project without a name is like a day without sunshine. fatal." when
    loading the device. The block mirrors the one Max emits when exporting a
    device from a project; ``contents.patchers`` is left empty so the device
    is self-contained (no external .maxproj reference).

    Mutates ``patcher_dict['patcher']`` in place if the ``project`` key is
    absent. Returns the same dict for convenience.
    """
    inner = patcher_dict.get("patcher", patcher_dict)
    if "project" in inner:
        return patcher_dict
    if mtime is None:
        mtime = unix_to_max_time()
    inner["project"] = {
        "version": 1,
        "creationdate": mtime,
        "modificationdate": mtime,
        "viewrect": [0.0, 0.0, 300.0, 500.0],
        "autoorganize": 1,
        "hideprojectwindow": 1,
        "showdependencies": 1,
        "autolocalize": 0,
        "contents": {"patchers": {}},
        "layout": {},
        "searchpath": {},
        "detailsvisible": 0,
        "amxdtype": _amxdtype_for(device_type),
        "readonly": 0,
        "devpathtype": 0,
        "devpath": ".",
        "sortmode": 0,
        "viewmode": 0,
        "includepackages": 0,
    }
    return patcher_dict


def _tag_for(device_type: str) -> bytes:
    try:
        return DEVICE_TYPES[device_type]
    except KeyError as e:
        raise ValueError(
            f"unknown device_type {device_type!r}; "
            f"expected one of {sorted(DEVICE_TYPES)}"
        ) from e


def _pad4(payload: bytes) -> bytes:
    """Right-pad a chunk payload with zeros to a 4-byte boundary."""
    extra = (-len(payload)) % 4
    return payload + b"\x00" * extra


def _chunk(tag: bytes, payload: bytes) -> bytes:
    """Build an IFF-style chunk: FOURCC + BE u32 size + payload.

    Size is inclusive of the 8-byte header. Payloads must already be padded.
    """
    if len(tag) != 4:
        raise ValueError(f"chunk tag must be 4 bytes, got {tag!r}")
    size = 8 + len(payload)
    return tag + struct.pack(">I", size) + payload


def _u32_chunk(tag: bytes, value: int) -> bytes:
    return _chunk(tag, struct.pack(">I", value))


def pack_amxd(
    patcher_json: Union[str, bytes],
    *,
    device_type: str = "audio_effect",
    patcher_filename: str = "patcher.maxpat",
    mtime: Optional[int] = None,
) -> bytes:
    """Wrap patcher JSON in the .amxd binary container.

    Args:
        patcher_json: The patcher JSON, as a str or pre-encoded UTF-8 bytes.
        device_type: M4L device type. One of "audio_effect" (default),
            "instrument", or "midi_effect".
        patcher_filename: Filename to embed in the trailer's ``fnam`` chunk.
            Max uses this to resolve the patcher within the surrounding
            project. Defaults to ``"patcher.maxpat"``.
        mtime: Modification time, in Max's seconds-since-1904 epoch. If
            ``None``, the current time is used.
    """
    tag = _tag_for(device_type)
    if isinstance(patcher_json, str):
        json_bytes = patcher_json.encode("utf-8")
    else:
        json_bytes = patcher_json

    json_block = json_bytes + b"\x00"
    mxac_content_size = _MXAC_PREAMBLE + len(json_block)

    if mtime is None:
        mtime = unix_to_max_time()

    fname_payload = _pad4(patcher_filename.encode("utf-8") + b"\x00")
    dire_payload = b"".join(
        [
            _chunk(b"type", _TYPE_PAYLOAD),
            _chunk(b"fnam", fname_payload),
            _u32_chunk(b"sz32", len(json_block)),
            _u32_chunk(b"of32", _OF32_VALUE),
            _u32_chunk(b"vers", _VERS_VALUE),
            _u32_chunk(b"flag", _FLAG_VALUE),
            _u32_chunk(b"mdat", mtime),
        ]
    )
    dlst = _chunk(b"dlst", _chunk(b"dire", dire_payload))

    # Header
    header_top = _MAGIC + struct.pack("<I", _VERSION) + tag + _PTCH_TAG
    # ptch payload starts at offset 20 and runs to end of file.
    ptch_payload_size = (
        4  # "mx@c"
        + 4  # bytes 24-27 (BE 16)
        + 4  # bytes 28-31 (BE 0 flags)
        + 4  # bytes 32-35 (mxac content size)
        + len(json_block)
        + len(dlst)
    )

    mxac_block = (
        _MXAC_TAG
        + struct.pack(">I", _MXAC_CONST)
        + struct.pack(">I", _MXAC_FLAGS)
        + struct.pack(">I", mxac_content_size)
        + json_block
    )

    return header_top + struct.pack("<I", ptch_payload_size) + mxac_block + dlst


def unpack_amxd(data: bytes) -> Tuple[bytes, str]:
    """Extract the patcher JSON payload and device type from an .amxd byte string.

    Returns:
        A ``(payload, device_type)`` tuple where ``payload`` is the raw JSON
        bytes (no trailing NUL) and ``device_type`` is one of "audio_effect",
        "instrument", or "midi_effect".

    Raises:
        PatcherIOError: on an invalid header or unrecognized device tag.
    """
    if len(data) < _HEADER_SIZE:
        raise PatcherIOError(
            f"amxd file too short ({len(data)} bytes, need >= {_HEADER_SIZE})",
            operation="read",
        )

    if data[0:4] != _MAGIC:
        raise PatcherIOError(
            f"not an amxd file (magic={data[0:4]!r}, expected {_MAGIC!r})",
            operation="read",
        )

    version = struct.unpack("<I", data[4:8])[0]
    if version != _VERSION:
        raise PatcherIOError(
            f"unsupported amxd version {version} (expected {_VERSION})",
            operation="read",
        )

    tag = data[8:12]
    device_type = _TAG_TO_DEVICE_TYPE.get(tag)
    if device_type is None:
        raise PatcherIOError(
            f"unknown amxd device-type tag {tag!r} at offset 8 "
            f"(expected one of {sorted(DEVICE_TYPES.values())})",
            operation="read",
        )

    if data[12:16] != _PTCH_TAG:
        raise PatcherIOError(
            f"missing ptch tag at offset 12 (got {data[12:16]!r})",
            operation="read",
        )

    if data[20:24] != _MXAC_TAG:
        raise PatcherIOError(
            f"missing mx@c tag at offset 20 (got {data[20:24]!r})",
            operation="read",
        )

    mxac_content_size = struct.unpack(">I", data[32:36])[0]
    if mxac_content_size < _MXAC_PREAMBLE + 1:
        raise PatcherIOError(
            f"mx@c content size too small ({mxac_content_size})",
            operation="read",
        )
    json_block_len = mxac_content_size - _MXAC_PREAMBLE
    json_end_excl_nul = _HEADER_SIZE + json_block_len - 1
    if json_end_excl_nul > len(data):
        raise PatcherIOError(
            f"declared JSON length runs past end of file "
            f"({json_end_excl_nul} > {len(data)})",
            operation="read",
        )

    json_bytes = data[_HEADER_SIZE:json_end_excl_nul]
    return json_bytes, device_type


def read_amxd(path: Union[str, Path]) -> Tuple[Dict[str, Any], str]:
    """Read an .amxd file.

    Returns:
        A ``(patcher_dict, device_type)`` tuple.
    """
    path = Path(path)
    try:
        data = path.read_bytes()
    except OSError as e:
        raise PatcherIOError(
            f"failed to read amxd file: {path}", file_path=str(path), operation="read"
        ) from e

    payload, device_type = unpack_amxd(data)
    return json.loads(payload), device_type


def write_amxd(
    path: Union[str, Path],
    patcher_dict: Dict[str, Any],
    *,
    device_type: str = "audio_effect",
    patcher_filename: Optional[str] = None,
    mtime: Optional[int] = None,
) -> None:
    """Serialize a patcher dict and write it as a .amxd file.

    Args:
        path: Output path.
        patcher_dict: Patcher dict (the same shape as a .maxpat JSON).
        device_type: M4L device type. One of "audio_effect" (default),
            "instrument", or "midi_effect".
        patcher_filename: Filename to embed in the ``fnam`` trailer chunk.
            Defaults to the output path's stem with a ``.maxpat`` extension.
        mtime: Modification time in Max's seconds-since-1904 epoch.
            Defaults to the current time.
    """
    path = Path(path)
    if patcher_filename is None:
        patcher_filename = path.stem + ".maxpat"
    ensure_amxd_project_block(patcher_dict, device_type=device_type, mtime=mtime)
    payload = json.dumps(patcher_dict, indent=4)
    data = pack_amxd(
        payload,
        device_type=device_type,
        patcher_filename=patcher_filename,
        mtime=mtime,
    )
    try:
        if path.parent:
            path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    except OSError as e:
        raise PatcherIOError(
            f"failed to write amxd file: {path}",
            file_path=str(path),
            operation="write",
        ) from e


# ===========================================================================
# Max for Live (M4L) presentation-mode helpers
#
# M4L devices live in a fixed-size device strip in Ableton Live. The patcher
# renders in *presentation mode* (not patching mode), so each UI object must
# be explicitly marked with ``presentation=1`` and given a ``presentation_rect``.
# Infrastructure objects (``live.remote~``, ``live.map``, etc.) stay hidden.
#
# Constraints imposed by Live's device view:
# - Device strip height is fixed at ~170 px by the host.
# - Coordinates should be whole integers; fractional values render blurry on
#   non-retina displays.
# - ``devicewidth`` on the patcher controls the device strip width.
# ===========================================================================

# ---------------------------------------------------------------------------
# Object classification for presentation-mode filtering
#
# Only user-facing controls belong in the device strip. Infrastructure
# objects (Live API bridges, routing, device lifecycle) stay in the patcher
# but must not get presentation=1.

M4L_PRESENTATION_UI_CLASSES: FrozenSet[str] = frozenset(
    {
        "live.dial",
        "live.numbox",
        "live.slider",
        "live.menu",
        "live.tab",
        "live.text",
        "live.toggle",
        "live.button",
        "live.comment",
        "live.gain~",
        "live.step",
        "live.grid",
        "live.meter~",
        "live.scope~",
        # Classic (non-live.*) UI that also works in presentation
        "dial",
        "number",
        "flonum",
        "toggle",
        "button",
        "comment",
        "panel",
        "umenu",
        "slider",
    }
)

M4L_INFRASTRUCTURE_CLASSES: FrozenSet[str] = frozenset(
    {
        "live.remote~",
        "live.map",
        "live.object",
        "live.path",
        "live.observer",
        "live.thisdevice",
        "live.banks",
        "live.parameter",
    }
)

# Ableton's device view height is fixed; devicewidth is the one dim you set.
M4L_DEVICE_HEIGHT_PX = 170

# ---------------------------------------------------------------------------
# Integer-coordinate guardrail


class NonIntegerCoordinateWarning(UserWarning):
    """Emitted when a rect contains fractional coordinates."""


def _to_int_rect(rect: Iterable[Union[int, float]], *, context: str) -> List[int]:
    """Coerce a 4-tuple rect to ints, warning on non-integer inputs."""
    values = list(rect)
    if len(values) != 4:
        raise ValueError(f"rect must have 4 elements, got {len(values)}: {values}")

    rounded = []
    had_float = False
    for v in values:
        if isinstance(v, float) and not v.is_integer():
            had_float = True
        rounded.append(int(round(float(v))))

    if had_float:
        warnings.warn(
            f"M4L: non-integer coords in {context} {values} -> {rounded}; "
            "Ableton renders decimals blurry on non-retina.",
            NonIntegerCoordinateWarning,
            stacklevel=3,
        )
    return rounded


# ---------------------------------------------------------------------------
# Classification helpers


def _object_name(box: "Box") -> str:
    """Resolve the effective object name for classification (see utils.object_name)."""

    return object_name(box)


def is_presentation_ui(box: "Box") -> bool:
    """True if the box is a user-facing control suitable for presentation."""
    return _object_name(box) in M4L_PRESENTATION_UI_CLASSES


def is_m4l_infrastructure(box: "Box") -> bool:
    """True if the box is M4L infrastructure that must stay hidden."""
    return _object_name(box) in M4L_INFRASTRUCTURE_CLASSES


# ---------------------------------------------------------------------------
# Presentation-mode public API


def add_to_presentation(
    box: "Box",
    rect: Union[Iterable[Union[int, float]], Tuple[int, int, int, int]],
    *,
    strict: bool = False,
) -> "Box":
    """Mark a box as a presentation-mode UI element.

    Sets ``presentation=1`` and ``presentation_rect=[x, y, w, h]``. Rounds
    fractional coordinates to integers with a warning. Refuses known
    infrastructure objects (``live.remote~`` etc.), which must not appear in
    the device strip.

    Args:
        box: the Box to expose in presentation mode.
        rect: [x, y, width, height] in device-strip coordinates.
        strict: if True, warn when the box is not a recognized UI class.
            Useful to catch typos early; defaults to False so user-defined
            or unusual UI objects still work.
    """
    if is_m4l_infrastructure(box):
        raise ValueError(
            f"refusing to add {_object_name(box)!r} to presentation: it is "
            "M4L infrastructure and must stay hidden from the device strip."
        )

    if strict and not is_presentation_ui(box):
        warnings.warn(
            f"M4L: {_object_name(box)!r} is not a known presentation UI class; "
            "it may still work but is unusual in a device strip.",
            UserWarning,
            stacklevel=2,
        )

    int_rect = _to_int_rect(rect, context=f"{_object_name(box)} presentation_rect")

    # These are patcher-level attributes on the box dict.
    box.presentation = 1  # type: ignore[attr-defined]
    box.presentation_rect = int_rect  # type: ignore[attr-defined]
    return box


def enable_presentation(
    patcher: "Patcher",
    devicewidth: Union[int, None] = None,
) -> "Patcher":
    """Configure a patcher to open in presentation mode as an M4L device.

    Sets ``openinpresentation=1`` and optionally ``devicewidth`` (px).
    Ableton's device strip height is fixed at ~170 px; only width is
    author-controlled.
    """
    patcher.openinpresentation = 1
    if devicewidth is not None:
        patcher.devicewidth = int(round(devicewidth))
    return patcher


def enforce_integer_coords(patcher: "Patcher") -> int:
    """Walk a patcher and round all rect coords to integers.

    Returns the number of rects that were non-integer (and got rounded).
    Recurses into nested subpatchers.
    """

    def _round_rect(rect: Any) -> int:
        """Round a rect in-place. Returns 1 if any coord was non-integer."""
        # Rect dataclass with .x/.y/.w/.h or a plain [x,y,w,h] list.
        if hasattr(rect, "x"):
            coords = [rect.x, rect.y, rect.w, rect.h]
            if any(isinstance(v, float) and not v.is_integer() for v in coords):
                rect.x, rect.y, rect.w, rect.h = (int(round(v)) for v in coords)
                return 1
        elif isinstance(rect, list):
            if any(isinstance(v, float) and not v.is_integer() for v in rect):
                rect[:] = [int(round(v)) for v in rect]
                return 1
        return 0

    changed = 0
    for box in patcher._boxes:
        pr = getattr(box, "patching_rect", None)
        if pr is not None:
            changed += _round_rect(pr)

        if hasattr(box, "presentation_rect"):
            changed += _round_rect(box.presentation_rect)

        sub = getattr(box, "_patcher", None)
        if sub is not None:
            changed += enforce_integer_coords(sub)

    return changed


# --------------------------------------------------------------------------
# py2max/export/svg.py
# --------------------------------------------------------------------------


# SVG styling constants -- approximate Max's default light theme.
BG_COLOR = "#cfcfcf"  # patcher background
BOX_FILL = "#e2e2e2"  # default object box
BOX_STROKE = "#8c8c8c"
BOX_STROKE_WIDTH = 1
COMMENT_FILL = "#ffffd0"
MESSAGE_FILL = "#dcdcdc"  # message box
SUBPATCHER_FILL = "#d3dcec"  # subpatchers get a blue tint
UI_FILL = "#f4f4f4"  # UI widgets (toggle/button/dial/slider/number)
UI_ACCENT = "#3a6ea5"  # UI indicator (dial pointer, slider thumb, ...)
TEXT_COLOR = "#1a1a1a"
TEXT_FONT_FAMILY = "Helvetica, Arial, sans-serif"
TEXT_FONT_SIZE = 12
# Connections: signal cables are drawn thicker and in a distinct color.
LINE_COLOR = "#5a5a5a"  # message/control cable
LINE_WIDTH = 1.2
SIGNAL_LINE_COLOR = "#b58900"  # signal cable
SIGNAL_LINE_WIDTH = 2.4
# Ports, colored by signal vs message/control.
SIGNAL_PORT_COLOR = "#2e8b57"  # signal inlets/outlets
MESSAGE_PORT_COLOR = "#1f1f1f"  # control/message inlets/outlets
PORT_RADIUS = 2.5
PADDING = 20

# UI objects whose glyph replaces a text label.
_ICON_ONLY = {"toggle", "button", "bng", "dial", "slider"}


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #
def _escape_text(text: str) -> str:
    """Escape text for SVG."""
    return html.escape(str(text))


def _kwd(box: AbstractBox, key: str) -> object:
    """Read a value out of the box's stored keyword attributes."""
    kw = getattr(box, "_kwds", None)
    if isinstance(kw, dict):
        return kw.get(key)
    return None


def _rgba_to_css(seq: object) -> Optional[str]:
    """Convert a Max ``[r, g, b, a]`` float list (0..1) to a CSS color.

    Returns ``None`` when ``seq`` is not a usable color sequence.
    """
    if not isinstance(seq, (list, tuple)) or len(seq) < 3:
        return None
    try:
        r, g, b = (int(round(float(seq[i]) * 255)) for i in range(3))
        a = float(seq[3]) if len(seq) > 3 else 1.0
    except (TypeError, ValueError):
        return None
    r, g, b = (max(0, min(255, c)) for c in (r, g, b))
    if a >= 1.0:
        return f"rgb({r},{g},{b})"
    return f"rgba({r},{g},{b},{a:.3f})"


def _rect_of(box: AbstractBox) -> Optional[Tuple[float, float, float, float]]:
    """Return ``(x, y, w, h)`` for a box, or ``None`` if it has no rect."""
    rect = getattr(box, "patching_rect", None)
    if not rect:
        return None
    if hasattr(rect, "x"):
        return (float(rect.x), float(rect.y), float(rect.w), float(rect.h))
    if isinstance(rect, (list, tuple)) and len(rect) >= 4:
        return (float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3]))
    return None


def _is_subpatcher(box: AbstractBox) -> bool:
    """True if the box embeds a subpatcher (``p``, ``bpatcher``, ``poly~`` ...)."""
    if getattr(box, "subpatcher", None) is not None:
        return True
    text = str(getattr(box, "text", "") or "")
    return text == "p" or text.startswith(
        ("p ", "bpatcher", "poly~", "gen~", "gen ", "rnbo~")
    )


# --------------------------------------------------------------------------- #
# Colors
# --------------------------------------------------------------------------- #
def _default_fill(box: AbstractBox) -> str:
    maxclass = getattr(box, "maxclass", "newobj")
    if maxclass == "comment":
        return COMMENT_FILL
    if maxclass == "message":
        return MESSAGE_FILL
    if maxclass in ("toggle", "button", "bng", "dial", "slider", "number", "flonum"):
        return UI_FILL
    if _is_subpatcher(box):
        return SUBPATCHER_FILL
    return BOX_FILL


def _box_colors(box: AbstractBox) -> Tuple[str, str, str]:
    """Return ``(fill, stroke, text_color)`` honoring user-set box colors."""
    fill = _rgba_to_css(_kwd(box, "bgcolor")) or _default_fill(box)
    stroke = (
        _rgba_to_css(_kwd(box, "bordercolor"))
        or _rgba_to_css(_kwd(box, "color"))
        or BOX_STROKE
    )
    text_color = (
        _rgba_to_css(_kwd(box, "textcolor"))
        or _rgba_to_css(_kwd(box, "color"))
        or TEXT_COLOR
    )
    return fill, stroke, text_color


# --------------------------------------------------------------------------- #
# Ports (counts come from the box's own numinlets/numoutlets)
# --------------------------------------------------------------------------- #
def _outlet_types(box: AbstractBox) -> List[str]:
    ot = getattr(box, "outlettype", None)
    if isinstance(ot, (list, tuple)) and ot:
        return [str(t) for t in ot]
    if hasattr(box, "get_outlet_types"):
        try:
            return [str(t) for t in (box.get_outlet_types() or [])]
        except Exception:
            return []
    return []


def _inlet_types(box: AbstractBox) -> List[str]:
    if hasattr(box, "get_inlet_types"):
        try:
            return [str(t) for t in (box.get_inlet_types() or [])]
        except Exception:
            return []
    return []


def _port_color(types: List[str], idx: int) -> str:
    if idx < len(types) and types[idx] == "signal":
        return SIGNAL_PORT_COLOR
    return MESSAGE_PORT_COLOR


def _inlet_count(box: AbstractBox) -> int:
    """Number of inlets to draw.

    The box's own ``numinlets`` is authoritative -- it is what gets written to
    the ``.maxpat`` and therefore matches Max's real port layout, and it needs
    no maxref lookup. Fall back to maxref, then to a private cache, only when
    the box does not declare it.
    """
    n = getattr(box, "numinlets", None)
    if n is not None:
        return int(n)
    if hasattr(box, "get_inlet_count"):
        try:
            return int(box.get_inlet_count() or 0)
        except Exception:
            pass
    return int(getattr(box, "_inlet_count", 0) or 0)


def _outlet_count(box: AbstractBox) -> int:
    """Number of outlets to draw (see :func:`_inlet_count`)."""
    n = getattr(box, "numoutlets", None)
    if n is not None:
        return int(n)
    if hasattr(box, "get_outlet_count"):
        try:
            return int(box.get_outlet_count() or 0)
        except Exception:
            pass
    return int(getattr(box, "_outlet_count", 0) or 0)


def _render_ports(box: AbstractBox, x: float, y: float, w: float, h: float) -> str:
    parts = []
    ic = _inlet_count(box)
    if ic > 0:
        itypes = _inlet_types(box)
        spacing = w / (ic + 1)
        for i in range(ic):
            parts.append(
                f'<circle cx="{x + spacing * (i + 1)}" cy="{y}" r="{PORT_RADIUS}" '
                f'fill="{_port_color(itypes, i)}" stroke="{BOX_STROKE}" '
                f'stroke-width="0.5" />'
            )
    oc = _outlet_count(box)
    if oc > 0:
        otypes = _outlet_types(box)
        spacing = w / (oc + 1)
        for i in range(oc):
            parts.append(
                f'<circle cx="{x + spacing * (i + 1)}" cy="{y + h}" r="{PORT_RADIUS}" '
                f'fill="{_port_color(otypes, i)}" stroke="{BOX_STROKE}" '
                f'stroke-width="0.5" />'
            )
    return "\n".join(parts)


def _get_port_position(
    box: AbstractBox, port_index: int, is_outlet: bool
) -> Tuple[float, float]:
    """x,y of an inlet/outlet, using the same counts as :func:`_render_ports`."""
    r = _rect_of(box)
    if r is None:
        return (0.0, 0.0)
    x, y, w, h = r
    count = _outlet_count(box) if is_outlet else _inlet_count(box)
    count = max(count, 1)  # avoid div-by-zero; a connected port implies >=1
    spacing = w / (count + 1)
    port_x = x + spacing * (port_index + 1)
    port_y = y + h if is_outlet else y
    return (port_x, port_y)


# --------------------------------------------------------------------------- #
# Box shapes
# --------------------------------------------------------------------------- #
def _rect(x: float, y: float, w: float, h: float, fill: str, stroke: str) -> str:
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" '
        f'stroke="{stroke}" stroke-width="{BOX_STROKE_WIDTH}" rx="2" />'
    )


def _message_shape(
    x: float, y: float, w: float, h: float, fill: str, stroke: str
) -> str:
    """A message box: rectangle with a small flag notch on the right edge."""
    flag = min(h * 0.4, 8.0)
    right = x + w
    path = (
        f"M {x} {y} L {right - flag} {y} L {right} {y + h / 2} "
        f"L {right - flag} {y + h} L {x} {y + h} Z"
    )
    return (
        f'<path d="{path}" fill="{fill}" stroke="{stroke}" '
        f'stroke-width="{BOX_STROKE_WIDTH}" />'
    )


def _toggle_glyph(x: float, y: float, w: float, h: float, stroke: str) -> str:
    ins = min(w, h) * 0.22
    return (
        f'<line x1="{x + ins}" y1="{y + ins}" x2="{x + w - ins}" y2="{y + h - ins}" '
        f'stroke="{stroke}" stroke-width="1.5" />'
        f'<line x1="{x + w - ins}" y1="{y + ins}" x2="{x + ins}" y2="{y + h - ins}" '
        f'stroke="{stroke}" stroke-width="1.5" />'
    )


def _button_glyph(x: float, y: float, w: float, h: float, stroke: str) -> str:
    r = min(w, h) / 2 - min(w, h) * 0.18
    return (
        f'<circle cx="{x + w / 2}" cy="{y + h / 2}" r="{r}" fill="none" '
        f'stroke="{stroke}" stroke-width="1.2" />'
    )


def _number_glyph(x: float, y: float, w: float, h: float, stroke: str) -> str:
    """The little right-pointing triangle marker on a number box's left edge."""
    cy = y + h / 2
    return (
        f'<polygon points="{x + 3},{cy - 3} {x + 3},{cy + 3} {x + 7},{cy}" '
        f'fill="{stroke}" />'
    )


def _dial_glyph(x: float, y: float, w: float, h: float, stroke: str) -> str:
    cx, cy = x + w / 2, y + h / 2
    r = min(w, h) / 2 - 2
    # pointer toward the lower-left (a dial's minimum position)
    px = cx - r * 0.7
    py = cy + r * 0.7
    return (
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{stroke}" '
        f'stroke-width="1.2" />'
        f'<line x1="{cx}" y1="{cy}" x2="{px}" y2="{py}" stroke="{UI_ACCENT}" '
        f'stroke-width="1.5" />'
    )


def _slider_glyph(x: float, y: float, w: float, h: float, stroke: str) -> str:
    """A thumb bar; horizontal if wider than tall, else vertical."""
    if w >= h:
        tx = x + w * 0.3
        return (
            f'<line x1="{tx}" y1="{y + 2}" x2="{tx}" y2="{y + h - 2}" '
            f'stroke="{UI_ACCENT}" stroke-width="2.5" />'
        )
    ty = y + h * 0.7  # low value sits near the bottom
    return (
        f'<line x1="{x + 2}" y1="{ty}" x2="{x + w - 2}" y2="{ty}" '
        f'stroke="{UI_ACCENT}" stroke-width="2.5" />'
    )


def _render_shape(
    box: AbstractBox,
    maxclass: str,
    x: float,
    y: float,
    w: float,
    h: float,
    fill: str,
    stroke: str,
) -> str:
    if maxclass == "message":
        return _message_shape(x, y, w, h, fill, stroke)
    base = _rect(x, y, w, h, fill, stroke)
    if maxclass == "toggle":
        return base + "\n" + _toggle_glyph(x, y, w, h, stroke)
    if maxclass in ("button", "bng"):
        return base + "\n" + _button_glyph(x, y, w, h, stroke)
    if maxclass in ("number", "flonum", "number~"):
        return base + "\n" + _number_glyph(x, y, w, h, stroke)
    if maxclass == "dial":
        return base + "\n" + _dial_glyph(x, y, w, h, stroke)
    if maxclass == "slider":
        return base + "\n" + _slider_glyph(x, y, w, h, stroke)
    return base


def _get_box_text(box: AbstractBox) -> str:
    text = getattr(box, "text", None)
    if text:
        return str(text)
    return getattr(box, "maxclass", "newobj")


def _text_svg(
    x: float, y: float, h: float, text: str, color: str, x_offset: float = 5.0
) -> str:
    return (
        f'<text x="{x + x_offset}" y="{y + h / 2 + TEXT_FONT_SIZE / 3}" '
        f'font-family="{TEXT_FONT_FAMILY}" font-size="{TEXT_FONT_SIZE}" '
        f'fill="{color}">{_escape_text(text)}</text>'
    )


def _render_box(box: AbstractBox, show_ports: bool = True) -> str:
    """Render a single box (shape, label, and ports) to SVG."""
    r = _rect_of(box)
    if r is None:
        return ""
    x, y, w, h = r
    maxclass = getattr(box, "maxclass", "newobj")
    fill, stroke, text_color = _box_colors(box)

    parts = [_render_shape(box, maxclass, x, y, w, h, fill, stroke)]

    # Text label -- skipped for icon-only widgets whose glyph is the content.
    if maxclass not in _ICON_ONLY:
        text = _get_box_text(box)
        if text:
            x_offset = 10.0 if maxclass in ("number", "flonum", "number~") else 5.0
            parts.append(_text_svg(x, y, h, text, text_color, x_offset))

    if show_ports:
        ports = _render_ports(box, x, y, w, h)
        if ports:
            parts.append(ports)

    return "\n".join(p for p in parts if p)


# --------------------------------------------------------------------------- #
# Patchlines
# --------------------------------------------------------------------------- #
def _render_patchline(line: AbstractPatchline, patcher: Patcher) -> str:
    src_id = getattr(line, "src", None)
    dst_id = getattr(line, "dst", None)
    if not src_id or not dst_id:
        return ""

    src_box = patcher._objects.get(src_id)
    dst_box = patcher._objects.get(dst_id)
    if not src_box or not dst_box:
        return ""

    source = getattr(line, "source", [src_id, 0])
    destination = getattr(line, "destination", [dst_id, 0])
    src_port = int(source[1]) if len(source) > 1 else 0
    dst_port = int(destination[1]) if len(destination) > 1 else 0

    x1, y1 = _get_port_position(src_box, src_port, is_outlet=True)
    x2, y2 = _get_port_position(dst_box, dst_port, is_outlet=False)

    # Signal cables (from a signal outlet) are drawn thicker and distinct.
    out_types = _outlet_types(src_box)
    is_signal = src_port < len(out_types) and out_types[src_port] == "signal"
    color = SIGNAL_LINE_COLOR if is_signal else LINE_COLOR
    width = SIGNAL_LINE_WIDTH if is_signal else LINE_WIDTH

    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
        f'stroke="{color}" stroke-width="{width}" stroke-linecap="round" />'
    )


def _calculate_viewbox(patcher: Patcher) -> Tuple[float, float, float, float]:
    """Calculate SVG viewBox to fit all objects with padding."""
    boxes = patcher._boxes
    if not boxes:
        return (0.0, 0.0, 800.0, 600.0)

    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")
    for box in boxes:
        r = _rect_of(box)
        if r is None:
            continue
        x, y, w, h = r
        min_x = min(min_x, x)
        min_y = min(min_y, y)
        max_x = max(max_x, x + w)
        max_y = max(max_y, y + h)

    if min_x == float("inf"):
        return (0.0, 0.0, 800.0, 600.0)

    min_x -= PADDING
    min_y -= PADDING
    max_x += PADDING
    max_y += PADDING
    return (min_x, min_y, max_x - min_x, max_y - min_y)


def _build_svg(
    patcher: Patcher, show_ports: bool = True, title: Optional[str] = None
) -> str:
    """Build the full SVG document for a patcher as a string."""
    vx, vy, vw, vh = _calculate_viewbox(patcher)

    parts: List[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{vx} {vy} {vw} {vh}" width="{vw}" height="{vh}">',
        "",
        "<defs>",
        "  <style>",
        "    text { user-select: none; }",
        "  </style>",
        "</defs>",
        "",
        f'<rect x="{vx}" y="{vy}" width="{vw}" height="{vh}" fill="{BG_COLOR}" />',
        "",
    ]

    if title:
        parts.append(
            f'<text x="{vx + vw / 2}" y="{vy + 20}" '
            f'font-family="{TEXT_FONT_FAMILY}" font-size="16" font-weight="bold" '
            f'fill="{TEXT_COLOR}" text-anchor="middle">{_escape_text(title)}</text>'
        )
        parts.append("")

    parts.append("<!-- Patchlines -->")
    for line in patcher._lines:
        line_svg = _render_patchline(line, patcher)
        if line_svg:
            parts.append(line_svg)
    parts.append("")

    parts.append("<!-- Boxes -->")
    for box in patcher._boxes:
        box_svg = _render_box(box, show_ports=show_ports)
        if box_svg:
            parts.append(box_svg)
    parts.append("")

    parts.append("</svg>")
    return "\n".join(parts)


def export_svg(
    patcher: Patcher,
    output_path: Union[str, Path],
    show_ports: bool = True,
    title: Optional[str] = None,
) -> None:
    """Export a patcher to SVG format.

    Args:
        patcher: The Patcher object to export.
        output_path: Output file path for the SVG.
        show_ports: Whether to show inlet/outlet ports on boxes.
        title: Optional title to display at top of SVG.

    Example:
        >>> p = Patcher('test.maxpat')
        >>> osc = p.add_textbox('cycle~ 440')
        >>> dac = p.add_textbox('ezdac~')
        >>> p.add_line(osc, dac)
        >>> export_svg(p, '/tmp/test.svg')
    """
    Path(output_path).write_text(
        _build_svg(patcher, show_ports=show_ports, title=title), encoding="utf-8"
    )


def export_svg_string(
    patcher: Patcher,
    show_ports: bool = True,
    title: Optional[str] = None,
) -> str:
    """Export a patcher to SVG format as a string.

    Args:
        patcher: The Patcher object to export.
        show_ports: Whether to show inlet/outlet ports on boxes.
        title: Optional title to display at top of SVG.

    Returns:
        SVG content as a string.

    Example:
        >>> p = Patcher('test.maxpat')
        >>> svg_str = export_svg_string(p)
    """
    return _build_svg(patcher, show_ports=show_ports, title=title)


class GraphLayoutManager:  # pragma: no cover - excluded from the single file
    """Placeholder: graph layouts need third-party backends.

    ``layout="graph:*"`` requires networkx/pygraphviz/ogdf and therefore cannot
    ship in a dependency-free single file. Install the full package for it:
    ``pip install "py2max[graph]"``.
    """

    def __init__(self, *args: Any, **kwds: Any) -> None:
        raise NotImplementedError(
            "graph layouts are not available in the single-file edition of "
            'py2max; install the full package: pip install "py2max[graph]"'
        )


# Aliases from stripped intra-package imports (e.g. `from .lint import lint as _lint_patch`).
_lint = lint
_lint_patch = lint
