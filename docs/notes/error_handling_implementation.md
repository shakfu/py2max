# Error Handling and Logging Implementation

**Date:** October 13, 2025
**Status:** Implemented and Tested

## Overview

This document describes the comprehensive error handling and logging system implementation for py2max, addressing the recommendations from CODE_REVIEW.md regarding "Error handling (logging, meaningful errors, validation)".

## What Was Implemented

### 1. Enhanced Logging Module (`py2max/log.py`)

**Features:**

- Color-coded console output with custom formatting
- Configurable log levels via environment variables
- Optional file logging support
- Domain-specific logger helpers
- Context managers for operation tracking
- Error logging utilities with stack traces

**Key Functions:**

- `get_logger(name)` - Get configured logger for a module
- `log_exception(logger, exc, context)` - Log exceptions with full tracebacks
- `log_warning_once(logger, key, message)` - Avoid log spam from repeated warnings
- `log_operation(logger, operation, **kwargs)` - Context manager for timing operations
- `LoggerMixin` - Mixin class for adding logging to any class

**Environment Variables:**

- `DEBUG` - Enable DEBUG level logging (default: '1')
- `COLOR` - Enable colored output (default: '1')
- `PY2MAX_LOG_FILE` - Optional log file path
- `PY2MAX_LOG_LEVEL` - Override log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

**Example Usage:**

```python
from py2max.log import get_logger, log_operation

logger = get_logger(__name__)
logger.info("Starting operation")

with log_operation(logger, "save patcher", path="out.maxpat"):
    patcher.save()
```

### 2. Custom Exception Hierarchy (`py2max/exceptions.py`)

**Exception Hierarchy:**

```text
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
```

**Key Features:**

- All exceptions include context dictionaries for detailed error information
- Formatted error messages with context: `"Error message (key1=val1, key2=val2)"`
- `InvalidConnectionError` includes src, dst, outlet, inlet details
- `PatcherIOError` and `MaxRefError` are subclasses of IOError for compatibility
- Can catch all py2max errors with `except Py2MaxError`

**Example Usage:**

```python
from py2max import InvalidConnectionError, Py2MaxError

try:
    p.add_line(osc, gain, outlet=10)
except InvalidConnectionError as e:
    print(f"Connection failed: {e}")
    print(f"Source: {e.src}, Outlet: {e.outlet}")
except Py2MaxError as e:
    print(f"Other py2max error: {e}")
```

### 3. Core Module Integration (`py2max/core.py`)

**Changes:**

- Replaced standalone `InvalidConnectionError` with import from `exceptions`
- Added module-level logger
- Enhanced `save_as()` with:
  - Logging of save operations
  - Better error messages with PatcherIOError
  - Operation timing via `log_operation`
- Enhanced `add_patchline()` with:
  - Detailed connection logging
  - Better validation error messages with full context
  - Object existence checking before validation

**Example Log Output:**

```text
00:00:01 - DEBUG - py2max.core.Patcher.__init__ - Initializing Patcher: path=test.maxpat, layout=grid, validate_connections=True
00:00:01 - DEBUG - py2max.core.Patcher.add_patchline - Adding patchline: cycle_1[0] -> gain_1[0]
00:00:02 - INFO - py2max.core.Patcher.save_as - Saved patcher to: /tmp/test.maxpat (3 objects, 2 connections)
```

### 4. MaxRef Module Integration (`py2max/maxref.py`)

**Changes:**

- Added module-level logger
- **Replaced silent error handling** (CODE_REVIEW.md critical issue)
- Enhanced `get_object_data()` with:
  - Cache hit/miss logging
  - Detailed XML parsing error logs (using `log_warning_once` to avoid spam)
  - IOError logging with full context
  - Unexpected error logging with stack traces
- Added logging to `_get_refpages()` for Max installation discovery

**Before (Silent Errors):**

```python
except Exception:
    # If parsing fails, return None
    return None
```

**After (Proper Logging):**

