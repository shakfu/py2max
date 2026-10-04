"""py2max: a pure python library to generate .maxpat patcher files.

GENERATED FILE -- DO NOT EDIT BY HAND.
py2max 0.4.1, generated from a2d8e36 (working tree modified)
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
    FrozenSet,
    Iterable,
    List,
    Optional,
    Tuple,
    Union,
    cast,
)
from typing import (
    Iterator,
)
from typing import Set
from typing import NamedTuple
from typing import Sequence, TypedDict
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


def _atom(token: str) -> Any:
    """A Max atom from a text token: int, float, or symbol."""
    if re.fullmatch(r"[-+]?\d+", token):
        return int(token)
    try:
        return float(token)
    except ValueError:
        return token


def parse_attr_args(tokens: List[str]) -> Tuple[List[str], Dict[str, Any]]:
    """Split box-text arguments into leading positionals and ``@attr`` values.

    ``["a", "@size", "3", "@color", "1", "0", "0", "1"]`` gives
    ``(["a"], {"size": 3, "color": [1, 0, 0, 1]})``. An attribute with one
    value maps to a scalar, with several to a list, with none to ``[]``.
    """
    first = next((i for i, t in enumerate(tokens) if t.startswith("@")), len(tokens))
    attrs: Dict[str, Any] = {}
    name = None
    values: List[Any] = []
    for token in tokens[first:] + ["@"]:
        if token.startswith("@"):
            if name:
                attrs[name] = values[0] if len(values) == 1 else values
            name, values = token[1:], []
        else:
            values.append(_atom(token))
    return tokens[:first], attrs


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


# Keys whose values carry ``.x/.y/.w/.h`` semantics, i.e. the ones py2max reads
# attribute-wise. Deliberately excludes the other ``*rect`` props
# (``client_rect``, ``dstrect``, ``storage_rect``, ...), which are opaque
# passthrough values the library never interprets.
RECT_KEYS = ("rect", "patching_rect", "presentation_rect")


def as_rect(value: Any) -> Any:
    """Coerce a 4-element JSON array into a ``Rect``, else pass it through.

    JSON has no tuple type, so a patch read off disk carries every rect as a
    plain list. ``Box.patching_rect`` is declared ``Optional[Rect]`` and read as
    ``rect.x``/``rect.y`` by the layout managers, so leaving the list in place
    breaks ``optimize_layout()`` on any loaded patch. Anything that is not a
    4-element sequence is left untouched rather than guessed at.
    """
    if isinstance(value, (list, tuple)) and len(value) == 4:
        return Rect(*value)
    return value


def rects_to_lists(d: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize ``Rect`` values in a serialization dict back to plain lists.

    ``Rect`` is an internal convenience type; the ``.maxpat`` format has only
    JSON arrays. Both forms encode identically via ``json.dump``, but leaking a
    NamedTuple out of ``to_dict()`` makes the result compare unequal to the dict
    it was loaded from, so the mapping is undone at the serialization boundary.
    Mutates and returns ``d``, which is always a fresh copy at the call sites.
    """
    for key in RECT_KEYS:
        value = d.get(key)
        if isinstance(value, Rect):
            d[key] = list(value)
    return d


# Advance widths in 1/1000 em from the Helvetica AFM, which Arial (Max's
# default box font) matches. Unlisted characters count as 556, a digit.
_GLYPH_WIDTHS: Dict[str, int] = {
    **dict.fromkeys("0123456789#$_?", 556),
    **dict(
        zip(
            "abcdefghijklmnopqrstuvwxyz",
            (
                556,
                556,
                500,
                556,
                556,
                278,
                556,
                556,
                222,
                222,
                500,
                222,
                833,
                556,
                556,
                556,
                556,
                333,
                500,
                278,
                556,
                500,
                722,
                500,
                500,
                500,
            ),
        )
    ),
    **dict(
        zip(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
            (
                667,
                667,
                722,
                722,
                667,
                611,
                778,
                722,
                278,
                500,
                667,
                556,
                833,
                722,
                778,
                667,
                778,
                722,
                667,
                611,
                722,
                667,
                944,
                667,
                667,
                611,
            ),
        )
    ),
    " ": 278,
    "!": 278,
    '"': 355,
    "%": 889,
    "&": 667,
    "'": 191,
    "(": 333,
    ")": 333,
    "*": 389,
    "+": 584,
    ",": 278,
    "-": 333,
    ".": 278,
    "/": 278,
    ":": 278,
    ";": 278,
    "<": 584,
    "=": 584,
    ">": 584,
    "@": 1015,
    "[": 278,
    "\\": 278,
    "]": 278,
    "^": 469,
    "`": 333,
    "{": 334,
    "|": 260,
    "}": 334,
    "~": 584,
}

# Fitted on 392 Arial newobj/message boxes in 60 Max-written patches: box
# width is text width plus 10.6 px (median error 2 px), at least 15 px per
# port and 28 px overall.
_BOX_TEXT_PAD = 10.6
_BOX_PORT_WIDTH = 15.0
_BOX_MIN_WIDTH = 28.0


def text_width(text: str, fontsize: float = 12.0) -> float:
    """Rendered width in px of one line of Arial ``text``."""
    return sum(_GLYPH_WIDTHS.get(c, 556) for c in text) * fontsize / 1000


