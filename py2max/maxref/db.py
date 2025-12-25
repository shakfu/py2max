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

    # -------------------------------------------------------------------------
    # Insert helpers
    # -------------------------------------------------------------------------

    def _extract_extra_attrs(
        self, data: Dict[str, Any], exclude: List[str]
    ) -> Optional[str]:
        """Extract extra attributes not in exclude list and JSON-encode them."""
        extra = {k: v for k, v in data.items() if k not in exclude}
        return json.dumps(extra) if extra else None

    def _insert_main_object(
        self, cursor: sqlite3.Cursor, name: str, data: Dict[str, Any]
    ) -> int:
        """Insert main object record and return object_id."""
        known_keys = {
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
        }
        root_attrs = {k: v for k, v in data.items() if k not in known_keys}

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
        return cursor.lastrowid  # type: ignore[return-value]

    def _delete_related_records(self, cursor: sqlite3.Cursor, object_id: int) -> None:
        """Delete all related records for an object (for REPLACE operations)."""
        tables = [
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
        ]
        for table in tables:
            cursor.execute(f"DELETE FROM {table} WHERE object_id = ?", (object_id,))

    def _insert_metadata(
        self, cursor: sqlite3.Cursor, object_id: int, metadata: Dict[str, Any]
    ) -> None:
        """Insert metadata key-value pairs."""
        for key, value in metadata.items():
            values = value if isinstance(value, list) else [value]
            for v in values:
                cursor.execute(
                    "INSERT INTO metadata (object_id, key, value) VALUES (?, ?, ?)",
                    (object_id, key, v),
                )

    def _insert_inlets_outlets(
        self, cursor: sqlite3.Cursor, object_id: int, items: List[Dict], table: str
    ) -> None:
        """Insert inlet or outlet records."""
        id_col = "inlet_id" if table == "inlets" else "outlet_id"
        type_col = "inlet_type" if table == "inlets" else "outlet_type"
        exclude = ["id", "type", "digest", "description"]

        for item in items:
            cursor.execute(
                f"""
                INSERT INTO {table} (object_id, {id_col}, {type_col}, digest, description, attrs)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    object_id,
                    item.get("id"),
                    item.get("type"),
                    item.get("digest"),
                    item.get("description"),
                    self._extract_extra_attrs(item, exclude),
                ),
            )

    def _insert_objargs(
        self, cursor: sqlite3.Cursor, object_id: int, objargs: List[Dict]
    ) -> None:
        """Insert object argument records."""
        exclude = ["name", "optional", "type", "digest", "description"]
        for objarg in objargs:
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
                    self._extract_extra_attrs(objarg, exclude),
                ),
            )

    def _insert_methods(
        self, cursor: sqlite3.Cursor, object_id: int, methods: Dict[str, Dict]
    ) -> None:
        """Insert method records and their arguments."""
        method_exclude = ["digest", "description", "args", "attributes"]
        arg_exclude = ["name", "optional", "type"]

        for method_name, method_data in methods.items():
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
                    self._extract_extra_attrs(method_data, method_exclude),
                ),
            )
            method_id = cursor.lastrowid

            for arg in method_data.get("args", []):
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
                        self._extract_extra_attrs(arg, arg_exclude),
                    ),
                )

    def _insert_attributes(
        self, cursor: sqlite3.Cursor, object_id: int, attributes: Dict[str, Dict]
    ) -> None:
        """Insert attribute records and their enum values."""
        attr_exclude = [
            "get",
            "set",
            "type",
            "size",
            "digest",
            "description",
            "enumlist",
            "attributes",
        ]
        enum_exclude = ["name", "digest", "description"]

        for attr_name, attr_data in attributes.items():
            size_val = attr_data.get("size")
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
                    int(size_val) if size_val else None,
                    attr_data.get("digest"),
                    attr_data.get("description"),
                    self._extract_extra_attrs(attr_data, attr_exclude),
                ),
            )
            attr_id = cursor.lastrowid

            for enum in attr_data.get("enumlist", []):
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
                        self._extract_extra_attrs(enum, enum_exclude),
                    ),
                )

    def _insert_examples(
        self, cursor: sqlite3.Cursor, object_id: int, examples: List[Dict]
    ) -> None:
        """Insert example records."""
        exclude = ["name", "caption"]
        for example in examples:
            cursor.execute(
                """
                INSERT INTO examples (object_id, name, caption, attrs)
                VALUES (?, ?, ?, ?)
                """,
                (
                    object_id,
                    example.get("name"),
                    example.get("caption"),
                    self._extract_extra_attrs(example, exclude),
                ),
            )

    def _insert_seealso(
        self, cursor: sqlite3.Cursor, object_id: int, refs: List[str]
    ) -> None:
        """Insert see-also references."""
        for ref in refs:
            cursor.execute(
                "INSERT INTO seealso (object_id, ref_name) VALUES (?, ?)",
                (object_id, ref),
            )

    def _insert_misc(
        self, cursor: sqlite3.Cursor, object_id: int, misc: Dict[str, Dict[str, str]]
    ) -> None:
        """Insert misc entries."""
        for category, entries in misc.items():
            for entry_name, description in entries.items():
                cursor.execute(
                    """
                    INSERT INTO misc (object_id, category, entry_name, description)
                    VALUES (?, ?, ?, ?)
                    """,
                    (object_id, category, entry_name, description),
                )

    def _insert_palette(
        self, cursor: sqlite3.Cursor, object_id: int, palette: Dict[str, Any]
    ) -> None:
        """Insert palette info."""
        if not palette:
            return
        exclude = ["category", "palette_index"]
        idx = palette.get("palette_index")
        cursor.execute(
            """
            INSERT INTO palette (object_id, category, palette_index, attrs)
            VALUES (?, ?, ?, ?)
            """,
            (
                object_id,
                palette.get("category"),
                int(idx) if idx else None,
                self._extract_extra_attrs(palette, exclude),
            ),
        )

    def _insert_parameter(
        self, cursor: sqlite3.Cursor, object_id: int, parameter: Dict[str, Any]
    ) -> None:
        """Insert parameter info."""
        if not parameter:
            return
        cursor.execute(
            "INSERT INTO parameter (object_id, attrs) VALUES (?, ?)",
            (object_id, json.dumps(parameter)),
        )

    def insert_object(self, name: str, data: Dict[str, Any]) -> int:
        """Insert object data into database

        Args:
            name: Object name
            data: Object data dictionary from maxref

        Returns:
            Object ID
        """
        with self._get_cursor() as cursor:
            object_id = self._insert_main_object(cursor, name, data)
            self._delete_related_records(cursor, object_id)

            self._insert_metadata(cursor, object_id, data.get("metadata", {}))
            self._insert_inlets_outlets(
                cursor, object_id, data.get("inlets", []), "inlets"
            )
            self._insert_inlets_outlets(
                cursor, object_id, data.get("outlets", []), "outlets"
            )
            self._insert_objargs(cursor, object_id, data.get("objargs", []))
            self._insert_methods(cursor, object_id, data.get("methods", {}))
            self._insert_attributes(cursor, object_id, data.get("attributes", {}))
            self._insert_examples(cursor, object_id, data.get("examples", []))
            self._insert_seealso(cursor, object_id, data.get("seealso", []))
            self._insert_misc(cursor, object_id, data.get("misc", {}))
            self._insert_palette(cursor, object_id, data.get("palette", {}))
            self._insert_parameter(cursor, object_id, data.get("parameter", {}))

            return object_id

    # -------------------------------------------------------------------------
    # Get helpers
    # -------------------------------------------------------------------------

    def _get_simple_list(
        self, cursor: sqlite3.Cursor, table: str, object_id: int
    ) -> List[Dict[str, Any]]:
        """Fetch all rows from a table as a list of dicts."""
        cursor.execute(f"SELECT * FROM {table} WHERE object_id = ?", (object_id,))
        return [dict(row) for row in cursor.fetchall()]

    def _get_metadata(self, cursor: sqlite3.Cursor, object_id: int) -> Dict[str, Any]:
        """Fetch metadata, collapsing duplicate keys into lists."""
        cursor.execute(
            "SELECT key, value FROM metadata WHERE object_id = ?", (object_id,)
        )
        metadata: Dict[str, Any] = {}
        for row in cursor.fetchall():
            key, value = row["key"], row["value"]
            if key in metadata:
                if not isinstance(metadata[key], list):
                    metadata[key] = [metadata[key]]
                metadata[key].append(value)
            else:
                metadata[key] = value
        return metadata

    def _get_methods(
        self, cursor: sqlite3.Cursor, object_id: int
    ) -> Dict[str, Dict[str, Any]]:
        """Fetch methods with their arguments."""
        cursor.execute("SELECT * FROM methods WHERE object_id = ?", (object_id,))
        methods: Dict[str, Dict[str, Any]] = {}
        for method_row in cursor.fetchall():
            method_data = dict(method_row)
            method_id = method_data["id"]
            cursor.execute(
                "SELECT * FROM method_args WHERE method_id = ?", (method_id,)
            )
            method_data["args"] = [dict(row) for row in cursor.fetchall()]
            methods[method_data["name"]] = method_data
        return methods

    def _get_attributes(
        self, cursor: sqlite3.Cursor, object_id: int
    ) -> Dict[str, Dict[str, Any]]:
        """Fetch attributes with their enum values."""
        cursor.execute("SELECT * FROM attributes WHERE object_id = ?", (object_id,))
        attributes: Dict[str, Dict[str, Any]] = {}
        for attr_row in cursor.fetchall():
            attr_data = dict(attr_row)
            attr_id = attr_data["id"]
            cursor.execute(
                "SELECT * FROM attribute_enums WHERE attribute_id = ?", (attr_id,)
            )
            attr_data["enumlist"] = [dict(row) for row in cursor.fetchall()]
            attributes[attr_data["name"]] = attr_data
        return attributes

    def _get_seealso(self, cursor: sqlite3.Cursor, object_id: int) -> List[str]:
        """Fetch see-also references as a list of names."""
        cursor.execute("SELECT ref_name FROM seealso WHERE object_id = ?", (object_id,))
        return [row["ref_name"] for row in cursor.fetchall()]

    def _get_misc(
        self, cursor: sqlite3.Cursor, object_id: int
    ) -> Dict[str, Dict[str, str]]:
        """Fetch misc entries grouped by category."""
        cursor.execute("SELECT * FROM misc WHERE object_id = ?", (object_id,))
        misc: Dict[str, Dict[str, str]] = {}
        for row in cursor.fetchall():
            category = row["category"]
            if category not in misc:
                misc[category] = {}
            misc[category][row["entry_name"]] = row["description"]
        return misc

    def _get_palette(self, cursor: sqlite3.Cursor, object_id: int) -> Dict[str, Any]:
        """Fetch palette info."""
        cursor.execute("SELECT * FROM palette WHERE object_id = ?", (object_id,))
        row = cursor.fetchone()
        return dict(row) if row else {}

    def _get_parameter(self, cursor: sqlite3.Cursor, object_id: int) -> Dict[str, Any]:
        """Fetch parameter info."""
        cursor.execute("SELECT attrs FROM parameter WHERE object_id = ?", (object_id,))
        row = cursor.fetchone()
        if row and row["attrs"]:
            return json.loads(row["attrs"])
        return {}

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

            # Parse and merge root_attrs
            if data["root_attrs"]:
                data.update(json.loads(data["root_attrs"]))
            del data["root_attrs"]

            # Fetch all related data
            data["metadata"] = self._get_metadata(cursor, object_id)
            data["inlets"] = self._get_simple_list(cursor, "inlets", object_id)
            data["outlets"] = self._get_simple_list(cursor, "outlets", object_id)
            data["objargs"] = self._get_simple_list(cursor, "objargs", object_id)
            data["methods"] = self._get_methods(cursor, object_id)
            data["attributes"] = self._get_attributes(cursor, object_id)
            data["examples"] = self._get_simple_list(cursor, "examples", object_id)
            data["seealso"] = self._get_seealso(cursor, object_id)
            data["misc"] = self._get_misc(cursor, object_id)
            data["palette"] = self._get_palette(cursor, object_id)
            data["parameter"] = self._get_parameter(cursor, object_id)

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
