"""Logging and error handling utilities for py2max.

This module provides comprehensive logging configuration and utilities for
debugging, error tracking, and performance monitoring across the py2max library.

Features:
    - Color-coded console output with custom formatting (opt-in)
    - Domain-specific loggers for different modules
    - Context managers for operation tracking
    - Error logging utilities with stack traces

py2max is a library, so importing it does not configure logging and prints
nothing: the ``py2max`` logger carries a ``NullHandler`` and the application
decides where records go. Call :func:`setup_logging` for py2max's colored console
output (the CLI does this), or configure the ``py2max`` logger yourself with the
standard library, as with any other package.

Environment Variables:
    PY2MAX_DEBUG: Set to '1' to call setup_logging(level='DEBUG') at import.
    PY2MAX_LOG_LEVEL: Log level for setup_logging; also enables it at import if
        set (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    PY2MAX_LOG_FILE: Optional log file path; also enables logging at import.
    PY2MAX_COLOR: Set to '0' to disable ANSI colors in py2max's own handler.

Example:
    >>> from py2max.log import get_logger
    >>> logger = get_logger(__name__)
    >>> logger.info("Creating patcher")   # silent unless configured

    >>> from py2max.log import setup_logging
    >>> setup_logging("INFO")             # opt in to py2max's console output
"""

import contextlib
import datetime
import logging
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Iterator, Optional

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

__all__ = [
    "LOGGER_NAME",
    "config",
    "setup_logging",
    "get_logger",
    "log_exception",
    "log_warning_once",
    "log_operation",
    "LoggerMixin",
    "CustomFormatter",
]
