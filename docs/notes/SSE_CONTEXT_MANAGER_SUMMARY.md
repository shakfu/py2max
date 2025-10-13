# SSE Live Preview - Context Manager Implementation

## Overview

Added context manager support to the `PatcherServer` class, enabling automatic cleanup of server resources when used in a `with` statement.

## Implementation Summary

### Files Modified

1. **`py2max/server.py`**
   - Added `_running` flag to track server state
   - Implemented `__enter__()` and `__exit__()` methods for context manager protocol
   - Added graceful `shutdown()` method with proper cleanup
   - Added `stop()` as backward-compatible alias for `shutdown()`
   - Added `__del__()` for cleanup on object deletion
   - Enhanced docstrings with context manager usage examples

2. **`examples/live_preview_demo.py`**
   - Added `demo_context_manager()` function demonstrating context manager usage
   - Updated usage documentation to include 'context' mode
   - Added command-line argument parsing for different demo modes

3. **`tests/test_server.py`** (NEW)
   - Created comprehensive test suite with 22 test cases
   - Tests cover: basic functionality, context manager, exception handling, cleanup
   - All tests pass successfully

## API Usage

### Context Manager Pattern (Recommended)

```python
from py2max import Patcher

p = Patcher('patch.maxpat')

# Server automatically starts and stops
with p.serve(port=8000) as server:
    osc = p.add_textbox('cycle~ 440')
    p.save()  # Browser updates

    gain = p.add_textbox('gain~')
    p.save()

    p.add_line(osc, gain)
    p.save()

# Server is automatically stopped after exiting the context
```

### Manual Management Pattern (Backward Compatible)

```python
from py2max import Patcher

p = Patcher('patch.maxpat')
server = p.serve(port=8000)

osc = p.add_textbox('cycle~ 440')
p.save()

# Manual cleanup when done
server.shutdown()  # or server.stop()
```

### Exception Handling

The context manager properly handles exceptions and ensures cleanup:

```python
with p.serve(port=8000) as server:
    osc = p.add_textbox('cycle~ 440')
    p.save()

    raise ValueError("Something went wrong")
    # Server is still properly stopped

# Server is stopped even when exceptions occur
```

## Key Features

1. **Automatic Cleanup**: Server resources are automatically freed when exiting context
2. **Exception Safe**: Server stops even if exceptions occur within the context
3. **Backward Compatible**: Existing code using manual `shutdown()` continues to work
4. **Pythonic API**: Follows Python conventions for context managers
5. **State Tracking**: `_running` flag prevents double-start/stop operations
6. **Comprehensive Tests**: 22 test cases ensure correctness

## Implementation Details

### Context Manager Protocol

```python
class PatcherServer:
    def __enter__(self):
        """Context manager entry - server already started."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - shutdown server."""
        self.shutdown()
        return False  # Don't suppress exceptions
```

### Graceful Shutdown

```python
def shutdown(self):
    """Shutdown the server gracefully."""
    if not self._running:
        return

    if self.server:
        self.server.shutdown()
        self.server.server_close()
        self._running = False
        print("Live preview server stopped")

    # Clear class-level references
    SSEHandler.patcher = None
    SSEHandler.event_queues.clear()
```

### Automatic Cleanup on Deletion

```python
def __del__(self):
    """Cleanup on deletion."""
    if self._running:
        self.shutdown()
```

## Testing

All tests pass successfully:

```bash
$ uv run pytest tests/test_server.py -v
============================== 22 passed in 6.72s ===============================

$ make test
======================= 299 passed, 14 skipped in 8.70s ========================
```

### Test Coverage

- `get_patcher_state_json()` function (6 tests)
- `PatcherServer` class initialization and lifecycle (9 tests)
- Context manager functionality (2 tests)
- `serve_patcher()` convenience function (2 tests)
- `Patcher.serve()` integration (2 tests)
- SSEHandler class-level state management (1 test)

## Demo Usage

Run the context manager demo:

```bash
# Interactive demo with browser
python examples/live_preview_demo.py context

# Basic demo (manual server management)
python examples/live_preview_demo.py

# Interactive REPL mode
python examples/live_preview_demo.py interactive
```

## Benefits

1. **Resource Management**: Ensures server resources are properly cleaned up
2. **Cleaner Code**: Reduces boilerplate for common use cases
3. **Error Safety**: Guarantees cleanup even in error conditions
4. **Familiar Pattern**: Uses standard Python context manager idiom
5. **Flexibility**: Supports both automatic and manual management styles

## Next Steps

The SSE implementation is now complete with:

- [x] Pure stdlib Server-Sent Events
- [x] Real-time browser updates
- [x] Context manager support
- [x] Comprehensive testing
- [x] Multiple usage patterns

**Future enhancement**: WebSocket implementation (Python 3.11+ asyncio) for bidirectional communication and interactive editing features.
