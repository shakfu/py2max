# py2max Package Restructuring Report

## Overview

The py2max package has been reorganized from a flat module structure (22 Python files) into logical subpackages while maintaining 100% backward compatibility. All 418 tests pass after the restructuring.

## New Package Structure

```
py2max/
├── __init__.py          # Public API (re-exports from subpackages)
├── __main__.py          # Entry point (unchanged)
├── cli.py               # CLI (updated imports)
├── exceptions.py        # Exceptions (unchanged)
├── log.py               # Logging (unchanged)
├── utils.py             # Utilities (unchanged)
├── transformers.py      # Transformers (unchanged)
├── py.typed             # PEP 561 marker (unchanged)
│
├── core/                # Core patcher functionality
│   ├── __init__.py      # Exports: Patcher, Box, Patchline, etc.
│   ├── patcher.py       # Patcher class (~1,563 lines)
│   ├── box.py           # Box class (~214 lines)
│   ├── patchline.py     # Patchline class (~62 lines)
│   ├── abstract.py      # Abstract base classes
│   └── common.py        # Rect class
│
├── maxref/              # Max object reference system
│   ├── __init__.py      # Exports: MaxRefDB, MaxRefCache, etc.
│   ├── parser.py        # XML parsing (was maxref.py)
│   ├── db.py            # SQLite database
│   ├── category.py      # Object categorization
│   └── legacy.py        # MAXCLASS_DEFAULTS (was maxclassdb.py)
│
├── layout/              # Layout managers
│   ├── __init__.py      # Exports all layout managers
│   ├── base.py          # LayoutManager base class
│   ├── grid.py          # GridLayoutManager + legacy aliases
│   ├── flow.py          # FlowLayoutManager
│   └── matrix.py        # MatrixLayoutManager
│
├── server/              # Interactive server & REPL
│   ├── __init__.py      # Exports: InteractivePatcherServer, etc.
│   ├── websocket.py     # WebSocket server (was server.py)
│   ├── repl.py          # REPL core
│   ├── client.py        # REPL client (was repl_client.py)
│   ├── inline.py        # Inline REPL (was repl_inline.py)
│   └── rpc.py           # RPC server (was repl_server.py)
│
├── export/              # Export functionality
│   ├── __init__.py      # Exports: export_svg, converters
│   ├── svg.py           # SVG export
│   └── converters.py    # Format converters
│
└── [shim modules]       # Backward compatibility shims (see below)
```

## Backward Compatibility Shims

The following shim modules exist at the top level to maintain backward compatibility with existing code:

| Shim Module | Re-exports From | Exports |
|-------------|-----------------|---------|
| `abstract.py` | `core.abstract` | `AbstractBox`, `AbstractLayoutManager`, `AbstractPatcher`, `AbstractPatchline` |
| `category.py` | `maxref.category` | `CONTROL_OBJECTS`, `GENERATOR_OBJECTS`, `INPUT_OBJECTS`, `OUTPUT_OBJECTS`, `PROCESSOR_OBJECTS` |
| `common.py` | `core.common` | `Rect` |
| `converters.py` | `export.converters` | `maxpat_to_python`, `maxref_to_sqlite` |
| `db.py` | `maxref.db`, `maxref` | `MaxRefDB`, `get_object_info`, `get_available_objects`, `get_all_*_objects` |
| `maxclassdb.py` | `maxref.legacy` | `MAXCLASS_DEFAULTS` |
| `repl.py` | `server.repl` | `AutoSyncWrapper`, `ReplCommands`, `start_repl`, `start_repl_with_refresh`, `embed` |
| `repl_client.py` | `server.client` | `ReplClient`, `start_repl_client`, `connect` |
| `repl_inline.py` | `server.inline` | `BackgroundServerREPL`, `start_inline_repl`, `start_background_server_repl`, `setup_file_logging`, `restore_console_logging` |
| `repl_server.py` | `server.rpc` | `ReplServer`, `start_repl_server` |
| `svg.py` | `export.svg` | `export_svg`, `export_svg_string` |

**Note:** The `core/`, `maxref/`, `layout/`, `server/`, and `export/` directories are Python packages. The original module names (e.g., `core.py`, `server.py`) were removed since packages take precedence over same-named modules.

## Import Patterns

All of the following import patterns work:

### Public API (recommended)
```python
from py2max import Patcher, Box, Patchline
from py2max import MaxRefDB
from py2max import export_svg, export_svg_string
```

### Subpackage imports (new, preferred for internal use)
```python
from py2max.core import Patcher, Box, Patchline
from py2max.core.patcher import Patcher
from py2max.maxref import MaxRefDB, get_object_info
from py2max.layout import FlowLayoutManager, GridLayoutManager
from py2max.server import InteractivePatcherServer
from py2max.export import export_svg
```

### Legacy imports (still work via shims)
```python
from py2max.common import Rect
from py2max.db import MaxRefDB
from py2max.maxclassdb import MAXCLASS_DEFAULTS
from py2max.repl import start_repl
from py2max.svg import export_svg
```

## Internal Import Style

Within the package, relative imports are used consistently:

```python
# From py2max/server/repl.py
from ..core import Patcher
from ..maxref import get_object_help
from .websocket import InteractivePatcherServer

# From py2max/export/converters.py
from ..core import Patcher
from ..maxref.db import MaxRefDB
```

## Test Updates

Some tests that used monkey-patching were updated to patch at the new module locations:

| Old Patch Target | New Patch Target |
|------------------|------------------|
| `py2max.repl.embed` | `py2max.server.repl.embed` |
| `py2max.repl_client.connect` | `py2max.server.client.connect` |
| `py2max.db.get_object_info` | `py2max.maxref.db.get_object_info` |

## Files Unchanged

The following files remain at the top level and were not moved:

- `__init__.py` - Main package exports
- `__main__.py` - Entry point
- `cli.py` - Command line interface
- `exceptions.py` - Exception classes
- `log.py` - Logging utilities
- `utils.py` - Utility functions
- `transformers.py` - Patch transformers
- `py.typed` - PEP 561 marker

## Summary

- **Before:** 22 flat Python modules
- **After:** 5 subpackages + 7 top-level modules + 11 shim modules
- **Tests:** 418 passed, 14 skipped
- **Backward Compatibility:** 100% maintained via shim modules