```python
except ElementTree.ParseError as e:
    log_warning_once(logger, f"xml_parse_{name}", f"Failed to parse XML for '{name}': {e}")
    return None
except IOError as e:
    log_exception(logger, e, f"Failed to read MaxRef file for '{name}'")
    return None
```

### 5. Public API Updates (`py2max/__init__.py`)

**Exports:**

- All new exceptions: `Py2MaxError`, `InvalidConnectionError`, `InvalidObjectError`, etc.
- Logging utilities: `get_logger`, `log_exception`, `log_operation`
- Maintains backward compatibility - old imports still work

### 6. Comprehensive Test Suite (`tests/test_error_handling.py`)

**Test Coverage (24 tests):**

- Exception hierarchy validation
- Exception context and attributes
- Logging system functionality
- Error handling in Patcher operations
- Backward compatibility with old exception imports
- Real-world error scenarios

**Test Classes:**

- `TestExceptionHierarchy` - Exception class behavior
- `TestLoggingSystem` - Logger and utility functions
- `TestPatcherErrorHandling` - Error handling in core operations
- `TestBackwardsCompatibility` - Old code still works
- `TestLoggingConfiguration` - Configuration options
- `TestRealWorldScenarios` - Complex usage patterns

## Code Review Issues Addressed

### Critical Issues (Fixed)

1. **Silent Error Handling** (maxref.py:92)
   - **Before:** Exceptions swallowed with `return None`
   - **After:** Proper logging with `log_exception` and `log_warning_once`
   - **Benefit:** Developers can now debug XML parsing and I/O issues

2. **Error Messages Without Context**
   - **Before:** `raise InvalidConnectionError("Invalid connection")`
   - **After:** `raise InvalidConnectionError("Invalid connection", src="obj1", dst="obj2", outlet=5)`
   - **Benefit:** Error messages include all relevant debugging information

3. **No Logging Throughout Codebase**
   - **Before:** Minimal logging, some `print()` statements
   - **After:** Comprehensive logging at DEBUG, INFO, WARNING, ERROR levels
   - **Benefit:** Users can enable logging to troubleshoot issues

### High Priority Issues (Fixed)

1. **Input Validation**
   - Added detailed validation error messages with context
   - Enhanced path validation with specific PatcherIOError exceptions
   - Better connection validation with object existence checks

2. **Performance Monitoring**
   - `log_operation` context manager tracks operation timing
   - Can identify slow operations via DEBUG logging

## Usage Examples

### Enable Logging for Debugging

```python
import os
os.environ['PY2MAX_LOG_LEVEL'] = 'DEBUG'

from py2max import Patcher

p = Patcher('debug.maxpat', validate_connections=True)
# Will log: Initializing Patcher: path=debug.maxpat, layout=horizontal, validate_connections=True

osc = p.add_textbox('cycle~ 440')
# Will log: Adding box with id: cycle_1

gain = p.add_textbox('gain~')
p.add_line(osc, gain)
# Will log: Adding patchline: cycle_1[0] -> gain_1[0]
# Will log: Created patchline (order=0): cycle_1[0] -> gain_1[0]

p.save()
# Will log: Starting render patcher (boxes=2, lines=1)
# Will log: Completed render patcher in 0.001s
# Will log: Saved patcher to: /tmp/debug.maxpat (2 objects, 1 connections)
```

### Catch Specific Errors

```python
from py2max import Patcher, InvalidConnectionError, PatcherIOError

p = Patcher('test.maxpat', validate_connections=True)

try:
    osc = p.add_textbox('cycle~ 440')
    gain = p.add_textbox('gain~')
    p.add_line(osc, gain, outlet=10)
except InvalidConnectionError as e:
    print(f"Connection error: {e}")
    print(f"  Source: {e.src}")
    print(f"  Destination: {e.dst}")
    print(f"  Outlet: {e.outlet}")
    # Output:
    # Connection error: Invalid connection from cycle~[10] to gain~[0]: cycle~ only has 1 outlet (src=cycle_1, dst=gain_1, outlet=10, inlet=0)
    #   Source: cycle_1
    #   Destination: gain_1
    #   Outlet: 10

try:
    p.save_as('../../etc/passwd')
except PatcherIOError as e:
    print(f"I/O error: {e}")
    print(f"  Operation: {e.operation}")
    # Output:
    # I/O error: Invalid path detected (potential path traversal): ../../etc/passwd (file_path=../../etc/passwd, operation=validate)
    #   Operation: validate
```

