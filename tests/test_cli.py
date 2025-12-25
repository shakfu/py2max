from pathlib import Path

import pytest

from py2max import Patcher
from py2max import cli


def run_cli(args):
    return cli.main(args)


class DummyCache:
    def __init__(self, data):
        self._data = data
        self._refdict = {name: Path(f"{name}.maxref.xml") for name in data}

    @property
    def refdict(self):
        return self._refdict

    def get_object_data(self, name):
        return self._data.get(name)


def test_cli_new_creates_patch(tmp_path: Path):
    target = tmp_path / "demo.maxpat"
    exit_code = run_cli(
        [
            "new",
            str(target),
            "--template",
            "stereo",
            "--layout",
            "vertical",
            "--title",
            "Demo",
        ]
    )

    assert exit_code == 0
    assert target.exists()

    patcher = Patcher.from_file(target)
    assert len(patcher._boxes) >= 3


def test_cli_info_reports_counts(tmp_path: Path, capsys):
    target = tmp_path / "info.maxpat"
    patcher = Patcher(path=target)
    patcher.add_textbox("cycle~ 440")
    patcher.add_textbox("ezdac~")
    patcher.save()

    exit_code = run_cli(["info", str(target)])
    captured = capsys.readouterr().out

    assert exit_code == 0
    assert "Boxes: 2" in captured
    assert "ezdac~" in captured


def test_cli_optimize_writes_output(tmp_path: Path):
    source = tmp_path / "opt.maxpat"
    dest = tmp_path / "optimized.maxpat"
    patcher = Patcher(path=source, layout="grid")
    osc = patcher.add_textbox("cycle~ 440")
    gain = patcher.add_textbox("gain~")
    dac = patcher.add_textbox("ezdac~")
    patcher.link(osc, gain)
    patcher.link(gain, dac)
    patcher.link(gain, dac, inlet=1)
    patcher.save()

    exit_code = run_cli(
        [
            "optimize",
            str(source),
            "--layout",
            "matrix",
            "--flow-direction",
            "horizontal",
            "-o",
            str(dest),
        ]
    )

    assert exit_code == 0
    assert dest.exists()


def test_cli_validate_flags_invalid_connection(tmp_path: Path):
    target = tmp_path / "invalid.maxpat"
    patcher = Patcher(path=target)
    osc = patcher.add_textbox("cycle~ 440")
    dac = patcher.add_textbox("ezdac~")
    patcher.add_line(osc, dac, inlet=2)
    patcher.save()

    exit_code = run_cli(["validate", str(target)])

    assert exit_code == 1


def test_cli_maxref_list(monkeypatch, capsys):
    data = {
        "cycle~": {
            "digest": "Sinusoidal oscillator",
            "description": "Generates a sine wave",
            "methods": {},
        }
    }
    dummy = DummyCache(data)
    monkeypatch.setattr(cli, "MaxRefCache", lambda: dummy)

    exit_code = run_cli(["maxref", "--list"])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "cycle~" in out


def test_cli_maxref_json(monkeypatch, capsys):
    data = {
        "gain~": {
            "digest": "Adjust signal gain",
            "description": "Scales the amplitude of an incoming signal.",
            "methods": {
                "float": {
                    "args": [{"name": "value", "optional": "0", "type": "float"}],
                    "digest": "Set gain",
                    "description": "Set the linear gain multiplier.",
                }
            },
        }
    }
    dummy = DummyCache(data)
    monkeypatch.setattr(cli, "MaxRefCache", lambda: dummy)

    exit_code = run_cli(["maxref", "gain~", "--json"])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert '"digest": "Adjust signal gain"' in out
    assert '"float"' in out


def test_cli_maxref_test_output(monkeypatch, tmp_path, capsys):
    data = {
        "ezdac~": {
            "digest": "Audio output and on/off button",
            "description": "Outputs audio to the system.",
            "inlets": [{"id": "0"}, {"id": "1"}],
            "outlets": [],
            "methods": {},
        }
    }
    dummy = DummyCache(data)
    monkeypatch.setattr(cli, "MaxRefCache", lambda: dummy)

    target = tmp_path / "test_ezdac_maxref.py"
    exit_code = run_cli(["maxref", "ezdac~", "--test", "--output", str(target)])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert target.exists()
    contents = target.read_text()
    assert "def test_ezdac_maxref():" in contents
    assert 'len(data.get("inlets"' in contents
    assert "Wrote test skeleton" in out


