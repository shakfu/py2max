"""db.py - SQLite database for Max object reference data"""

import json
import sqlite3
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .parser import (
    get_all_jit_objects,
    get_all_m4l_objects,
    get_all_max_objects,
    get_all_msp_objects,
    get_available_objects,
    get_object_info,
)


class MaxRefDB:
    """SQLite database for Max object reference data

    By default, uses a cached database at:
    - macOS: ~/Library/Caches/py2max/maxref.db
    - Linux: ~/.cache/py2max/maxref.db
    - Windows: ~/AppData/Local/py2max/Cache/maxref.db

    The cache is automatically populated on first use.
    """

    @staticmethod
    def get_cache_dir() -> Path:
        """Get platform-specific cache directory for py2max

        Returns:
            Path to cache directory:
            - macOS: ~/Library/Caches/py2max
            - Linux: ~/.cache/py2max
            - Windows: ~/AppData/Local/py2max/Cache
        """
        home = Path.home()

        if sys.platform == "darwin":  # macOS
            cache_dir = home / "Library" / "Caches" / "py2max"
        elif sys.platform == "win32":  # Windows
            cache_dir = home / "AppData" / "Local" / "py2max" / "Cache"
        else:  # Linux and others
            cache_dir = home / ".cache" / "py2max"

        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    @staticmethod
    def get_default_db_path() -> Path:
        """Get default database path

        Returns:
            Path to default maxref.db in cache directory
        """
        return MaxRefDB.get_cache_dir() / "maxref.db"

    def __init__(
        self, db_path: Optional[Union[Path, str]] = None, auto_populate: bool = True
    ):
        """Initialize database connection

        Args:
            db_path: Path to SQLite database file.
                    If None, uses platform-specific cache location.
                    Use ":memory:" for in-memory database.
            auto_populate: If True and database is empty, automatically populate
                          with all Max objects (only applies to file-based databases).
        """
        if db_path is None:
            self.db_path: Union[Path, str] = self.get_default_db_path()
            self._use_cache = True
        elif db_path == ":memory:":
            self.db_path = ":memory:"
            self._use_cache = False
        else:
            self.db_path = Path(db_path)
            self._use_cache = False

        self._conn = None
        # For in-memory databases, maintain a persistent connection
        if self.db_path == ":memory:":
            self._conn = sqlite3.connect(":memory:")
            self._conn.row_factory = sqlite3.Row

        self._init_schema()

        # Auto-populate cache on first use
        if auto_populate and self._use_cache and self.count == 0:
            self._auto_populate_cache()

    def __len__(self) -> int:
        """Return number of objects in database"""
        return self.count

    def __enter__(self) -> "MaxRefDB":
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - close connection"""
        self.close()

    def __del__(self) -> None:
        """Destructor - ensure connection is closed"""
        self.close()

    def close(self) -> None:
        """Close database connection

        Safe to call multiple times. Should be called when done with
        in-memory databases to prevent ResourceWarning.
        """
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass  # Ignore errors during close
            self._conn = None

    def __contains__(self, name: str) -> bool:
        """Check if object exists in database"""
        with self._get_cursor() as cursor:
            cursor.execute("SELECT 1 FROM objects WHERE name = ?", (name,))
            return cursor.fetchone() is not None

    def __getitem__(self, name: str) -> Dict[str, Any]:
        """Get object by name using subscript notation"""
        obj = self.get_object(name)
        if obj is None:
            raise KeyError(f"Object '{name}' not found in database")
        return obj

    @classmethod
    def create_database(cls, db_path: Path, populate: bool = True) -> "MaxRefDB":
        """Create and optionally populate a Max reference database

        Args:
            db_path: Path to SQLite database file
            populate: Whether to populate with all available .maxref.xml files

        Returns:
            MaxRefDB instance
        """
        db = cls(db_path)
        if populate:
            db.populate_from_maxref()
        return db

    @contextmanager
    def _get_cursor(self):
        """Context manager for database cursor"""
        if self._conn is not None:
            # Use persistent connection for in-memory databases
            cursor = self._conn.cursor()
            try:
                yield cursor
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise
        else:
            # Use new connection for file-based databases
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            try:
                yield cursor
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def _init_schema(self):
        """Create database schema"""
        with self._get_cursor() as cursor:
            # Main objects table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS objects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    digest TEXT,
                    description TEXT,
                    category TEXT,
                    module_pathname TEXT,
                    autofit INTEGER DEFAULT 0,
                    root_attrs TEXT
                )
            """)

            # Metadata table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    object_id INTEGER NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    FOREIGN KEY (object_id) REFERENCES objects(id) ON DELETE CASCADE
                )
            """)

            # Inlets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inlets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    object_id INTEGER NOT NULL,
                    inlet_id TEXT NOT NULL,
                    inlet_type TEXT,
                    digest TEXT,
                    description TEXT,
                    attrs TEXT,
                    FOREIGN KEY (object_id) REFERENCES objects(id) ON DELETE CASCADE
                )
            """)

            # Outlets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS outlets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    object_id INTEGER NOT NULL,
                    outlet_id TEXT NOT NULL,
                    outlet_type TEXT,
                    digest TEXT,
                    description TEXT,
                    attrs TEXT,
                    FOREIGN KEY (object_id) REFERENCES objects(id) ON DELETE CASCADE
                )
            """)

            # Object arguments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS objargs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    object_id INTEGER NOT NULL,
                    name TEXT,
                    optional INTEGER DEFAULT 0,
                    arg_type TEXT,
                    digest TEXT,
                    description TEXT,
                    attrs TEXT,
                    FOREIGN KEY (object_id) REFERENCES objects(id) ON DELETE CASCADE
                )
            """)

            # Methods table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS methods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    object_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    digest TEXT,
                    description TEXT,
                    attrs TEXT,
                    FOREIGN KEY (object_id) REFERENCES objects(id) ON DELETE CASCADE
                )
            """)

            # Method arguments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS method_args (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    method_id INTEGER NOT NULL,
                    name TEXT,
                    optional INTEGER DEFAULT 0,
                    arg_type TEXT,
                    attrs TEXT,
                    FOREIGN KEY (method_id) REFERENCES methods(id) ON DELETE CASCADE
                )
            """)

            # Attributes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attributes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    object_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    can_get INTEGER DEFAULT 1,
                    can_set INTEGER DEFAULT 1,
                    attr_type TEXT,
                    size INTEGER,
                    digest TEXT,
                    description TEXT,
                    attrs TEXT,
                    FOREIGN KEY (object_id) REFERENCES objects(id) ON DELETE CASCADE
                )
            """)

            # Attribute enum values table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attribute_enums (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    attribute_id INTEGER NOT NULL,
                    name TEXT,
                    digest TEXT,
                    description TEXT,
                    attrs TEXT,
                    FOREIGN KEY (attribute_id) REFERENCES attributes(id) ON DELETE CASCADE
                )
            """)

            # Examples table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS examples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    object_id INTEGER NOT NULL,
                    name TEXT,
                    caption TEXT,
                    attrs TEXT,
                    FOREIGN KEY (object_id) REFERENCES objects(id) ON DELETE CASCADE
                )
            """)

            # See also references table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS seealso (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    object_id INTEGER NOT NULL,
                    ref_name TEXT NOT NULL,
                    FOREIGN KEY (object_id) REFERENCES objects(id) ON DELETE CASCADE
                )
            """)

            # Misc table (for Output, Connections, etc.)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS misc (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    object_id INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    entry_name TEXT NOT NULL,
                    description TEXT,
                    FOREIGN KEY (object_id) REFERENCES objects(id) ON DELETE CASCADE
                )
            """)

            # Palette information table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS palette (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    object_id INTEGER NOT NULL,
                    category TEXT,
                    palette_index INTEGER,
                    attrs TEXT,
                    FOREIGN KEY (object_id) REFERENCES objects(id) ON DELETE CASCADE
                )
            """)

            # Parameter information table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS parameter (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    object_id INTEGER NOT NULL,
                    attrs TEXT,
                    FOREIGN KEY (object_id) REFERENCES objects(id) ON DELETE CASCADE
                )
            """)

            # Create indices for faster queries
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_objects_name ON objects(name)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_metadata_object ON metadata(object_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_inlets_object ON inlets(object_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_outlets_object ON outlets(object_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_methods_object ON methods(object_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_attributes_object ON attributes(object_id)"
            )

    def populate(
        self, object_names: Optional[List[str]] = None, category: Optional[str] = None
    ):
        """Populate database from .maxref.xml files

        Args:
            object_names: List of object names to import. If None, imports based on category.
            category: Category to import ('max', 'msp', 'jit', 'm4l', or None for all).
                     Ignored if object_names is provided.
        """
        if object_names is None:
            if category is None:
                object_names = get_available_objects()
            elif category.lower() == "max":
                object_names = get_all_max_objects()
            elif category.lower() == "msp":
                object_names = get_all_msp_objects()
            elif category.lower() == "jit":
                object_names = get_all_jit_objects()
            elif category.lower() == "m4l":
                object_names = get_all_m4l_objects()
            else:
                raise ValueError(
                    f"Unknown category: {category}. Use 'max', 'msp', 'jit', 'm4l', or None"
                )

        for name in object_names:
            data = get_object_info(name)
            if data:
                self.insert_object(name, data)

    # Deprecated methods - use populate() instead
    def populate_from_maxref(self, object_names: Optional[List[str]] = None):
        """Populate database from .maxref.xml files (deprecated: use populate())

        Args:
            object_names: List of object names to import. If None, imports all available objects.
        """
        self.populate(object_names)

    def populate_all_objects(self):
        """Populate database with all available Max objects (deprecated: use populate())"""
        self.populate(category=None)

    def populate_all_max_objects(self):
        """Populate database with all Max objects (deprecated: use populate(category='max'))"""
        self.populate(category="max")

    def populate_all_jit_objects(self):
        """Populate database with all Jitter objects (deprecated: use populate(category='jit'))"""
        self.populate(category="jit")

    def populate_all_msp_objects(self):
        """Populate database with all MSP objects (deprecated: use populate(category='msp'))"""
        self.populate(category="msp")

    def populate_all_m4l_objects(self):
        """Populate database with all Max for Live objects (deprecated: use populate(category='m4l'))"""
        self.populate(category="m4l")

    def insert_object(self, name: str, data: Dict[str, Any]) -> int:
        """Insert object data into database

        Args:
            name: Object name
            data: Object data dictionary from maxref

        Returns:
            Object ID
        """
        with self._get_cursor() as cursor:
            # Store root attributes separately
            root_attrs = {}
            for key, value in data.items():
                if key not in [
                    "digest",
                    "description",
                    "metadata",
                    "inlets",
                    "outlets",
                    "objargs",
                    "methods",
                    "attributes",
                    "examples",
                    "seealso",
                    "misc",
                    "palette",
                    "parameter",
                    "name",
                    "category",
                    "module_pathname",
                    "autofit",
                ]:
                    root_attrs[key] = value

            # Insert main object record
            cursor.execute(
                """
                INSERT OR REPLACE INTO objects
                (name, digest, description, category, module_pathname, autofit, root_attrs)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    name,
                    data.get("digest"),
                    data.get("description"),
                    data.get("category"),
                    data.get("module_pathname"),
                    1 if data.get("autofit") == "1" else 0,
                    json.dumps(root_attrs) if root_attrs else None,
                ),
            )

            object_id = cursor.lastrowid

            # Delete existing related records (for REPLACE)
            cursor.execute("DELETE FROM metadata WHERE object_id = ?", (object_id,))
            cursor.execute("DELETE FROM inlets WHERE object_id = ?", (object_id,))
            cursor.execute("DELETE FROM outlets WHERE object_id = ?", (object_id,))
            cursor.execute("DELETE FROM objargs WHERE object_id = ?", (object_id,))
            cursor.execute("DELETE FROM methods WHERE object_id = ?", (object_id,))
            cursor.execute("DELETE FROM attributes WHERE object_id = ?", (object_id,))
            cursor.execute("DELETE FROM examples WHERE object_id = ?", (object_id,))
            cursor.execute("DELETE FROM seealso WHERE object_id = ?", (object_id,))
            cursor.execute("DELETE FROM misc WHERE object_id = ?", (object_id,))
            cursor.execute("DELETE FROM palette WHERE object_id = ?", (object_id,))
            cursor.execute("DELETE FROM parameter WHERE object_id = ?", (object_id,))

            # Insert metadata
            metadata = data.get("metadata", {})
            for key, value in metadata.items():
                # Handle lists (e.g., multiple tags)
                if isinstance(value, list):
                    for v in value:
                        cursor.execute(
                            "INSERT INTO metadata (object_id, key, value) VALUES (?, ?, ?)",
                            (object_id, key, v),
                        )
                else:
                    cursor.execute(
                        "INSERT INTO metadata (object_id, key, value) VALUES (?, ?, ?)",
                        (object_id, key, value),
                    )

            # Insert inlets
            for inlet in data.get("inlets", []):
                extra_attrs = {
                    k: v
                    for k, v in inlet.items()
                    if k not in ["id", "type", "digest", "description"]
                }
                cursor.execute(
                    """
                    INSERT INTO inlets (object_id, inlet_id, inlet_type, digest, description, attrs)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        object_id,
                        inlet.get("id"),
                        inlet.get("type"),
                        inlet.get("digest"),
                        inlet.get("description"),
                        json.dumps(extra_attrs) if extra_attrs else None,
                    ),
                )

            # Insert outlets
            for outlet in data.get("outlets", []):
                extra_attrs = {
                    k: v
                    for k, v in outlet.items()
                    if k not in ["id", "type", "digest", "description"]
                }
                cursor.execute(
                    """
                    INSERT INTO outlets (object_id, outlet_id, outlet_type, digest, description, attrs)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        object_id,
                        outlet.get("id"),
                        outlet.get("type"),
                        outlet.get("digest"),
                        outlet.get("description"),
                        json.dumps(extra_attrs) if extra_attrs else None,
                    ),
                )

            # Insert object arguments
            for objarg in data.get("objargs", []):
                extra_attrs = {
                    k: v
                    for k, v in objarg.items()
                    if k not in ["name", "optional", "type", "digest", "description"]
                }
                cursor.execute(
                    """
                    INSERT INTO objargs (object_id, name, optional, arg_type, digest, description, attrs)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        object_id,
                        objarg.get("name"),
                        1 if objarg.get("optional") == "1" else 0,
                        objarg.get("type"),
                        objarg.get("digest"),
                        objarg.get("description"),
                        json.dumps(extra_attrs) if extra_attrs else None,
                    ),
                )

            # Insert methods
            for method_name, method_data in data.get("methods", {}).items():
                extra_attrs = {
                    k: v
                    for k, v in method_data.items()
                    if k not in ["digest", "description", "args", "attributes"]
                }
                cursor.execute(
                    """
                    INSERT INTO methods (object_id, name, digest, description, attrs)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        object_id,
                        method_name,
                        method_data.get("digest"),
                        method_data.get("description"),
                        json.dumps(extra_attrs) if extra_attrs else None,
                    ),
                )
                method_id = cursor.lastrowid

                # Insert method arguments
                for arg in method_data.get("args", []):
                    extra_attrs = {
                        k: v
                        for k, v in arg.items()
                        if k not in ["name", "optional", "type"]
                    }
                    cursor.execute(
                        """
                        INSERT INTO method_args (method_id, name, optional, arg_type, attrs)
                        VALUES (?, ?, ?, ?, ?)
                    """,
                        (
                            method_id,
                            arg.get("name"),
                            1 if arg.get("optional") == "1" else 0,
                            arg.get("type"),
                            json.dumps(extra_attrs) if extra_attrs else None,
                        ),
                    )

            # Insert attributes
            for attr_name, attr_data in data.get("attributes", {}).items():
                extra_attrs = {
                    k: v
                    for k, v in attr_data.items()
                    if k
                    not in [
                        "get",
                        "set",
                        "type",
                        "size",
                        "digest",
                        "description",
                        "enumlist",
                        "attributes",
                    ]
                }
                cursor.execute(
                    """
                    INSERT INTO attributes (object_id, name, can_get, can_set, attr_type, size, digest, description, attrs)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        object_id,
                        attr_name,
                        1 if attr_data.get("get") == "1" else 0,
                        1 if attr_data.get("set") == "1" else 0,
                        attr_data.get("type"),
                        int(attr_data.get("size", 0))
                        if attr_data.get("size")
                        else None,
                        attr_data.get("digest"),
                        attr_data.get("description"),
                        json.dumps(extra_attrs) if extra_attrs else None,
                    ),
                )
                attr_id = cursor.lastrowid

                # Insert enum values
                for enum in attr_data.get("enumlist", []):
                    extra_attrs = {
                        k: v
                        for k, v in enum.items()
                        if k not in ["name", "digest", "description"]
                    }
                    cursor.execute(
                        """
                        INSERT INTO attribute_enums (attribute_id, name, digest, description, attrs)
                        VALUES (?, ?, ?, ?, ?)
                    """,
                        (
                            attr_id,
                            enum.get("name"),
                            enum.get("digest"),
                            enum.get("description"),
                            json.dumps(extra_attrs) if extra_attrs else None,
                        ),
                    )

            # Insert examples
            for example in data.get("examples", []):
                extra_attrs = {
                    k: v for k, v in example.items() if k not in ["name", "caption"]
                }
                cursor.execute(
                    """
                    INSERT INTO examples (object_id, name, caption, attrs)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        object_id,
                        example.get("name"),
                        example.get("caption"),
                        json.dumps(extra_attrs) if extra_attrs else None,
                    ),
                )

            # Insert see also references
            for ref in data.get("seealso", []):
                cursor.execute(
                    "INSERT INTO seealso (object_id, ref_name) VALUES (?, ?)",
                    (object_id, ref),
                )

            # Insert misc entries
            for category, entries in data.get("misc", {}).items():
                for entry_name, description in entries.items():
                    cursor.execute(
                        """
                        INSERT INTO misc (object_id, category, entry_name, description)
                        VALUES (?, ?, ?, ?)
                    """,
                        (object_id, category, entry_name, description),
                    )

            # Insert palette info
            palette = data.get("palette", {})
            if palette:
                extra_attrs = {
                    k: v
                    for k, v in palette.items()
                    if k not in ["category", "palette_index"]
                }
                cursor.execute(
                    """
                    INSERT INTO palette (object_id, category, palette_index, attrs)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        object_id,
                        palette.get("category"),
                        int(palette.get("palette_index"))
                        if palette.get("palette_index")
                        else None,
                        json.dumps(extra_attrs) if extra_attrs else None,
                    ),
                )

            # Insert parameter info
            parameter = data.get("parameter", {})
            if parameter:
                cursor.execute(
                    """
                    INSERT INTO parameter (object_id, attrs)
                    VALUES (?, ?)
                """,
                    (object_id, json.dumps(parameter) if parameter else None),
                )

            return object_id

    def get_object(self, name: str) -> Optional[Dict[str, Any]]:
        """Get object data from database

        Args:
            name: Object name

        Returns:
            Object data dictionary or None if not found
        """
        with self._get_cursor() as cursor:
            cursor.execute("SELECT * FROM objects WHERE name = ?", (name,))
            row = cursor.fetchone()

            if not row:
                return None

            data = dict(row)
            object_id = data["id"]

            # Parse root_attrs
            if data["root_attrs"]:
                root_attrs = json.loads(data["root_attrs"])
                data.update(root_attrs)
            del data["root_attrs"]

            # Get metadata
            cursor.execute(
                "SELECT key, value FROM metadata WHERE object_id = ?", (object_id,)
            )
            metadata: Dict[str, Any] = {}
            for meta_row in cursor.fetchall():
                key, value = meta_row["key"], meta_row["value"]
                if key in metadata:
                    if not isinstance(metadata[key], list):
                        metadata[key] = [metadata[key]]
                    metadata[key].append(value)
                else:
                    metadata[key] = value
            data["metadata"] = metadata

            # Get inlets
            cursor.execute("SELECT * FROM inlets WHERE object_id = ?", (object_id,))
            data["inlets"] = [dict(row) for row in cursor.fetchall()]

            # Get outlets
            cursor.execute("SELECT * FROM outlets WHERE object_id = ?", (object_id,))
            data["outlets"] = [dict(row) for row in cursor.fetchall()]

            # Get objargs
            cursor.execute("SELECT * FROM objargs WHERE object_id = ?", (object_id,))
            data["objargs"] = [dict(row) for row in cursor.fetchall()]

            # Get methods
            cursor.execute("SELECT * FROM methods WHERE object_id = ?", (object_id,))
            methods = {}
            for method_row in cursor.fetchall():
                method_data = dict(method_row)
                method_id = method_data["id"]
                method_name = method_data["name"]

                # Get method args
                cursor.execute(
                    "SELECT * FROM method_args WHERE method_id = ?", (method_id,)
                )
                method_data["args"] = [dict(row) for row in cursor.fetchall()]

                methods[method_name] = method_data
            data["methods"] = methods

            # Get attributes
            cursor.execute("SELECT * FROM attributes WHERE object_id = ?", (object_id,))
            attributes = {}
            for attr_row in cursor.fetchall():
                attr_data = dict(attr_row)
                attr_id = attr_data["id"]
                attr_name = attr_data["name"]

                # Get enum values
                cursor.execute(
                    "SELECT * FROM attribute_enums WHERE attribute_id = ?", (attr_id,)
                )
                attr_data["enumlist"] = [dict(row) for row in cursor.fetchall()]

                attributes[attr_name] = attr_data
            data["attributes"] = attributes

            # Get examples
            cursor.execute("SELECT * FROM examples WHERE object_id = ?", (object_id,))
            data["examples"] = [dict(row) for row in cursor.fetchall()]

            # Get seealso
            cursor.execute(
                "SELECT ref_name FROM seealso WHERE object_id = ?", (object_id,)
            )
            data["seealso"] = [row["ref_name"] for row in cursor.fetchall()]

            # Get misc
            cursor.execute("SELECT * FROM misc WHERE object_id = ?", (object_id,))
            misc: Dict[str, Dict[str, str]] = {}
            for misc_row in cursor.fetchall():
                category = misc_row["category"]
                if category not in misc:
                    misc[category] = {}
                misc[category][misc_row["entry_name"]] = misc_row["description"]
            data["misc"] = misc

            # Get palette
            cursor.execute("SELECT * FROM palette WHERE object_id = ?", (object_id,))
            palette_row = cursor.fetchone()
            if palette_row:
                data["palette"] = dict(palette_row)
            else:
                data["palette"] = {}

            # Get parameter
            cursor.execute(
                "SELECT attrs FROM parameter WHERE object_id = ?", (object_id,)
            )
            param_row = cursor.fetchone()
            if param_row and param_row["attrs"]:
                data["parameter"] = json.loads(param_row["attrs"])
            else:
                data["parameter"] = {}

            return data

    def search(self, query: str, fields: Optional[List[str]] = None) -> List[str]:
        """Search for objects by name, digest, or description

        Args:
            query: Search query string
            fields: List of fields to search in. Default: ['name', 'digest', 'description']

        Returns:
            List of matching object names
        """
        if fields is None:
            fields = ["name", "digest", "description"]

        with self._get_cursor() as cursor:
            conditions = []
            for field in fields:
                if field in ["name", "digest", "description", "category"]:
                    conditions.append(f"{field} LIKE ?")

            where_clause = " OR ".join(conditions)
            sql = f"SELECT name FROM objects WHERE {where_clause} ORDER BY name"

            cursor.execute(sql, tuple([f"%{query}%" for _ in conditions]))
            return [row["name"] for row in cursor.fetchall()]

    def search_objects(
        self, query: str, fields: Optional[List[str]] = None
    ) -> List[str]:
        """Search for objects by name, digest, or description (deprecated: use search())

        Args:
            query: Search query string
            fields: List of fields to search in. Default: ['name', 'digest', 'description']

        Returns:
            List of matching object names
        """
        return self.search(query, fields)

    def by_category(self, category: str) -> List[str]:
        """Get all objects in a category

        Args:
            category: Category name

        Returns:
            List of object names
        """
        with self._get_cursor() as cursor:
            cursor.execute(
                "SELECT name FROM objects WHERE category = ? ORDER BY name", (category,)
            )
            return [row["name"] for row in cursor.fetchall()]

    def get_objects_by_category(self, category: str) -> List[str]:
        """Get all objects in a category (deprecated: use by_category())

        Args:
            category: Category name

        Returns:
            List of object names
        """
        return self.by_category(category)

    @property
    def categories(self) -> List[str]:
        """All unique categories in database"""
        with self._get_cursor() as cursor:
            cursor.execute(
                "SELECT DISTINCT category FROM objects WHERE category IS NOT NULL ORDER BY category"
            )
            return [row["category"] for row in cursor.fetchall()]

    def get_all_categories(self) -> List[str]:
        """Get all unique categories (deprecated: use .categories property)

        Returns:
            List of category names
        """
        return self.categories

    @property
    def count(self) -> int:
        """Total number of objects in database"""
        with self._get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM objects")
            return cursor.fetchone()["count"]

    @property
    def objects(self) -> List[str]:
        """All object names in database"""
        with self._get_cursor() as cursor:
            cursor.execute("SELECT name FROM objects ORDER BY name")
            return [row["name"] for row in cursor.fetchall()]

    def get_object_count(self) -> int:
        """Get total number of objects in database (deprecated: use .count property)

        Returns:
            Object count
        """
        return self.count

    def export(self, output_path: Path):
        """Export entire database to JSON file

        Args:
            output_path: Path to output JSON file
        """
        with self._get_cursor() as cursor:
            cursor.execute("SELECT name FROM objects ORDER BY name")
            all_objects = {}

            for row in cursor.fetchall():
                name = row["name"]
                all_objects[name] = self.get_object(name)

            output_path.write_text(json.dumps(all_objects, indent=2))

    def export_to_json(self, output_path: Path):
        """Export entire database to JSON file (deprecated: use export())

        Args:
            output_path: Path to output JSON file
        """
        self.export(output_path)

    def load(self, input_path: Path):
        """Import objects from JSON file

        Args:
            input_path: Path to input JSON file
        """
        data = json.loads(input_path.read_text())
        for name, obj_data in data.items():
            self.insert_object(name, obj_data)

    def import_from_json(self, input_path: Path):
        """Import objects from JSON file (deprecated: use load())

        Args:
            input_path: Path to input JSON file
        """
        self.load(input_path)

    def summary(self) -> Dict[str, Any]:
        """Get database summary statistics

        Returns:
            Dictionary with count, categories, and category counts
        """
        summary = {
            "total_objects": self.count,
            "categories": {},
        }

        categories_dict: Dict[str, int] = {}
        for category in self.categories:
            categories_dict[category] = len(self.by_category(category))
        summary["categories"] = categories_dict

        return summary

    def __repr__(self) -> str:
        """String representation of database"""
        if self.db_path == ":memory:":
            location = "in-memory"
        else:
            location = str(self.db_path)
        return f"MaxRefDB({location}, {self.count} objects)"

    def _auto_populate_cache(self):
        """Auto-populate cache database with all Max objects"""
        import sys

        print("Initializing py2max cache (one-time setup)...", file=sys.stderr)
        print(f"Location: {self.db_path}", file=sys.stderr)
        print("Populating with all Max objects (1157 objects)...", file=sys.stderr)
        self.populate()
        print(f"Cache ready with {self.count} objects", file=sys.stderr)


__all__ = ["MaxRefDB"]
