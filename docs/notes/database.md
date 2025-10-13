# SQLite Database for Max Reference Data

## Overview

The `py2max.db` module provides SQLite database functionality for Max object reference data. It converts .maxref.xml files into a queryable, normalized database schema.

## Quick Start

```python
from py2max import MaxRefDB, create_database
from pathlib import Path

# In-memory database
db = MaxRefDB()
db.populate_from_maxref(['cycle~', 'gain~', 'dac~'])

# Query objects
cycle = db.get_object('cycle~')
print(f"Inlets: {len(cycle['inlets'])}, Outlets: {len(cycle['outlets'])}")

# Search
results = db.search_objects('filter')

# Persistent database
file_db = create_database(Path("maxref.db"), populate=True)
```

## Database Schema

### Core Tables

- **objects** - Main object information (name, digest, description, category)
- **metadata** - Key-value metadata (tags, authors, etc.)
- **inlets** - Inlet specifications (type, digest, description)
- **outlets** - Outlet specifications (type, digest, description)

### Documentation Tables

- **methods** - Method definitions
- **method_args** - Method arguments
- **attributes** - Object attributes
- **attribute_enums** - Enum values for attributes
- **objargs** - Object initialization arguments
- **examples** - Example patches
- **seealso** - Related objects
- **misc** - Miscellaneous entries

### Configuration Tables

- **palette** - Palette information
- **parameter** - Parameter settings

## API Reference

### MaxRefDB Class

#### `__init__(db_path: Optional[Path] = None)`

Create database connection. Uses in-memory database if `db_path` is None.

#### `populate_from_maxref(object_names: Optional[List[str]] = None)`

Populate database from .maxref.xml files.

#### `populate_all_objects()`

Populate database with all available Max objects (all categories).

#### `populate_all_max_objects()`

Populate database with all Max objects (max-ref category only).

#### `populate_all_jit_objects()`

Populate database with all Jitter objects (jit-ref category only).

#### `populate_all_msp_objects()`

Populate database with all MSP objects (msp-ref category only).

#### `populate_all_m4l_objects()`

Populate database with all Max for Live objects (m4l-ref category only).

#### `insert_object(name: str, data: Dict[str, Any]) -> int`

Insert single object. Returns object ID.

#### `get_object(name: str) -> Optional[Dict[str, Any]]`

Retrieve object data by name.

#### `search_objects(query: str, fields: Optional[List[str]] = None) -> List[str]`

Search objects. Default fields: `['name', 'digest', 'description']`

#### `get_objects_by_category(category: str) -> List[str]`

Get all objects in a category.

#### `get_all_categories() -> List[str]`

Get all unique categories.

#### `get_object_count() -> int`

Get total number of objects.

#### `export_to_json(output_path: Path)`

Export entire database to JSON.

#### `import_from_json(input_path: Path)`

Import objects from JSON file.

### Helper Function

#### `create_database(db_path: Path, populate: bool = True) -> MaxRefDB`

Convenience function to create and optionally populate database.

## Examples

### Basic Usage

See `examples/maxref_db_demo.py` for comprehensive examples.

### Category-Based Population

```python
from py2max import MaxRefDB
from py2max.maxref import (
    get_all_max_objects,
    get_all_jit_objects,
    get_all_msp_objects,
    get_all_m4l_objects,
)

# Populate with specific categories
db_msp = MaxRefDB()
db_msp.populate_all_msp_objects()  # Only MSP objects
print(f"MSP objects: {db_msp.get_object_count()}")

db_jit = MaxRefDB()
db_jit.populate_all_jit_objects()  # Only Jitter objects
print(f"Jitter objects: {db_jit.get_object_count()}")

# Populate with all objects
db_all = MaxRefDB()
db_all.populate_all_objects()  # All categories
print(f"All objects: {db_all.get_object_count()}")

# Get object lists by category
max_objects = get_all_max_objects()  # Returns list of Max object names
msp_objects = get_all_msp_objects()  # Returns list of MSP object names
jit_objects = get_all_jit_objects()  # Returns list of Jitter object names
m4l_objects = get_all_m4l_objects()  # Returns list of M4L object names
```

See `examples/category_db_demo.py` for detailed category examples.

## Tests

Run tests with:

```bash
uv run pytest tests/test_db.py -v
```

Coverage: 97%
