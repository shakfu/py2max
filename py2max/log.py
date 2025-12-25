"""Logging and error handling utilities for py2max.

This module provides comprehensive logging configuration and utilities for
debugging, error tracking, and performance monitoring across the py2max library.

Features:
    - Color-coded console output with custom formatting
    - Domain-specific loggers for different modules
    - Context managers for operation tracking
    - Error logging utilities with stack traces
    - Configurable log levels via environment variables

Environment Variables:
    DEBUG: Set to '1' to enable DEBUG level logging (default: '1')
    COLOR: Set to '1' to enable colored output (default: '1')
    PY2MAX_LOG_FILE: Optional log file path for persistent logging
    PY2MAX_LOG_LEVEL: Override log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

Example:
    >>> from py2max.log import get_logger
    >>> logger = get_logger(__name__)
    >>> logger.info("Creating patcher")
    >>> logger.debug("Adding box with id: cycle_1")
"""

import contextlib
import datetime
import logging
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Optional

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
DEBUG = getenv("DEBUG", default=True)
COLOR = getenv("COLOR", default=True)
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


# Global flag to track if logging has been configured
_logging_configured = False


def config(name: str) -> logging.Logger:
    """Configure and return a logger with custom formatting.

    This function sets up the global logging configuration on first call,
    then returns named loggers for specific modules. Supports both console
    and optional file output.

    Args:
        name: Logger name (typically __name__ from calling module).

    Returns:
        Configured logger instance for the specified name.

    Example:
        >>> logger = config(__name__)
        >>> logger.info("Application started")
    """
    global _logging_configured

    if not _logging_configured:
        handlers: list[logging.Handler] = []

        # Console handler with color formatting
        strm_handler = logging.StreamHandler()
        strm_handler.setFormatter(CustomFormatter(use_color=COLOR))
        handlers.append(strm_handler)

        # Optional file handler
        if LOG_FILE:
            log_path = Path(LOG_FILE)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_path, mode="a")
            file_handler.setFormatter(CustomFormatter(use_color=False))
            handlers.append(file_handler)

        # Get log level from environment or default
        level = getattr(logging, (LOG_LEVEL or "INFO").upper(), logging.INFO)

        logging.basicConfig(
            level=level,
            handlers=handlers,
            force=True,  # Override any existing configuration
        )
        _logging_configured = True

    return logging.getLogger(name)


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger for the specified module.

    Convenience function that wraps config() for clearer API.

    Args:
        name: Logger name (typically __name__ from calling module).

    Returns:
        Configured logger instance.

    Example:
        >>> from py2max.log import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.debug("Processing object: cycle~")
    """
    return config(name)


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
def log_operation(logger: logging.Logger, operation: str, **kwargs: Any):
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
    "config",
    "get_logger",
    "log_exception",
    "log_warning_once",
    "log_operation",
    "LoggerMixin",
    "CustomFormatter",
]
