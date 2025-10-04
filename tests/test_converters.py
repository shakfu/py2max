import json
import runpy
import sqlite3
from pathlib import Path

from py2max import cli
from py2max.converters import maxpat_to_python, maxref_to_sqlite
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
    dummy = DummyMaxRefCache()
    monkeypatch.setattr("py2max.converters.MaxRefCache", lambda: dummy)

    db_path = tmp_path / "cache.db"
    count = maxref_to_sqlite(db_path, overwrite=True)

    assert count == len(dummy._data)

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT name, category, digest FROM maxref ORDER BY name"
        ).fetchall()
    finally:
        conn.close()

    assert len(rows) == len(dummy._data)
    assert rows[0][0] == "cycle~"
    assert rows[0][1] == "msp"


def test_cli_convert_maxref_to_sqlite(monkeypatch, tmp_path: Path):
    dummy = DummyMaxRefCache()
    monkeypatch.setattr("py2max.converters.MaxRefCache", lambda: dummy)

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
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT name, category FROM maxref ORDER BY name"
        ).fetchall()
    finally:
        conn.close()

    assert len(rows) == 2
    assert all(row[1] == "msp" for row in rows)


def test_maxpat_to_python_with_subpatcher(tmp_path: Path):
    source = DATA_DIR / "nested.maxpat"
    script_path = OUTPUT_DIR / "nested_builder.py"
    output_maxpat = OUTPUT_DIR / "nested_roundtrip.maxpat"

    maxpat_to_python(source, script_path, default_output=str(output_maxpat))
    runpy.run_path(str(script_path), run_name="__main__")

    assert output_maxpat.exists()
    assert _canonical(output_maxpat) == _canonical(source)
