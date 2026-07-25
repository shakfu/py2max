"""Differential tests for the generated single-file edition.

``scripts/py2max.py`` is an amalgamation of the package produced by
``scripts/build_single_file.py``. These tests assert it behaves *identically* to
the package rather than merely importing: each builder below constructs the same
patch twice -- once with ``py2max``, once with the single file -- and the emitted
JSON must match exactly.

They also guard against the failure that made the previous, hand-maintained
version of that file rot undetected: a stale checked-in copy now fails CI.
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List

import pytest

import py2max

ROOT = Path(__file__).resolve().parent.parent
SINGLE_FILE = ROOT / "scripts" / "py2max.py"
BUILDER = ROOT / "scripts" / "build_single_file.py"


def _load_single_file():
    """Import the single file under a private module name.

    Loaded via importlib rather than a ``sys.path`` insertion on purpose: putting
    ``scripts/`` on the path lets ``scripts/py2max.py`` shadow the real package
    for the rest of the session.
    """
    spec = importlib.util.spec_from_file_location("_py2max_single_file", SINGLE_FILE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["_py2max_single_file"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def single():
    if not SINGLE_FILE.exists():
        pytest.skip("scripts/py2max.py has not been generated")
    return _load_single_file()


# ---------------------------------------------------------------------------
# patch builders, run against both implementations
#
# Each takes the module under test and returns a Patcher. They must use only
# features the single file includes (everything except graph:* layouts, the CLI
# and the SQLite maxref database).

Builder = Callable[[Any], Any]


def build_basic(m: Any) -> Any:
    p = m.Patcher("basic.maxpat")
    osc = p.add_textbox("cycle~ 440")
    gain = p.add_textbox("gain~")
    dac = p.add_textbox("ezdac~")
    p.add_line(osc, gain)
    p.add_line(gain, dac)
    return p


def build_ui_objects(m: Any) -> Any:
    p = m.Patcher("ui.maxpat")
    num = p.add_floatbox()
    msg = p.add_message("1 2 3")
    com = p.add_comment("a comment")
    tog = p.add_textbox("toggle", maxclass="toggle")
    p.add_line(num, tog)
    p.add_line(msg, com)
    return p


def build_containers(m: Any) -> Any:
    p = m.Patcher("containers.maxpat")
    p.add_coll(name="mycoll", dictionary={"1": "a b c"})
    p.add_coll(text="coll explicit @embed 1")
    p.add_dict(name="mydict")
    p.add_table(name="mytable")
    p.add_table(name="mytilde", tilde=True)
    p.add_itable(name="myitable")
    return p


def build_subpatcher(m: Any) -> Any:
    p = m.Patcher("sub.maxpat")
    sub = p.add_subpatcher("p processing")
    inner = sub.subpatcher
    i = inner.add_textbox("inlet")
    o = inner.add_textbox("outlet")
    filt = inner.add_textbox("lores~ 1000 0.5")
    inner.add_line(i, filt)
    inner.add_line(filt, o)
    osc = p.add_textbox("saw~ 110")
    dac = p.add_textbox("ezdac~")
    p.add_line(osc, sub)
    p.add_line(sub, dac)
    return p


def build_semantic_ids(m: Any) -> Any:
    p = m.Patcher("semantic.maxpat", semantic_ids=True)
    a = p.add_textbox("cycle~ 440")
    b = p.add_textbox("cycle~ 220")
    g = p.add_textbox("gain~")
    p.add_line(a, g)
    p.add_line(b, g)
    return p


def _synth(m: Any, **kwds: Any) -> Any:
    p = m.Patcher("layout.maxpat", **kwds)
    freq = p.add_floatbox()
    osc = p.add_textbox("cycle~ 440")
    vca = p.add_textbox("*~ 0.5")
    filt = p.add_textbox("lores~ 1200 0.4")
    scope = p.add_textbox("scope~", maxclass="scope~")
    dac = p.add_textbox("ezdac~")
    p.add_line(freq, osc)
    p.add_line(osc, vca)
    p.add_line(vca, filt)
    p.add_line(filt, dac)
    p.add_line(filt, scope)
    return p


def build_grid_layout(m: Any) -> Any:
    p = _synth(m, layout="grid", flow_direction="horizontal")
    p.optimize_layout()
    return p


def build_grid_vertical(m: Any) -> Any:
    p = _synth(m, layout="grid", flow_direction="vertical", cluster_connected=False)
    p.optimize_layout()
    return p


def build_flow_layout(m: Any) -> Any:
    p = _synth(m, layout="flow")
    p.optimize_layout()
    return p


def build_columnar_layout(m: Any) -> Any:
    p = _synth(m, layout="columnar")
    p.optimize_layout()
    return p


def build_matrix_layout(m: Any) -> Any:
    p = _synth(m, layout="matrix")
    p.optimize_layout()
    return p


def build_param_placement(m: Any) -> Any:
    p = _synth(m, layout="flow", param_placement=True)
    p.optimize_layout()
    return p


def build_editing(m: Any) -> Any:
    p = m.Patcher("editing.maxpat")
    a = p.add_textbox("cycle~ 440")
    b = p.add_textbox("gain~")
    c = p.add_textbox("ezdac~")
    p.add_line(a, b)
    p.add_line(b, c)
    p.remove_line(p._lines[0])
    p.remove_box(b)
    d = p.add_textbox("saw~ 220")
    p.add_line(d, c)
    return p


def build_theming(m: Any) -> Any:
    p = m.Patcher("theme.maxpat")
    box = p.add_textbox("cycle~ 440")
    box.set_color(bg=[0.1, 0.2, 0.3, 1.0], text="red", border="#ff8800")
    p.enable_presentation()
    p.enforce_integer_coords()
    return p


BUILDERS: List[Builder] = [
    build_basic,
    build_ui_objects,
    build_containers,
    build_subpatcher,
    build_semantic_ids,
    build_grid_layout,
    build_grid_vertical,
    build_flow_layout,
    build_columnar_layout,
    build_matrix_layout,
    build_param_placement,
    build_editing,
    build_theming,
]


def _emit(patcher: Any) -> Dict[str, Any]:
    """Render to a plain dict, the way save() would."""
    return json.loads(patcher.to_json())


@pytest.mark.parametrize("builder", BUILDERS, ids=lambda b: b.__name__)
def test_output_matches_package(builder: Builder, single: Any) -> None:
    """The single file must emit byte-identical JSON to the package."""
    assert _emit(builder(py2max)) == _emit(builder(single))


# ---------------------------------------------------------------------------
# maxref-backed behaviour (the shimmed data layer)


@pytest.mark.parametrize(
    "name", ["cycle~", "gain~", "ezdac~", "metro", "umenu", "lores~", "adsr~", "select"]
)
def test_port_counts_match(name: str, single: Any) -> None:
    from py2max import maxref

    assert maxref.get_inlet_count(name) == single.get_inlet_count(name)
    assert maxref.get_outlet_count(name) == single.get_outlet_count(name)
    assert maxref.get_inlet_types(name) == single.get_inlet_types(name)
    assert maxref.get_outlet_types(name) == single.get_outlet_types(name)


CONNECTIONS = [
    ("cycle~", 0, "gain~", 0),
    ("cycle~", 5, "gain~", 0),  # out of range outlet
    ("metro", 0, "cycle~", 0),  # bang into a signal inlet
    ("loadbang", 0, "adsr~", 0),  # bang into a wildcard inlet (legal)
    ("select", 3, "print", 0),  # arg-scaled outlet count
    ("nonexistent.object", 0, "gain~", 0),  # unknown source
]


@pytest.mark.parametrize(
    "conn", CONNECTIONS, ids=lambda c: f"{c[0]}[{c[1]}]->{c[2]}[{c[3]}]"
)
def test_validation_verdicts_match(conn: Any, single: Any) -> None:
    """Connection validation must reach the same verdict, with the same message."""
    from py2max import maxref

    assert maxref.validate_connection(*conn) == single.validate_connection(*conn)


def test_object_defaults_match(single: Any) -> None:
    """MAXCLASS_DEFAULTS drives box geometry, so it must agree object by object."""
    from py2max import maxref

    for name in ["cycle~", "gain~", "ezdac~", "toggle", "dial", "scope~", "flonum"]:
        assert (name in maxref.MAXCLASS_DEFAULTS) == (name in single.MAXCLASS_DEFAULTS)
        assert maxref.MAXCLASS_DEFAULTS.get(name) == single.MAXCLASS_DEFAULTS.get(name)


def test_known_object_coverage(single: Any) -> None:
    """The embedded table must cover the same objects as the package."""
    from py2max import maxref

    assert set(single.get_available_objects()) == set(maxref.get_available_objects())


def test_validation_raises_identically(single: Any) -> None:
    """An invalid connection must raise in both, from the same call."""
    for module in (py2max, single):
        p = module.Patcher("v.maxpat", validate_connections=True)
        osc = p.add_textbox("cycle~ 440")
        gain = p.add_textbox("gain~")
        p.add_line(osc, gain)  # valid
        with pytest.raises(module.InvalidConnectionError):
            p.add_line(osc, gain, outlet=5)


def test_lint_findings_match(single: Any) -> None:
    """lint() must report the same codes for the same defects."""

    def defective(m: Any) -> Any:
        p = m.Patcher("bad.maxpat")
        a = p.add_textbox("metro 500")
        b = p.add_textbox("cycle~ 440")
        p.add_line(a, b)  # control -> signal inlet
        return p

    codes = [sorted(f.code for f in m.lint(defective(m))) for m in (py2max, single)]
    assert codes[0] == codes[1]
    assert codes[0], "expected at least one finding"


def test_structured_info_matches_package(single: Any) -> None:
    """get_info() resolves on maxclass, and must agree with the package for the
    keys the single file carries (prose keys are absent by design)."""
    boxes = [
        (m.Patcher("h.maxpat").add_textbox("toggle", maxclass="toggle"))
        for m in (py2max, single)
    ]
    pkg_info, sf_info = (b.get_info() for b in boxes)
    assert pkg_info is not None and sf_info is not None
    assert len(sf_info["inlets"]) == len(pkg_info["inlets"])
    assert len(sf_info["outlets"]) == len(pkg_info["outlets"])
    assert set(sf_info["methods"]) == set(pkg_info["methods"])
    assert set(sf_info["attributes"]) == set(pkg_info["attributes"])


def test_help_degrades_with_a_pointer(single: Any) -> None:
    """Documentation prose is deliberately absent; say so instead of lying."""
    box = single.Patcher("h.maxpat").add_textbox("toggle", maxclass="toggle")
    assert box.get_info() is not None  # structured data is present
    assert "pip install py2max" in box.help_text()  # prose is not


def test_svg_export_matches_package(single: Any) -> None:
    """SVG export is pure stdlib, so it comes along and must render identically."""
    svgs = [
        builder(m).to_svg_string()
        for m, builder in ((py2max, build_basic), (single, build_basic))
    ]
    assert svgs[0] == svgs[1]
    assert svgs[0].lstrip().startswith("<")


def test_graph_layout_fails_clearly(single: Any) -> None:
    """graph:* needs third-party backends and cannot ship here."""
    with pytest.raises(NotImplementedError, match="graph layouts are not available"):
        single.Patcher("g.maxpat", layout="graph:hola")


# ---------------------------------------------------------------------------
# round-trip and staleness


def test_round_trip_and_edit(tmp_path: Path, single: Any) -> None:
    """Load an existing patch, edit it, and save without id collisions."""
    source = tmp_path / "rt.maxpat"
    build_basic(py2max).save_as(source)

    outputs = []
    for module in (py2max, single):
        p = module.Patcher.from_file(source)
        new = p.add_textbox("*~ 0.5")
        p.add_line(p._boxes[0], new)
        out = tmp_path / f"out-{module.__name__}.maxpat"
        p.save_as(out)
        data = json.loads(out.read_text())
        ids = [b["box"]["id"] for b in data["patcher"]["boxes"]]
        assert len(ids) == len(set(ids)), f"duplicate ids: {ids}"
        outputs.append(data)
    assert outputs[0] == outputs[1]


def test_single_file_is_not_stale() -> None:
    """A stale committed copy must fail here, not rot for five releases."""
    result = subprocess.run(
        [sys.executable, str(BUILDER), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