def test_cli_maxref_requires_name(monkeypatch, capsys):
    dummy = DummyCache({})
    monkeypatch.setattr(cli, "MaxRefCache", lambda: dummy)

    exit_code = run_cli(["maxref"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Please specify" in captured.err


def test_cli_transform_chain(tmp_path: Path):
    source = tmp_path / "pipeline.maxpat"
    patcher = Patcher(path=source)
    osc = patcher.add_textbox("cycle~ 440")
    dac = patcher.add_textbox("ezdac~")
    patcher.add_line(osc, dac)
    patcher.save()

    dest = tmp_path / "pipeline_out.maxpat"
    exit_code = run_cli(
        [
            "transform",
            str(source),
            "--output",
            str(dest),
            "--apply",
            "set-font-size=24",
            "--apply",
            "add-comment=CLI",
        ]
    )

    assert exit_code == 0
    transformed = Patcher.from_file(dest)
    assert transformed.default_fontsize == 24
    comments = [box for box in transformed._boxes if box.maxclass == "comment"]
    assert comments
    assert all(comment.text == "CLI" for comment in comments)


def test_cli_transform_list(capsys):
    exit_code = run_cli(["transform", "--list-transformers"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "set-font-size" in captured.out


def test_cli_db_create(tmp_path: Path):
    """Test creating a new MaxRefDB database"""
    db_path = tmp_path / "test.db"

    exit_code = run_cli(
        [
            "db",
            "create",
            str(db_path),
            "--category",
            "msp",
        ]
    )

    assert exit_code == 0
    assert db_path.exists()

    # Verify database was populated
    from py2max.maxref.db import MaxRefDB

    db = MaxRefDB(db_path, auto_populate=False)
    assert db.count > 0


def test_cli_db_create_empty(tmp_path: Path):
    """Test creating an empty MaxRefDB database"""
    db_path = tmp_path / "empty.db"

    exit_code = run_cli(
        [
            "db",
            "create",
            str(db_path),
            "--empty",
        ]
    )

    assert exit_code == 0
    assert db_path.exists()

    from py2max.maxref.db import MaxRefDB

    db = MaxRefDB(db_path, auto_populate=False)
    assert db.count == 0


def test_cli_db_populate(tmp_path: Path):
    """Test populating an existing database"""
    db_path = tmp_path / "populate.db"

    # Create empty database first
    run_cli(["db", "create", str(db_path), "--empty"])

    # Populate with specific objects
    exit_code = run_cli(
        [
            "db",
            "populate",
            str(db_path),
            "--objects",
            "cycle~",
            "gain~",
        ]
    )

    assert exit_code == 0

    from py2max.maxref.db import MaxRefDB

    db = MaxRefDB(db_path, auto_populate=False)
    assert db.count == 2
    assert "cycle~" in db
    assert "gain~" in db


def test_cli_db_info(tmp_path: Path, capsys):
    """Test getting database info"""
    db_path = tmp_path / "info.db"

    # Create database with specific objects
    from py2max.maxref.db import MaxRefDB

    db = MaxRefDB(db_path, auto_populate=False)
    db.populate(["cycle~", "gain~"])

    exit_code = run_cli(
        [
            "db",
            "info",
            str(db_path),
            "--summary",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Total objects: 2" in captured.out
    assert "Categories:" in captured.out


def test_cli_db_search(tmp_path: Path, capsys):
    """Test searching database"""
    db_path = tmp_path / "search.db"

    # Create database with specific objects
    from py2max.maxref.db import MaxRefDB

    db = MaxRefDB(db_path, auto_populate=False)
    db.populate(["cycle~", "gain~", "dac~"])

    exit_code = run_cli(
        [
            "db",
            "search",
            str(db_path),
            "cycle",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "cycle~" in captured.out


def test_cli_db_query(tmp_path: Path, capsys):
    """Test querying object details"""
    db_path = tmp_path / "query.db"

    # Create database with specific objects
    from py2max.maxref.db import MaxRefDB

    db = MaxRefDB(db_path, auto_populate=False)
    db.populate(["cycle~"])

    exit_code = run_cli(
        [
            "db",
            "query",
            str(db_path),
            "cycle~",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "cycle~" in captured.out
    assert "Digest:" in captured.out


def test_cli_db_export_import(tmp_path: Path):
    """Test exporting and importing database"""
    db_path = tmp_path / "export.db"
    json_path = tmp_path / "export.json"
    db_path2 = tmp_path / "import.db"

    # Create database
    from py2max.maxref.db import MaxRefDB

    db = MaxRefDB(db_path, auto_populate=False)
    db.populate(["cycle~", "gain~"])

    # Export to JSON
    exit_code = run_cli(
        [
            "db",
            "export",
            str(db_path),
            str(json_path),
        ]
    )
    assert exit_code == 0
    assert json_path.exists()

    # Create new database and import
    run_cli(["db", "create", str(db_path2), "--empty"])
    exit_code = run_cli(
        [
            "db",
            "import",
            str(db_path2),
            str(json_path),
        ]
    )

    assert exit_code == 0
    db2 = MaxRefDB(db_path2, auto_populate=False)
    assert db2.count == 2
    assert "cycle~" in db2
