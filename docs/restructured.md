# py2max Package Restructuring Report

## Overview

The py2max package has been reorganized from a flat module structure (22 Python files) into logical subpackages. All 418 tests pass after the restructuring.

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
└── export/              # Export functionality
    ├── __init__.py      # Exports: export_svg, converters
    ├── svg.py           # SVG export
    └── converters.py    # Format converters
```

## Import Patterns

### Public API (recommended)
```python
from py2max import Patcher, Box, Patchline
from py2max import MaxRefDB
from py2max import export_svg, export_svg_string
```

### Subpackage imports (for direct module access)
```python
from py2max.core import Patcher, Box, Patchline
from py2max.core.patcher import Patcher
from py2max.core.common import Rect
from py2max.maxref import MaxRefDB, get_object_info
from py2max.maxref.category import CONTROL_OBJECTS, GENERATOR_OBJECTS
from py2max.maxref.legacy import MAXCLASS_DEFAULTS
from py2max.layout import FlowLayoutManager, GridLayoutManager
from py2max.server import InteractivePatcherServer
from py2max.server.repl import ReplCommands, start_repl
from py2max.server.client import ReplClient, start_repl_client
from py2max.server.inline import start_inline_repl, BackgroundServerREPL
from py2max.server.rpc import ReplServer, start_repl_server
from py2max.export import export_svg
from py2max.export.converters import maxpat_to_python, maxref_to_sqlite
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

## Module Mapping

| Old Location | New Location |
|--------------|--------------|
| `py2max.core` (class) | `py2max.core.patcher` |
| `py2max.abstract` | `py2max.core.abstract` |
| `py2max.common` | `py2max.core.common` |
| `py2max.maxref` | `py2max.maxref.parser` |
| `py2max.db` | `py2max.maxref.db` |
| `py2max.category` | `py2max.maxref.category` |
| `py2max.maxclassdb` | `py2max.maxref.legacy` |
| `py2max.layout` | `py2max.layout` (split into base/grid/flow/matrix) |
| `py2max.server` | `py2max.server.websocket` |
| `py2max.repl` | `py2max.server.repl` |
| `py2max.repl_client` | `py2max.server.client` |
| `py2max.repl_inline` | `py2max.server.inline` |
| `py2max.repl_server` | `py2max.server.rpc` |
| `py2max.svg` | `py2max.export.svg` |
| `py2max.converters` | `py2max.export.converters` |

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
- **After:** 5 subpackages + 7 top-level modules
- **Tests:** 418 passed, 14 skipped