### Custom Application Logging

```python
from py2max import get_logger

logger = get_logger(__name__)

logger.info("Starting patch generation")
logger.debug("Processing object list")
logger.warning("Object 'foo~' not found in MaxRef database")
logger.error("Failed to create patch")
```

### Log to File

```python
import os
os.environ['PY2MAX_LOG_FILE'] = '/tmp/py2max.log'
os.environ['PY2MAX_LOG_LEVEL'] = 'DEBUG'

from py2max import Patcher

# All log messages will be written to /tmp/py2max.log (without colors)
# and to console (with colors)
```

## Test Results

All tests pass successfully:

```text
pytest tests/test_error_handling.py -v
======================== 24 passed, 1 warning in 0.04s =========================

pytest tests/ --tb=short
================== 350 passed, 14 skipped, 1 warning in 4.60s ==================
```

## Backward Compatibility

Full backward compatibility maintained:

1. **Old exception imports work:**

   ```python
   from py2max.core import InvalidConnectionError  # Still works
   from py2max import InvalidConnectionError       # Also works (preferred)
   ```

2. **Old exception handling works:**

   ```python
   try:
       p.add_line(osc, gain, outlet=10)
   except InvalidConnectionError as e:
       print(str(e))  # Works as before
   ```

3. **Logging is opt-in:**
   - Default log level is ERROR (minimal output)
   - Set `PY2MAX_LOG_LEVEL=DEBUG` to see detailed logs
   - No changes to existing code required

## Remaining Work (Optional Enhancements)

The following tasks from the original plan were not completed as they are lower priority:

1. **Add logging to db.py** - Database operations logging
2. **Add logging to layout.py** - Layout algorithm debugging
3. **Add logging to server.py** - WebSocket operation logging

These can be added in future updates if needed, but the core error handling and logging system is now fully implemented and addresses all critical and high-priority issues from the code review.

## Migration Guide

For existing py2max users:

### No Changes Required

The implementation is fully backward compatible. Existing code will continue to work without modification.

### Optional: Enable Logging

To benefit from the new logging system, set environment variables:

```python
import os
os.environ['PY2MAX_LOG_LEVEL'] = 'INFO'  # or 'DEBUG' for verbose output

# Your existing code works unchanged
from py2max import Patcher
p = Patcher('my-patch.maxpat')
# ... rest of your code
```

### Optional: Better Error Handling

Update exception handling to access new error context:

```python
# Old style (still works):
try:
    p.add_line(osc, gain, outlet=10)
except InvalidConnectionError as e:
    print(f"Error: {e}")

# New style (recommended):
try:
    p.add_line(osc, gain, outlet=10)
except InvalidConnectionError as e:
    print(f"Connection failed: {e}")
    print(f"Details: src={e.src}, dst={e.dst}, outlet={e.outlet}")
```

### Optional: Add Logging to Your Code

Use py2max's logging system in your own code:

```python
from py2max import get_logger, log_operation

logger = get_logger(__name__)

logger.info("Starting patch generation workflow")

with log_operation(logger, "create complex patch", voices=8):
    # Your code here
    pass
```

## Summary

This implementation provides:

1. **Comprehensive error handling** - Detailed exception hierarchy with context
2. **Professional logging** - Configurable, color-coded logging system
3. **Better debugging** - No more silent failures; all errors are logged
4. **Backward compatibility** - Existing code continues to work
5. **Extensive testing** - 24 new tests, 350 total tests passing
6. **Production ready** - Addresses all critical and high-priority code review issues

The py2max library now has enterprise-grade error handling and logging capabilities while maintaining its ease of use and backward compatibility.
