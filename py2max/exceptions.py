"""Exception hierarchy for py2max.

This module defines a comprehensive exception hierarchy for error handling
throughout the py2max library. All exceptions inherit from Py2MaxError for
easy catching of library-specific errors.

Exception Hierarchy:
    Py2MaxError (base)
    ├── ValidationError
    │   ├── InvalidConnectionError (connections between objects)
    │   ├── InvalidObjectError (invalid object configuration)
    │   └── InvalidPatchError (invalid patcher state)
    ├── ConfigurationError
    │   ├── LayoutError (layout manager issues)
    │   └── DatabaseError (database configuration issues)
    ├── IOError (subclass of built-in IOError)
    │   ├── PatcherIOError (file I/O errors)
    │   └── MaxRefError (maxref.xml parsing errors)
    └── InternalError (unexpected internal errors)

Example:
    >>> from py2max.exceptions import InvalidConnectionError
    >>> try:
    ...     p.add_line(osc, gain, outlet=999)
    ... except InvalidConnectionError as e:
    ...     print(f"Connection error: {e}")
"""

from typing import Any, Optional


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
        context = {}
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

__all__ = [
    "Py2MaxError",
    "ValidationError",
    "InvalidConnectionError",
    "InvalidObjectError",
    "InvalidPatchError",
    "ConfigurationError",
    "LayoutError",
    "DatabaseError",
    "PatcherIOError",
    "MaxRefError",
    "InternalError",
]