def box_width_for(text: str, ports: int = 1, fontsize: float = 12.0) -> float:
    """Width Max gives an object or message box holding ``text``."""
    longest = max(
        (text_width(line, fontsize) for line in text.split("\n")), default=0.0
    )
    return round(
        max(longest + _BOX_TEXT_PAD, _BOX_PORT_WIDTH * ports, _BOX_MIN_WIDTH), 1
    )


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
    pad: float

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
    _on_invalid: str
    _validate_attrs: bool
    _maxclass_methods: dict[str, Callable[..., Any]]
    _semantic_ids: bool
    _semantic_counters: dict[str, int]
    _device_type: str
    _needs_js2max_runtime: bool
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
    # maxref lists 1 inlet for inlet and 2 for outlet; Max writes 0 and 1.
    "inlet": {
        "maxclass": "inlet",
        "numinlets": 0,
        "numoutlets": 1,
        "outlettype": [""],
        "patching_rect": Rect(x=0.0, y=0.0, w=30.0, h=30.0),
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
    "outlet": {
        "maxclass": "outlet",
        "numinlets": 1,
        "numoutlets": 0,
        "patching_rect": Rect(x=0.0, y=0.0, w=30.0, h=30.0),
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
        "palette": {"action": entry["pa"]} if entry["pa"] else {},
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
# py2max/maxref/parser.py (partial: MAXCLASS_DEFAULTS, MaxClassDefaults, _DEFAULT_RECT, get_inlet_count, get_inlet_types, get_legacy_defaults, get_outlet_count, get_outlet_types, validate_connection)
# --------------------------------------------------------------------------


# Module logger

# Prebuilt bundle shipped in the wheel; used as a fallback when no local Max
# installation is found (e.g. on Linux). Generated by
# scripts/build_maxref_bundle.py on a Max-equipped machine.

# Sentinel marking a refdict entry that lives in the bundle, not on disk.

# Matches an ampersand that does NOT begin a valid XML entity (named, decimal,
# or hex character reference).

# refpages location inside a macOS Max.app and a Windows Max install folder

# Global cache instance

# Legacy compatibility - generate defaults from .maxref.xml when available
_DEFAULT_RECT = Rect(x=0.0, y=0.0, w=60.0, h=22.0)  # immutable, so shared


def get_legacy_defaults(name: str) -> Dict[str, Any]:
    """Get legacy-compatible defaults for a Max object

    This function extracts basic information needed for backwards compatibility
    with the old MAXCLASS_DEFAULTS structure.
    """
    data = get_object_info(name)
    if not data:
        return {}

    # A box class (UI objects, inlet, message, ...) is one whose palette entry
    # creates the object by its own name; everything else is a "newobj".

    defaults: Dict[str, Any] = {}
    if name in LEGACY_DEFAULTS or data.get("palette", {}).get("action") == name:
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

    defaults["patching_rect"] = _DEFAULT_RECT

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
    "trigger": _unpack_counts,  # one outlet per argument
    "t": _unpack_counts,
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
    r_in, r_out = arg_port_counts(maxclass, text)
    return (
        r_in if r_in is not None else n_in,
        r_out if r_out is not None else n_out,
    )


def arg_port_counts(maxclass: str, text: Optional[str] = None) -> _Counts:
    """``(inlet_count, outlet_count)`` implied by ``text``'s arguments alone.

    ``None`` for a dimension that does not depend on arguments.
    """
    resolver = _ARG_RESOLVERS.get(maxclass)
    return resolver(_args(text)) if resolver is not None else (None, None)


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


# A right inlet is strict only when its digest describes a signal and nothing
# else: "(signal) Trigger", not "(signal/float) Duty Cycle" or "Reset Input".
_PLAIN_SIGNAL_DIGEST = re.compile(r"\s*\(signal\)[^,;]*", re.IGNORECASE)
_CONTROL_WORD = re.compile(r"\b(int|float|number|bang|list|reset|message)s?\b", re.I)

_OTHER_INLET = re.compile(
    r"\b(right|middle|other|either|each|any|all|second|third)\b[^.]*\binlets?\b"
)


def _left_inlet_only(spec: object) -> bool:
    """True if a maxref method's description confines it to the left inlet."""
    text = str(spec.get("description", "") if isinstance(spec, dict) else "").lower()
    return "left inlet" in text and not _OTHER_INLET.search(text)


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
        # maxref types many right inlets "signal" that also take numbers
        # (clip~ min/max, scope~ buffer size); its methods give that away
        methods = {
            name
            for name, spec in (info.get("methods", {}) if info else {}).items()
            if not _left_inlet_only(spec)
        }
        if "anything" in methods:
            return frozenset({ANY}), False
        control = {
            _METHOD_TO_KIND[m] for m in methods & {"bang", "int", "float", "list"}
        }
        if control:
            return frozenset({SIGNAL} | control), False
        digest = inlets[index].get("digest", "") if 0 <= index < len(inlets) else ""
        if not _PLAIN_SIGNAL_DIGEST.fullmatch(digest) or _CONTROL_WORD.search(digest):
            return frozenset({ANY}), False  # digest says more than "signal"
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
        return dict(box=rects_to_lists(d))

    @classmethod
    def from_dict(cls, obj_dict: Dict[str, Any]) -> "Box":
        """create instance from dict"""
        box = cls()
        box.__dict__.update(obj_dict)
        for key in RECT_KEYS:
            if key in box.__dict__:
                box.__dict__[key] = as_rect(box.__dict__[key])
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
        """Return the patcher as a ``.maxpat`` dictionary.

        Renders first, so the result is the patcher as it stands rather than as
        it stood after whatever last happened to render it. It did not, and the
        failure was silent and order-dependent: ``to_dict()`` returned a patcher
        with *no boxes* until something else called ``render()``, and the same
        call on the same object then started returning them. A test asserting
        over ``to_dict()`` examined an empty patcher and passed for the wrong
        reason, which is how this was found.

        Rendering here also removes the asymmetry with ``Box.to_dict()``, which
        has always returned a populated box with no preparation required.
        """
        self.render()
        d = vars(self).copy()
        to_del = [k for k in d if k.startswith("_")]
        for k in to_del:
            del d[k]
        rects_to_lists(d)
        if not self._parent:
            return dict(patcher=d)
        return d

    def to_json(self) -> str:
        """cascade convert to json"""
        # No `render()` here: `to_dict()` does its own, and rendering twice was
        # only ever safe because it is idempotent.
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

            # A patch holding a [v8 js2max.v8.js] box needs that file beside
            # it, or it opens with a broken object. Only patchers that asked for
            # the bridge get one, so an ordinary save never writes a second file.
            if getattr(self, "_needs_js2max_runtime", False):
                installed = js2max_runtime.install(resolved_path.parent)
                logger.info(f"Installed js2max runtime: {installed}")

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


# Max objects whose inlet/outlet counts are determined by their code (or, for
# bpatcher, the patch it loads) rather than by a fixed maxref entry. Connection
# validation for these consults the box's own declared numinlets/numoutlets
# instead of the static maxref data.
DYNAMIC_IO_MAXCLASSES = frozenset({"gen.codebox~", "codebox", "codebox~", "bpatcher"})


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
        "background",
        "patcher",  # embedded subpatcher (p, gen~, rnbo~, bpatcher)
        "rnbo_classname",  # every box in an rnbo~ patcher
        "bgfillcolor_angle",
        "bgfillcolor_autogradient",
        "bgfillcolor_color",
        "bgfillcolor_color1",
        "bgfillcolor_color2",
        "bgfillcolor_proportion",
        "bgfillcolor_type",
    }
)

# Keys Max saves on these boxes that their maxref entries do not declare.
# Measured on 868 boxes in 60 Max-written patches.
SAVED_BOX_ATTRS: Dict[str, FrozenSet[str]] = {
    "comment": frozenset({"linecount"}),
    "message": frozenset({"linecount"}),
    "flonum": frozenset({"format"}),
    "inlet": frozenset({"index"}),
    "outlet": frozenset({"index"}),
    "waveform~": frozenset({"ruler"}),
    "live.gain~": frozenset({"lastchannelcount"}),
    "radiogroup": frozenset({"disabled", "value"}),
    "preset": frozenset({"preset_data"}),
    "function": frozenset({"addpoints"}),
    "autopattr": frozenset({"restore"}),
    "pattr": frozenset({"restore"}),
    "table~": frozenset({"showeditor"}),
    "table": frozenset({"showeditor"}),
    # written by add_coll / add_bpatcher / add_beap
    "coll": frozenset({"coll_data"}),
    "bpatcher": frozenset({"viewvisibility", "extract"}),
}


