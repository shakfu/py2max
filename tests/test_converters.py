import json
import runpy
import sqlite3
from pathlib import Path

from py2max import cli
from py2max.export.converters import maxpat_to_python, maxref_to_sqlite
from py2max import Patcher


DATA_DIR = Path("tests/data")
OUTPUT_DIR = Path("./outputs")


def _load_dict(path: Path) -> dict:
    with path.open(encoding="utf8") as fh:
        return json.load(fh)


def _canonical(path: Path) -> dict:
    patcher = Patcher.from_file(path)
    return patcher.to_dict()


def test_maxpat_to_python_roundtrip(tmp_path: Path):
    source = DATA_DIR / "simple.maxpat"
    script_path = OUTPUT_DIR / "simple_builder.py"
    output_maxpat = OUTPUT_DIR / "roundtrip.maxpat"

    maxpat_to_python(source, script_path, default_output=str(output_maxpat))

    runpy.run_path(str(script_path), run_name="__main__")

    assert output_maxpat.exists()
    assert _canonical(output_maxpat) == _canonical(source)


def test_cli_convert_maxpat_to_python(tmp_path: Path):
    source = DATA_DIR / "simple.maxpat"
    script_path = OUTPUT_DIR / "simple_cli.py"
    output_path = OUTPUT_DIR / "simple_cli.maxpat"

    exit_code = cli.main(
        [
            "convert",
            "maxpat-to-python",
            str(source),
            str(script_path),
            "--default-output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    assert script_path.exists()

    runpy.run_path(str(script_path), run_name="__main__")
    assert output_path.exists()
    assert _canonical(output_path) == _canonical(source)


class DummyMaxRefCache:
    def __init__(self):
        self._data = {
            "cycle~": {
                "digest": "Sinusoidal oscillator",
                "description": "Generates a sine wave",
                "inlets": [],
                "outlets": [],
                "module": "msp",
            },
            "ezdac~": {
                "digest": "Audio output and on/off button",
                "description": "Route audio to the system output",
                "inlets": [],
                "outlets": [],
                "module": "msp",
            },
        }

    @property
    def refdict(self):
        return {
            "cycle~": Path("/fake/msp-ref/cycle~.maxref.xml"),
            "ezdac~": Path("/fake/msp-ref/ezdac~.maxref.xml"),
        }

    def get_object_data(self, name: str):
        return self._data.get(name)


def test_maxref_to_sqlite(monkeypatch, tmp_path: Path):
    from py2max.maxref.db import MaxRefDB
    from py2max.maxref import db as maxref_db

    dummy = DummyMaxRefCache()
    # Patch at the actual module where MaxRefDB imports these functions
    monkeypatch.setattr(maxref_db, "get_object_info", dummy.get_object_data)
    monkeypatch.setattr(
        maxref_db, "get_available_objects", lambda: list(dummy._data.keys())
    )

    db_path = tmp_path / "cache.db"
    count = maxref_to_sqlite(db_path, overwrite=True)

    assert count == len(dummy._data)

    # Use MaxRefDB to query the database
    database = MaxRefDB(db_path)
    assert database.count == len(dummy._data)
    assert "cycle~" in database
    assert "ezdac~" in database

    # Verify data integrity
    cycle = database["cycle~"]
    assert cycle["digest"] == "Sinusoidal oscillator"
    # Category comes from the actual XML data, not our test data
    assert "cycle" in cycle["name"].lower()


def test_cli_convert_maxref_to_sqlite(monkeypatch, tmp_path: Path):
    from py2max.maxref.db import MaxRefDB
    from py2max.maxref import db as maxref_db

    dummy = DummyMaxRefCache()
    # Patch at the actual module where MaxRefDB imports these functions
    monkeypatch.setattr(maxref_db, "get_object_info", dummy.get_object_data)

    db_path = tmp_path / "cli_cache.db"
    exit_code = cli.main(
        [
            "convert",
            "maxref-to-sqlite",
            "--output",
            str(db_path),
            "--names",
            "cycle~",
            "ezdac~",
            "--overwrite",
        ]
    )

    assert exit_code == 0

    # Use MaxRefDB to query the database
    db = MaxRefDB(db_path)
    assert db.count == 2
    assert "cycle~" in db
    assert "ezdac~" in db

    # Verify objects have expected data
    cycle = db["cycle~"]
    assert cycle["digest"] == "Sinusoidal oscillator"
    ezdac = db["ezdac~"]
    assert ezdac["digest"] == "Audio output and on/off button"


def test_maxpat_to_python_with_subpatcher(tmp_path: Path):
    source = DATA_DIR / "nested.maxpat"
    script_path = OUTPUT_DIR / "nested_builder.py"
    output_maxpat = OUTPUT_DIR / "nested_roundtrip.maxpat"

    maxpat_to_python(source, script_path, default_output=str(output_maxpat))
    runpy.run_path(str(script_path), run_name="__main__")

    assert output_maxpat.exists()
    assert _canonical(output_maxpat) == _canonical(source)
