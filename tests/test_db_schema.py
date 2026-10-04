"""MaxRefDB schema versioning, migrations, and idempotent inserts."""

import sqlite3

import pytest

from py2max.exceptions import DatabaseError
from py2max.maxref import get_object_info
from py2max.maxref.db import MaxRefDB

CHILD_TABLES = ("methods", "method_args", "attributes", "attribute_enums", "inlets")


def _counts(path):
    with sqlite3.connect(path) as conn:
        return {
            t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            for t in CHILD_TABLES
        }


def _version(path):
    with sqlite3.connect(path) as conn:
        return conn.execute("PRAGMA user_version").fetchone()[0]


def test_new_database_is_at_current_version(tmp_path):
    path = tmp_path / "m.db"
    MaxRefDB(path, auto_populate=False)
    assert _version(path) == MaxRefDB.SCHEMA_VERSION


def test_reinserting_an_object_does_not_duplicate_child_rows(tmp_path):
    path = tmp_path / "m.db"
    db = MaxRefDB(path, auto_populate=False)
    data = get_object_info("live.dial")  # has methods, attributes and enums
    db.insert_object("live.dial", data)
    once = _counts(path)
    db.insert_object("live.dial", data)
    assert _counts(path) == once
    assert db.get_object("live.dial")["methods"].keys() == data["methods"].keys()


def test_unversioned_database_is_migrated_and_orphans_purged(tmp_path):
    path = tmp_path / "old.db"
    db = MaxRefDB(path, auto_populate=False)
    db.insert_object("cycle~", get_object_info("cycle~"))
    clean = _counts(path)
    # simulate a pre-versioning cache: version 0 and rows orphaned by REPLACE
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA user_version = 0")
        conn.execute("INSERT INTO methods (object_id, name) VALUES (999, 'stale')")
        conn.execute("INSERT INTO method_args (method_id, name) VALUES (999, 'x')")
    assert _counts(path) != clean

    migrated = MaxRefDB(path, auto_populate=False)
    assert _version(path) == MaxRefDB.SCHEMA_VERSION
    assert _counts(path) == clean
    assert "cycle~" in migrated


def test_newer_database_is_refused(tmp_path):
    path = tmp_path / "new.db"
    MaxRefDB(path, auto_populate=False)
    with sqlite3.connect(path) as conn:
        conn.execute(f"PRAGMA user_version = {MaxRefDB.SCHEMA_VERSION + 1}")
    with pytest.raises(DatabaseError, match="newer than this py2max"):
        MaxRefDB(path, auto_populate=False)


def test_populate_twice_is_idempotent(tmp_path):
    path = tmp_path / "m.db"
    db = MaxRefDB(path, auto_populate=False)
    db.populate(object_names=["cycle~", "live.dial", "metro"])
    once = _counts(path)
    db.populate(object_names=["cycle~", "live.dial", "metro"])
    assert _counts(path) == once
    assert db.count == 3


@pytest.mark.parametrize("names", [["live.dial"], ["cycle~", "metro", "umenu"]])
def test_load_round_trips_export(tmp_path, names):
    src = MaxRefDB(tmp_path / "a.db", auto_populate=False)
    src.populate(object_names=names)
    src.export(tmp_path / "dump.json")
    dst = MaxRefDB(tmp_path / "b.db", auto_populate=False)
    dst.load(tmp_path / "dump.json")
    for name in names:
        assert dst.get_object(name) == src.get_object(name) == get_object_info(name)


def test_get_object_returns_what_was_inserted(tmp_path):
    db = MaxRefDB(tmp_path / "m.db", auto_populate=False)
    data = {
        "name": "custom",
        "digest": "d",
        "inlets": [{"id": "0", "type": "signal"}],
        "objargs": [{"name": "n", "optional": "0", "type": "int"}],
        "attributes": {"size": {"get": "1", "set": "0", "size": "1", "type": "int"}},
        "methods": {},
    }
    db.insert_object("custom", data)
    assert db.get_object("custom") == data


def test_v2_database_is_backfilled_from_maxref(tmp_path):
    path = tmp_path / "v2.db"
    db = MaxRefDB(path, auto_populate=False)
    db.insert_object("cycle~", get_object_info("cycle~"))
    with sqlite3.connect(path) as conn:  # simulate v2: no stored source
        conn.execute("UPDATE objects SET data = NULL")
        conn.execute("PRAGMA user_version = 2")
    migrated = MaxRefDB(path, auto_populate=False)
    assert _version(path) == MaxRefDB.SCHEMA_VERSION
    assert migrated.get_object("cycle~") == get_object_info("cycle~")