def unknown_attrs(name: str, keys: Iterable[str]) -> List[str]:
    """The ``keys`` that are not known attributes of Max object ``name``.

    Known means the attributes maxref declares for ``name`` and for ``jbox``
    (the base box class), ``UNIVERSAL_BOX_ATTRS``, ``SAVED_BOX_ATTRS``, and
    the keys of ``name``'s curated defaults. An object with no maxref entry
    cannot be checked, so nothing is reported for it.
    """

    info = maxref.get_object_info(name)
    if not info:
        return []
    jbox = maxref.get_object_info("jbox") or {}
    known = (
        UNIVERSAL_BOX_ATTRS
        | SAVED_BOX_ATTRS.get(name, frozenset())
        | set(CURATED.get(name, {}))
        | set(jbox.get("attributes", {}))
        | set(info.get("attributes", {}))
    )
    return [k for k in keys if k not in known]


class BoxFactoryMixin(AbstractPatcher):
    """Object creation (boxes, patchlines, and the add_* factory) for Patcher."""

    def _validate_box_attrs(self, box: "Box") -> None:
        """Warn when a box carries keywords that are not known attributes.

        Best-effort lint, enabled by ``Patcher(validate_attrs=True)``. The known
        set is the object's maxref attributes plus ``UNIVERSAL_BOX_ATTRS``;
        objects with no maxref entry are skipped (cannot be checked).
        """
        name = self._get_object_name(box)
        for key in unknown_attrs(name, box._kwds):
            warnings.warn(
                f"Unknown attribute {key!r} for Max object {name!r} (possible typo?)",
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

    def _connection_error(
        self, src_id: str, src_outlet: int, dst_id: str, dst_inlet: int
    ) -> str:
        """Why a connection is invalid, or ``""`` if it is fine or uncheckable."""
        src_obj = self._objects.get(src_id)
        dst_obj = self._objects.get(dst_id)
        if not src_obj:
            return f"Source object not found: {src_id}"
        if not dst_obj:
            return f"Destination object not found: {dst_id}"

        src_name = self._get_object_name(src_obj)
        dst_name = self._get_object_name(dst_obj)
        src_dynamic = src_obj.maxclass in DYNAMIC_IO_MAXCLASSES
        dst_dynamic = dst_obj.maxclass in DYNAMIC_IO_MAXCLASSES

        if src_dynamic or dst_dynamic:
            # Codeboxes and bpatchers derive their inlet/outlet counts from
            # their content, so bound-check indices against the box's own
            # declared counts rather than the fixed maxref entry. Type
            # checking is skipped: the content's port types are unknown here.
            src_outlets = (
                src_obj.numoutlets if src_dynamic else maxref.get_outlet_count(src_name)
            )
            dst_inlets = (
                dst_obj.numinlets if dst_dynamic else maxref.get_inlet_count(dst_name)
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
        else:
            _, error_msg = maxref.validate_connection(
                src_name,
                src_outlet,
                dst_name,
                dst_inlet,
                src_text=getattr(src_obj, "text", None),
                dst_text=getattr(dst_obj, "text", None),
            )
        if not error_msg:
            return ""
        return (
            f"Invalid connection from {src_name}[{src_outlet}] to "
            f"{dst_name}[{dst_inlet}]: {error_msg}"
        )

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

        if self._validate_connections:
            error = self._connection_error(src_id, src_outlet, dst_id, dst_inlet)
            if error:
                if self._on_invalid == "raise":
                    raise InvalidConnectionError(
                        error,
                        src=src_id,
                        dst=dst_id,
                        outlet=src_outlet,
                        inlet=dst_inlet,
                    )
                logger.warning(error)

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

        arg_in, arg_out = porttypes.arg_port_counts(_maxclass, text)
        code = kwds.get("code")
        if _maxclass in ("codebox", "codebox~") and isinstance(code, str):
            # like gen codeboxes, RNBO codeboxes take their ports from the code
            arg_in, arg_out = (
                _max_gen_io_index(code, "in"),
                _max_gen_io_index(code, "out"),
            )
        if numinlets is None:
            numinlets = arg_in
        if numoutlets is None:
            numoutlets = arg_out

        if defaults:
            if maxclass is None and defaults.get("maxclass"):
                maxclass = defaults["maxclass"]

            if numinlets is None and "numinlets" in defaults:
                numinlets = defaults["numinlets"]

            if numoutlets is None and "numoutlets" in defaults:
                numoutlets = defaults["numoutlets"]

        kwds = self._textbox_helper(_maxclass, kwds)

        auto_rect = patching_rect is None
        layout_rect = self.get_pos(maxclass) if maxclass else self.get_pos()
        if patching_rect is None and maxclass in ("inlet", "outlet"):
            layout_rect = self._right_of_ports(maxclass, layout_rect)
        if patching_rect is None and defaults and defaults.get("patching_rect"):
            default_rect = defaults["patching_rect"]
            patching_rect = Rect(
                layout_rect.x, layout_rect.y, default_rect.w, default_rect.h
            )
        elif patching_rect is None:
            patching_rect = layout_rect

        # An object with no maxref entry gets one outlet by default (not zero):
        # a zero-outlet object cannot act as a connection source, which is wrong
        # for the hand-typed long-tail objects that land here. Matches
        # Box.__init__'s default.
        if numoutlets is None:
            numoutlets = 1
        if outlettype is None:
            outlettype = (list(defaults.get("outlettype", [])) if defaults else [])[
                :numoutlets
            ]
            outlettype += [""] * (numoutlets - len(outlettype))

        maxclass = maxclass or "newobj"
        if maxclass in ("message", "comment"):
            kwds["text"] = " ".join(tail)  # type: ignore[typeddict-unknown-key]
        elif maxclass == "newobj":
            kwds["text"] = text  # type: ignore[typeddict-unknown-key]
        elif tail:
            # UI boxes store state as box attributes; explicit kwds win
            positional, attrs = parse_attr_args(tail)
            if positional:
                logger.warning(
                    f"{maxclass!r} is a UI box; ignoring arguments {positional} "
                    "(use @attr value or a keyword argument)"
                )
            # Text attributes escape the type checker, so check them even when
            # validate_attrs is off (add_box checks every key when it is on).
            if not self._validate_attrs:
                for key in unknown_attrs(_maxclass, attrs):
                    warnings.warn(
                        f"Unknown attribute {key!r} for Max object {_maxclass!r} "
                        f"(possible typo?)",
                        UserWarning,
                        stacklevel=2,
                    )
            kwds = {**attrs, **kwds}  # type: ignore[typeddict-item]

        if auto_rect and maxclass in ("newobj", "message"):
            patching_rect = self._fit_text_width(
                patching_rect,
                cast(str, kwds["text"]),  # type: ignore[typeddict-item]
                max(numinlets or 1, numoutlets),
                kwds.get("fontsize"),
            )

        return self.add_box(
            Box(
                id=id or self.get_id(_maxclass),
                maxclass=maxclass,
                numinlets=numinlets if numinlets is not None else 1,
                numoutlets=numoutlets,
                outlettype=outlettype,
                patching_rect=patching_rect,
                **kwds,
            ),
            comment,
            comment_pos,
        )

    @staticmethod
    def _fit_text_width(
        rect: Rect, text: str, ports: int, fontsize: Optional[float]
    ) -> Rect:
        """``rect`` with the width Max would give a box holding ``text``."""
        width = box_width_for(text, ports, float(fontsize or 12.0))
        return Rect(rect[0], rect[1], width, rect[3])

    def _right_of_ports(self, kind: str, rect: Rect) -> Rect:
        """``rect`` moved right of every existing ``kind`` box, in its row.

        Max numbers ports by x, so a new port placed left of an older one (the
        grid wraps rows) would take its number.
        """
        ports = [
            b.patching_rect
            for b in self._boxes
            if b.maxclass == kind and b.patching_rect is not None
        ]
        if not ports:
            return rect
        last = max(ports, key=lambda r: r[0])
        if rect[0] > last[0]:
            return rect
        return Rect(last[0] + last[2] + self._layout_mgr.pad, last[1], rect[2], rect[3])

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

        n_out = kwds.pop("numoutlets", None) or _max_gen_io_index(code, "out")
        return self.add_box(
            Box(
                id=id or self.get_id(_maxclass),
                code=code,
                maxclass=_maxclass,
                # ports come from the code's inN / outN, as for gen codeboxes
                numinlets=kwds.pop("numinlets", None) or _max_gen_io_index(code, "in"),
                numoutlets=n_out,
                outlettype=kwds.pop("outlettype", None) or [""] * n_out,
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

    def add_v8_bridge(
        self,
        bundle: Optional[str] = None,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        **kwds: "Unpack[TextboxProps]",
    ) -> "Box":
        """Add a ``[v8]`` box running the js2max bridge, and ship it with the patch.

        js2max is the JavaScript counterpart to this package: it runs *inside*
        an open patcher and can build objects into it from a patch description,
        or serialize the patcher back out to a ``.maxpat``. Adding this box is
        what makes a generated patch able to do either.

        The runtime is written next to the patch when it is saved -- Max
        resolves a bare filename through the folder holding the patch, so the
        two sitting together need no configuration. Nothing is written for a
        patcher that never called this, so an ordinary ``save()`` cannot leave a
        stray ``.js`` file behind.

        Args:
            bundle: Filename of the runtime to load. Defaults to the shipped
                drop-in build; pass another name only if you are installing the
                runtime yourself under a different name.
            patching_rect: Position and size of the box.
            id: Explicit object id.
            comment: Associated comment text.
            comment_pos: Where to place the associated comment.
            **kwds: Further box properties.

        Returns:
            The ``[v8]`` box, so it can be wired up like any other.

        Example:
            >>> p = Patcher('builder.maxpat')
            >>> bridge = p.add_v8_bridge()
            >>> p.save()   # writes builder.maxpat and js2max.v8.js beside it
        """

        # Marks the patcher, not the box: `save_as` needs to know whether to
        # install the runtime, and it is the patcher that gets saved.
        #
        # Only for the shipped bundle. A caller naming their own file has placed
        # it themselves, and copying `js2max.v8.js` next to a patch that refers
        # to something else would be both useless and surprising.
        self._needs_js2max_runtime = bundle is None or bundle == V8_BUNDLE
        return self.add_textbox(
            f"v8 {bundle or V8_BUNDLE}",
            patching_rect=patching_rect,
            id=id,
            comment=comment,
            comment_pos=comment_pos,
            **kwds,
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

        if patching_rect is None:
            patching_rect = self._fit_text_width(
                self.get_pos(), text or "", 2, kwds.get("fontsize")
            )
        return self.add_box(
            Box(
                id=id or self.get_id("message"),
                text=text or "",
                maxclass="message",
                numinlets=2,
                numoutlets=1,
                outlettype=[""],
                patching_rect=patching_rect,
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
                # Stated rather than left to Box.__init__'s defaults, which are
                # the wrong way round here: a comment takes a `set` message and
                # emits nothing. Confirmed against a patch Max itself saved,
                # which rewrote py2max's 0-in/1-out to 1-in/0-out.
                numinlets=1,
                numoutlets=0,
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

        # The rewired cords restate connections that already exist, so checking
        # them would re-report old faults, or under "raise" abort the move with
        # the patch half rewired.
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


def _is_anchor(v: float) -> bool:
    """A default-rect coordinate that is a fraction of the window."""
    return 0.0 < v <= 1.0


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
        # port order captured at the start of optimize_layout
        self._port_order_before: Dict[str, List[Any]] = {}

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
            # x/y in (0, 1] anchor the class to the window (ezdac~ bottom-left);
            # larger values are absolute coordinates from a captured patch
            if mclass_rect and (_is_anchor(mclass_rect.x) or _is_anchor(mclass_rect.y)):
                if _is_anchor(mclass_rect.x):
                    x = float(mclass_rect.x * self.parent.width)
                if _is_anchor(mclass_rect.y):
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
                    # any push counts: pushes that cancel out leave the box
                    # where it started, still overlapping
                    moved = True
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
            iterations_performed = iteration + 1
            if not moved:
                break
        else:
            self._push_down(objects, overlapping, min_gap)

        return iterations_performed

    @staticmethod
    def _push_down(objects: List[Any], overlapping: Any, min_gap: float) -> None:
        """Clear overlaps the sweeps left, moving boxes down only.

        The sweeps can trade one overlap for another: a box pushed left is
        clamped at the margin and may land on a neighbour. Here each box, in
        reading order, drops below any earlier box it still overlaps. Every
        move increases y, so this always terminates overlap-free.
        """
        objects.sort(key=lambda o: (o.patching_rect.y, o.patching_rect.x))
        for i in range(1, len(objects)):
            r = objects[i].patching_rect
            moved = True
            while moved:
                moved = False
                for j in range(i):
                    rj = objects[j].patching_rect
                    if overlapping(r, rj):
                        r = Rect(r.x, rj.y + rj.h + min_gap, r.w, r.h)
                        moved = True
            objects[i].patching_rect = r

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
        self._port_order_before = before = self._port_order()
        self._full_layout()
        self._restore_port_order(before)
        # layouts and the overlap pass can run past the window; grow it so the
        # whole patch is visible when opened
        self._fit_window(list(self.parent._boxes))

    def _fit_window(self, boxes: List[Any]) -> None:
        """Grow the patcher window so every laid-out box is fully visible."""
        if not boxes:
            return
        max_x = max(b.patching_rect[0] + b.patching_rect[2] for b in boxes)
        max_y = max(b.patching_rect[1] + b.patching_rect[3] for b in boxes)
        rect = self.parent.rect
        x, y, w, h = rect[0], rect[1], rect[2], rect[3]
        new_w = max(w, max_x + self.pad)
        new_h = max(h, max_y + self.pad)
        if (new_w, new_h) != (w, h):
            self.parent.rect = Rect(x, y, new_w, new_h)

    def _port_order(self) -> Dict[str, List[Any]]:
        """``inlet``/``outlet`` boxes in port-number order: by x, then creation."""
        order: Dict[str, List[Any]] = {}
        for kind in ("inlet", "outlet"):
            ports = [b for b in self.parent._boxes if object_name(b) == kind]
            order[kind] = sorted(ports, key=lambda b: b.patching_rect[0])
        return order

    def _restore_port_order(self, order: Dict[str, List[Any]]) -> None:
        """Give ports back the left-to-right order they had before layout.

        Max numbers a patcher's ports by x position, so a layout that reorders
        them silently rewires every cord to the patcher. The boxes trade
        positions among themselves, so no new space is occupied.
        """
        for ports in order.values():
            if len(ports) < 2:
                continue
            slots = sorted((b.patching_rect.x, b.patching_rect.y) for b in ports)
            prev_x = None
            for box, (x, y) in zip(ports, slots):
                if prev_x is not None and x <= prev_x:
                    x = prev_x + 1.0  # equal x leaves the order undefined
                r = box.patching_rect
                box.patching_rect = Rect(x, y, r.w, r.h)
                prev_x = x

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


# objects that take audio or data out of a patch, laid out last
_PATCH_OUTPUTS = frozenset(
    {"dac~", "ezdac~", "mc.dac~", "mc.ezdac~", "outlet", "out~", "outport"}
)


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
        self._flow_levels: Dict[str, int] = {}  # Track hierarchical flow levels
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
        """Level per object along the flow.

        Vertical flow uses longest-path levels: each object sits one below its
        deepest input, so every cord points down (feedback cycles are broken
        by ignoring the cords that close them). Patch outputs (``dac~``,
        ``outlet``, ...) with no outgoing cords then go on the last level.
        Horizontal flow keeps shortest-path levels: Max draws cords from a
        box's bottom edge to the next one's top, so in a left-to-right layout
        the extra levels doubled the crossings. Unconnected objects follow on
        a level of their own.
        """
        if self.flow_direction == "vertical":
            levels = self._longest_path_levels(connections)
        else:
            levels = self._shortest_path_levels(connections)

        last = max(levels.values(), default=0)
        if self.flow_direction == "vertical":
            for obj_id in levels:
                obj = self.parent._objects.get(obj_id)
                if (
                    obj is not None
                    and object_name(obj) in _PATCH_OUTPUTS
                    and not connections[obj_id]["outputs"]
                ):
                    levels[obj_id] = last

        for obj_id in self.parent._objects:
            if obj_id not in levels:
                levels[obj_id] = last + 1
        return levels

    def _longest_path_levels(
        self, connections: Dict[str, Dict[str, List[str]]]
    ) -> Dict[str, int]:
        back = self._back_edges(connections)
        indegree = {
            o: sum(1 for i in c["inputs"] if (i, o) not in back)
            for o, c in connections.items()
        }
        levels = {o: 0 for o, n in indegree.items() if n == 0}
        ready = sorted(levels)
        while ready:
            node = ready.pop()
            for out in connections[node]["outputs"]:
                if (node, out) in back:
                    continue
                levels[out] = max(levels.get(out, 0), levels[node] + 1)
                indegree[out] -= 1
                if indegree[out] == 0:
                    ready.append(out)
        return levels

    @staticmethod
    def _shortest_path_levels(
        connections: Dict[str, Dict[str, List[str]]],
    ) -> Dict[str, int]:
        sources = [o for o, c in connections.items() if not c["inputs"]]
        if not sources and connections:
            fewest = min(len(c["inputs"]) for c in connections.values())
            sources = [o for o, c in connections.items() if len(c["inputs"]) == fewest]
        levels: Dict[str, int] = {}
        frontier, level = sources, 0
        while frontier:
            nxt: List[str] = []
            for obj_id in frontier:
                if obj_id not in levels:
                    levels[obj_id] = level
                    nxt.extend(
                        o for o in connections[obj_id]["outputs"] if o not in levels
                    )
            frontier, level = sorted(set(nxt)), level + 1
        return levels

    @staticmethod
    def _back_edges(
        connections: Dict[str, Dict[str, List[str]]],
    ) -> Set[Tuple[str, str]]:
        """Cords that close a cycle, found by depth-first search."""
        back: Set[Tuple[str, str]] = set()
        state: Dict[str, int] = {}  # 1 on the current path, 2 finished
        for root in connections:
            if root in state:
                continue
            stack = [(root, iter(connections[root]["outputs"]))]
            state[root] = 1
            while stack:
                node, outs = stack[-1]
                nxt = next(outs, None)
                if nxt is None:
                    state[node] = 2
                    stack.pop()
                elif state.get(nxt) == 1:
                    back.add((node, nxt))
                elif nxt not in state and nxt in connections:
                    state[nxt] = 1
                    stack.append((nxt, iter(connections[nxt]["outputs"])))
        return back

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
        sweeps: int = 8,
    ) -> List[Dict[int, List[str]]]:
        """Candidate orderings of each level, for ``_full_layout`` to judge.

        Each connected component keeps a contiguous block within a level, so
        independent subgraphs do not interleave. Within that, barycenter sweeps
        alternate down (by inputs) and up (by outputs), placing each object at
        the mean relative position of its neighbours on any level. The ordering
        with the fewest estimated crossings is kept. The original single
        downward pass is included, so the chosen layout is never worse than it.
        """
        if len(groups) < 2:
            return [groups]

        levels = sorted(groups)
        component = self._components(connections)
        candidates = [self._barycenter_once(groups, connections)]
        # with components kept apart, and without
        for blocked in (True, False):
            group = component if blocked else {}
            seed = {
                lv: sorted(groups[lv], key=lambda o: (group.get(o, 0), o))
                for lv in levels
            }
            candidates.append(self._sweep(seed, levels, connections, group, sweeps)[0])
        return candidates

    def _barycenter_once(
        self,
        groups: Dict[int, List[str]],
        connections: Dict[str, Dict[str, List[str]]],
    ) -> Dict[int, List[str]]:
        """One downward barycenter pass by previous-level inputs (the original).

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

    def _sweep(
        self,
        order: Dict[int, List[str]],
        levels: List[int],
        connections: Dict[str, Dict[str, List[str]]],
        component: Dict[str, int],
        sweeps: int,
    ) -> Tuple[Dict[int, List[str]], int]:
        """Barycenter sweeps from ``order``: the best ordering seen, and its cost."""
        best = {lv: list(ids) for lv, ids in order.items()}
        best_cost = self._count_crossings(best, levels, connections)

        for sweep in range(sweeps):
            down = sweep % 2 == 0
            neighbours = "inputs" if down else "outputs"
            for lv in levels[1:] if down else levels[-2::-1]:
                rel = {
                    o: idx / max(len(ids) - 1, 1)
                    for ids in order.values()
                    for idx, o in enumerate(ids)
                }
                current = {o: idx for idx, o in enumerate(order[lv])}

                def key(o: str) -> Tuple[int, float, int]:
                    near = [
                        rel[n]
                        for n in connections.get(o, {}).get(neighbours, [])
                        if n in rel
                    ]
                    bary = sum(near) / len(near) if near else rel[o]
                    return (component.get(o, 0), bary, current[o])

                order[lv] = sorted(order[lv], key=key)
            cost = self._count_crossings(order, levels, connections)
            if cost < best_cost:
                best, best_cost = {lv: list(ids) for lv, ids in order.items()}, cost
        return best, best_cost

    @staticmethod
    def _components(connections: Dict[str, Dict[str, List[str]]]) -> Dict[str, int]:
        """Connected-component index per object, numbered in first-seen order."""
        component: Dict[str, int] = {}
        for start in connections:
            if start in component:
                continue
            index, stack = len(set(component.values())), [start]
            while stack:
                node = stack.pop()
                if node in component:
                    continue
                component[node] = index
                conn = connections.get(node, {})
                stack.extend(conn.get("inputs", []) + conn.get("outputs", []))
        return component

    def _count_crossings(
        self,
        order: Dict[int, List[str]],
        levels: List[int],
        connections: Dict[str, Dict[str, List[str]]],
    ) -> int:
        """Cord crossings if objects were placed in ``order``.

        Uses the positions this manager would assign, and Max's cord geometry
        (outlet on the bottom edge to inlet on the top edge), so the count is
        right for both flow directions and for cords spanning several levels.
        """
        if self.flow_direction == "vertical":
            rects = self._calculate_vertical_positions(order, self.pad)
        else:
            rects = self._calculate_horizontal_positions(order, self.pad)
        segs = [
            (
                (rects[o][0] + rects[o][2] / 2, rects[o][1] + rects[o][3]),
                (rects[d][0] + rects[d][2] / 2, rects[d][1]),
                o,
                d,
            )
            for o in rects
            for d in connections.get(o, {}).get("outputs", [])
            if d in rects
        ]
        return _count_segment_crossings(segs)

    def _candidate_positions(self) -> List[Dict[str, Rect]]:
        """Positions for each candidate ordering of the flow levels."""
        connections = self._analyze_connections()
        levels = self._calculate_flow_levels(connections)
        groups = self._group_by_level(levels)
        place = (
            self._calculate_vertical_positions
            if self.flow_direction == "vertical"
            else self._calculate_horizontal_positions
        )
        return [
            place(order, self.pad)
            for order in self._minimize_crossings(groups, connections)
        ]

    def _calculate_horizontal_positions(
        self, groups: Dict[int, List[str]], pad: float
    ) -> Dict[str, Rect]:
        """Positions for left-to-right flow: one column per level."""
        return self._place_levels(groups, pad, along=0)

    def _calculate_vertical_positions(
        self, groups: Dict[int, List[str]], pad: float
    ) -> Dict[str, Rect]:
        """Positions for top-to-bottom flow: one row per level."""
        return self._place_levels(groups, pad, along=1)

    def _place_levels(
        self, groups: Dict[int, List[str]], pad: float, along: int
    ) -> Dict[str, Rect]:
        """Lay levels out along axis ``along`` (0 = x, 1 = y), sized by their boxes.

        Each level is as deep as its largest box, and its boxes stack across
        the other axis by their real sizes, centred in the window when they
        fit. Spare window space spreads the levels, up to 100 px apart. Nothing
        is clamped to the window: ``optimize_layout`` grows it to fit.
        """
        across = 1 - along
        window = (float(self.parent.width), float(self.parent.height))

        def dims(obj_id: str) -> Tuple[float, float]:
            obj = self.parent._objects.get(obj_id)
            return (
                self.box_dims(obj)
                if obj is not None
                else (
                    float(self.box_width),
                    float(self.box_height),
                )
            )

        levels = sorted(groups)
        depth = {
            lv: max((dims(o)[along] for o in groups[lv]), default=0.0) for lv in levels
        }
        spare = window[along] - 2 * pad - sum(depth.values())
        gap = max(pad, min(spare / max(len(levels) - 1, 1), 100.0))

        positions: Dict[str, Rect] = {}
        offset = pad
        for lv in levels:
            sizes = [dims(o) for o in groups[lv]]
            extent = sum(sz[across] for sz in sizes) + pad * (len(sizes) - 1)
            start = max(pad, (window[across] - extent) / 2)
            for obj_id, (w, h) in zip(groups[lv], sizes):
                xy = [0.0, 0.0]
                xy[along], xy[across] = offset, start
                positions[obj_id] = Rect(xy[0], xy[1], w, h)
                start += (w, h)[across] + pad
            offset += depth[lv] + gap
        return positions

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

    def _place(self, positions: Dict[str, Rect]) -> None:
        """Apply ``positions``, keeping each object's own size, then de-overlap.

        The computed position carries the manager's uniform grid size; each
        object keeps its own w/h so UI objects are not squashed (L2).
        """
        for obj_id, position in positions.items():
            if obj_id in self.parent._objects:
                obj = self.parent._objects[obj_id]
                w, h = self.box_dims(obj)
                obj.patching_rect = Rect(position[0], position[1], w, h)
        self.prevent_overlaps()
        # judge the layout as optimize_layout will leave it
        self._restore_port_order(self._port_order_before)

    def _placed_crossings(self) -> int:
        """Crossings between the patch's cords as currently placed."""
        segs = []
        for line in self.parent._lines:
            src = self.parent._objects.get(line.src)
            dst = self.parent._objects.get(line.dst)
            if src is None or dst is None:
                continue
            a, b = src.patching_rect, dst.patching_rect
            segs.append(
                (
                    (a[0] + a[2] / 2, a[1] + a[3]),
                    (b[0] + b[2] / 2, b[1]),
                    line.src,
                    line.dst,
                )
            )
        return _count_segment_crossings(segs)

    def _full_layout(self) -> None:
        """Perform full layout optimization based on signal flow analysis."""
        if len(self.parent._objects) < 2:
            return  # Nothing to optimize

        # Place each candidate ordering for real, since prevent_overlaps can
        # move boxes after placement, and keep the one with fewest crossings.
        best: Optional[Dict[str, Rect]] = None
        best_cost = -1
        for candidate in self._candidate_positions():
            self._place(candidate)
            cost = self._placed_crossings()
            if best is None or cost < best_cost:
                best_cost = cost
                best = {i: o.patching_rect for i, o in self.parent._objects.items()}
        for obj_id, rect in (best or {}).items():
            self.parent._objects[obj_id].patching_rect = rect


_Point = Tuple[float, float]


def _count_segment_crossings(segs: List[Tuple[_Point, _Point, str, str]]) -> int:
    """Pairs of cords ``(start, end, src_id, dst_id)`` that cross.

    Cords sharing an object are not counted: they meet at a port.
    """

    def side(a: _Point, b: _Point, c: _Point) -> float:
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    total = 0
    for i, (p1, p2, o1, d1) in enumerate(segs):
        for p3, p4, o2, d2 in segs[i + 1 :]:
            if {o1, d1} & {o2, d2}:
                continue
            if (
                side(p1, p2, p3) * side(p1, p2, p4) < 0
                and side(p3, p4, p1) * side(p3, p4, p2) < 0
            ):
                total += 1
    return total


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

_ON_INVALID = ("warn", "raise", "ignore")


def _top_left(boxes: List["AbstractBox"]) -> Tuple[float, float]:
    return (
        min(float(b.patching_rect[0]) for b in boxes),
        min(float(b.patching_rect[1]) for b in boxes),
    )


def _shift(r: Any, dx: float, dy: float) -> Rect:
    return Rect(float(r[0]) + dx, float(r[1]) + dy, float(r[2]), float(r[3]))


def _within_gap(a: Any, b: Any, gap: float) -> bool:
    return bool(
        a[0] < b[0] + b[2] + gap
        and b[0] < a[0] + a[2] + gap
        and a[1] < b[1] + b[3] + gap
        and b[1] < a[1] + a[3] + gap
    )


def _resolve_on_invalid(
    validate_connections: Optional[bool],
    on_invalid: Optional[str],
    parent: Optional["AbstractPatcher"],
) -> str:
    """The connection policy from the two spellings, else the parent's, else warn."""
    implied = {True: "raise", False: "ignore", None: None}[validate_connections]
    if on_invalid is not None:
        if on_invalid not in _ON_INVALID:
            raise ValueError(
                f"on_invalid must be one of {_ON_INVALID}, not {on_invalid!r}"
            )
        if implied is not None and implied != on_invalid:
            raise ValueError(
                f"validate_connections={validate_connections} conflicts with "
                f"on_invalid={on_invalid!r}"
            )
        return on_invalid
    if implied is not None:
        return implied
    return cast(str, getattr(parent, "_on_invalid", "warn"))


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
        validate_connections: Shorthand for ``on_invalid``: ``True`` means
            ``"raise"``, ``False`` means ``"ignore"``.
        on_invalid: What an invalid connection does: ``"warn"`` (log it and
            add the cord), ``"raise"`` (``InvalidConnectionError``), or
            ``"ignore"`` (no check). Defaults to the parent patcher's policy,
            else ``"warn"``.
        validate_attrs: Whether to warn (UserWarning) when an object is given a
            keyword that is not a known attribute for its Max class -- catches
            typos like ``inital=`` for ``initial=``. Defaults to the parent
            patcher's setting, else on.
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
        validate_connections: Optional[bool] = None,
        on_invalid: Optional[str] = None,
        validate_attrs: Optional[bool] = None,
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
        # Set by add_v8_bridge(); save() then writes the js2max runtime beside
        # the patch. Only when asked for, so an ordinary save never drops a
        # stray .js file next to someone's patcher.
        self._needs_js2max_runtime = False
        self._flow_direction = flow_direction
        self._cluster_connected = cluster_connected
        self._num_dimensions = num_dimensions
        self._dimension_spacing = dimension_spacing
        self._layout_mgr: AbstractLayoutManager = self.set_layout_mgr(layout)
        self._auto_hints = auto_hints
        self._on_invalid = _resolve_on_invalid(validate_connections, on_invalid, parent)
        self._validate_connections = self._on_invalid != "ignore"
        if validate_attrs is None:
            validate_attrs = getattr(parent, "_validate_attrs", True)
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
        """Find all boxes whose text (or, for a UI box, maxclass) matches a pattern.

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
            text = getattr(box, "text", "") or object_name(box)
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
        # Indexed rather than ``.w`` so a hand-assigned plain list still works;
        # ``from_dict`` normalizes loaded rects to Rect, but nothing stops a
        # caller assigning ``patcher.rect = [0, 0, 640, 480]`` directly.
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
        # JSON has no tuple type, so a loaded window rect arrives as a list.
        # Restore it to a Rect for parity with a programmatically built patcher;
        # Rect is a NamedTuple, so this re-serializes identically.
        if "rect" in patcher.__dict__:
            patcher.__dict__["rect"] = as_rect(patcher.__dict__["rect"])

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
        """cascade convert py2max objects to dicts.

        Idempotent: rendering twice produces the same patcher, not two copies of
        it. That matters because ``to_dict()`` renders on its own behalf, so a
        ``save_as()`` renders once for its own log line and again underneath --
        and because a caller has no way to know whether a render already
        happened.

        ``self.boxes`` used to be *appended* to while ``self.lines`` was
        rebuilt, so a second render duplicated every box and no line. Nothing in
        the repository passed ``reset_on_render=False``, which is the only way
        to reach that path, so the asymmetry had never bitten -- but it made
        rendering order-dependent in exactly the way ``to_dict()`` was.
        """
        # Flush deferred associated comments here (not only in save()) so every
        # serialization entry point -- save, save_as, to_json -- emits them.
        # Idempotent: _process_pending_comments clears its queue after running.
        self._process_pending_comments()
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
        self._arrange()

        # Process pending comments after layout optimization
        self._process_pending_comments()

    def optimize_layout_subset(self, boxes: Iterable["AbstractBox"]) -> None:
        """Lay out only ``boxes`` and the cords between them.

        Every other box stays put, so logic can be arranged around fixed UI (a
        ``bpatcher`` view, a presentation area). The group keeps its top-left
        corner, and moves down as a whole if it then overlaps a fixed box.
        Like ``optimize_layout``, this is a batch operation.
        """
        self._arrange_subset(list(boxes))
        self._process_pending_comments()

    def _arrange(self) -> None:
        """Run the layout manager, then dock params if enabled."""
        if hasattr(self._layout_mgr, "optimize_layout"):
            self._layout_mgr.optimize_layout()

        # Dock value/UI params next to the object they drive (opt-in).
        if self._param_placement and hasattr(self._layout_mgr, "place_params"):
            self._layout_mgr.place_params()

    def _arrange_subset(self, subset: List["AbstractBox"]) -> None:
        """Lay out ``subset`` alone, then put it back clear of the other boxes."""
        ids = {b.id for b in subset}
        if not ids:
            return
        fixed = [b for b in self._boxes if b.id not in ids]
        corner = _top_left(subset)
        saved = (self._boxes, self._objects, self._lines)
        self._boxes = [b for b in self._boxes if b.id in ids]
        self._objects = {k: v for k, v in self._objects.items() if k in ids}
        self._lines = [ln for ln in self._lines if ln.src in ids and ln.dst in ids]
        try:
            self._arrange()
        finally:
            self._boxes, self._objects, self._lines = saved

        # back to the original corner, then down until clear of fixed boxes
        x, y = _top_left(subset)
        dx, dy = corner[0] - x, corner[1] - y
        gap = float(self._layout_mgr.pad)
        while True:
            moved = [_shift(b.patching_rect, dx, dy) for b in subset]
            hits = [
                f.patching_rect
                for f in fixed
                if any(_within_gap(r, f.patching_rect, gap) for r in moved)
            ]
            if not hits:
                break
            dy += max(h[1] + h[3] for h in hits) + gap - min(r[1] for r in moved)
        for box, rect in zip(subset, moved):
            box.patching_rect = rect

    def lint(self) -> "List[Finding]":
        """Return patch-level lint findings (errors and warnings), errors first.

        Checks connection validity, out-of-range ports, orphaned patchlines,
        duplicate IDs, overlapping objects, off-canvas objects, unknown object
        classes, and inlet/outlet boxes out of creation order. See
        :mod:`py2max.lint`.
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
W_PORT_ORDER = "W-PORT-ORDER"


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
    if getattr(box, "maxclass", None) in DYNAMIC_IO_MAXCLASSES:
        # ports come from code or a loaded file, so trust the declared counts
        n_in, n_out = getattr(box, "numinlets", None), getattr(box, "numoutlets", None)
    else:
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

    # Max numbers inlet/outlet boxes by x, not creation order; a mismatch
    # silently swaps the ports of the patcher (or abstraction) they belong to.
    for kind in ("inlet", "outlet"):
        ports = [b for b in boxes if object_name(b) == kind]
        for prev, cur in zip(ports, ports[1:]):
            if float(cur.patching_rect[0]) <= float(prev.patching_rect[0]):
                findings.append(
                    Finding(
                        W_PORT_ORDER,
                        WARNING,
                        f"{kind} {cur.id!r} is not right of {prev.id!r}, which was "
                        f"created before it; Max numbers {kind}s by x position",
                        obj_id=qid(cur.id),
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

    def _round_rect(owner: Any, attr: str) -> int:
        """Round a rect's coords to ints. Returns 1 if any was non-integer.

        ``Rect`` is a NamedTuple and therefore immutable, so a rounded rect is
        rebuilt and assigned back to the owner rather than mutated in place. A
        plain list is likewise replaced rather than sliced, so both storage
        forms take the same path.
        """
        rect = getattr(owner, attr, None)
        if rect is None:
            return 0
        try:
            coords = list(rect)
        except TypeError:
            return 0
        if len(coords) != 4:
            return 0
        if not any(isinstance(v, float) and not v.is_integer() for v in coords):
            return 0

        rounded = [int(round(float(v))) for v in coords]
        # Preserve the storage form: Rect in, Rect out; list in, list out.
        setattr(owner, attr, Rect(*rounded) if isinstance(rect, Rect) else rounded)
        return 1

    changed = 0
    for box in patcher._boxes:
        changed += _round_rect(box, "patching_rect")

        if hasattr(box, "presentation_rect"):
            changed += _round_rect(box, "presentation_rect")

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
TEXT_LINE_HEIGHT = 15
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


def _wrap_lines(text: str, width: float, x_offset: float) -> List[str]:
    """Split ``text`` into lines that fit ``width`` px, keeping explicit breaks."""
    room = width - 2 * x_offset
    lines: List[str] = []
    for para in text.split("\n"):
        line = ""
        for word in para.split():
            trial = f"{line} {word}" if line else word
            if line and text_width(trial, TEXT_FONT_SIZE) > room:
                lines.append(line)
                line = word
            else:
                line = trial
        lines.append(line)
    return lines


def _multiline_text_svg(
    x: float, y: float, lines: List[str], color: str, x_offset: float = 5.0
) -> str:
    return "\n".join(
        f'<text x="{x + x_offset}" '
        f'y="{y + 4 + TEXT_FONT_SIZE + i * TEXT_LINE_HEIGHT}" '
        f'font-family="{TEXT_FONT_FAMILY}" font-size="{TEXT_FONT_SIZE}" '
        f'fill="{color}">{_escape_text(line)}</text>'
        for i, line in enumerate(lines)
    )


def _render_box(box: AbstractBox, show_ports: bool = True) -> str:
    """Render a single box (shape, label, and ports) to SVG."""
    r = _rect_of(box)
    if r is None:
        return ""
    x, y, w, h = r
    maxclass = getattr(box, "maxclass", "newobj")
    fill, stroke, text_color = _box_colors(box)

    # Max wraps comment text and grows the box to fit it.
    lines: List[str] = []
    if maxclass == "comment":
        lines = _wrap_lines(_get_box_text(box), w, 5.0)
        if len(lines) > 1:
            h = max(h, len(lines) * TEXT_LINE_HEIGHT + 8)

    parts = [_render_shape(box, maxclass, x, y, w, h, fill, stroke)]

    if len(lines) > 1:
        parts.append(_multiline_text_svg(x, y, lines, text_color))
    # Text label -- skipped for icon-only widgets whose glyph is the content.
    elif maxclass not in _ICON_ONLY:
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


#: Filename of the js2max drop-in build, as a patch refers to it.
V8_BUNDLE = "js2max.v8.js"


class _JS2MaxRuntimeStub:  # pragma: no cover - excluded from the single file
    """Placeholder: the js2max runtime is package *data*, not code.

    The two bundles are 160 KB of built JavaScript. A single file whose point is
    to be one readable, dependency-free module cannot carry them, and there is
    nothing to amalgamate in any case -- they are assets, not Python.

    ``add_v8_bridge()`` still builds the box, so a patch can be generated here
    and the runtime placed beside it by hand. Pass its filename with
    ``add_v8_bridge(bundle=...)`` and nothing is installed for you.
    """

    V8_BUNDLE = V8_BUNDLE

    @staticmethod
    def path(flavor: str = "v8") -> Any:
        raise NotImplementedError(_JS2MaxRuntimeStub._message)

    @staticmethod
    def install(dest: Any, flavor: str = "v8") -> Any:
        raise NotImplementedError(_JS2MaxRuntimeStub._message)

    _message = (
        "the js2max runtime is not bundled in the single-file edition of "
        "py2max; install the full package (pip install py2max), or copy "
        "js2max.v8.js beside the patch yourself and name it with "
        "add_v8_bridge(bundle=...)"
    )


js2max_runtime = _JS2MaxRuntimeStub()


# Aliases from stripped intra-package imports (e.g. `from .lint import lint as _lint_patch`).
CURATED = MAXCLASS_DEFAULTS
_lint = lint
_lint_patch = lint
