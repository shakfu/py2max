"""Static checking of Max box properties.

``BoxProps`` types the keyword properties that reach a ``.maxpat``, so a
misspelled name or a wrongly-typed value is a type error instead of a key
silently written into the patch. These tests run ``mypy`` in a subprocess
because the guarantee under test is a *static* one -- nothing about it is
observable at runtime, so an ordinary assertion cannot see it.

They are slower than the rest of the suite (one mypy process per case, sharing a
warm cache). That is the honest cost of testing a type-level guarantee rather
than asserting it in a docstring.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

import pytest

from py2max.core.props import BOX_PROP_NAMES, BoxProps, TextboxProps

ROOT = Path(__file__).resolve().parent.parent
GENERATOR = ROOT / "scripts" / "gen_box_props.py"

PRELUDE = """from py2max import Patcher
from py2max.core.box import Box

p = Patcher("x.maxpat")
"""


def run_mypy(code: str, tmp_path: Path) -> Tuple[int, str]:
    """Type-check a snippet, returning ``(exit_code, output)``."""
    snippet = tmp_path / "snippet.py"
    snippet.write_text(PRELUDE + code)
    result = subprocess.run(
        # --no-color-output: these assertions match on message text, and mypy
        # honours a FORCE_COLOR inherited from the developer's shell.
        [sys.executable, "-m", "mypy", "--strict", "--no-color-output", str(snippet)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout + result.stderr


# (id, code, fragment the error must mention)
REJECTED: List[Tuple[str, str, str]] = [
    (
        "misspelled-on-add_textbox",
        'p.add_textbox("cycle~ 440", bgcolour=[0.0, 0.0, 0.0, 1.0])',
        'Unexpected keyword argument "bgcolour"',
    ),
    (
        "misspelled-on-Box",
        'Box(maxclass="newobj", bgcolour=[0.0, 0.0, 0.0, 1.0])',
        'Unexpected keyword argument "bgcolour"',
    ),
    (
        "misspelled-on-add_message",
        'p.add_message("hi", texcolor=[0.0, 0.0, 0.0, 1.0])',
        'Unexpected keyword argument "texcolor"',
    ),
    (
        "wrong-type",
        'p.add_textbox("cycle~ 440", fontsize="twelve")',
        'Argument "fontsize"',
    ),
    (
        "wrong-type-on-add_comment",
        'p.add_comment("note", fontsize=[12])',
        'Argument "fontsize"',
    ),
    (
        "explicit-none-for-optional",
        'p.add_textbox("cycle~ 440", varname=None)',
        'Argument "varname"',
    ),
]


@pytest.mark.parametrize("case", REJECTED, ids=[c[0] for c in REJECTED])
def test_mypy_rejects(case: Tuple[str, str, str], tmp_path: Path) -> None:
    """Each failure mode must be a type error, not a silently emitted key."""
    _, code, fragment = case
    returncode, output = run_mypy(code, tmp_path)
    assert returncode != 0, f"mypy accepted it:\n{output}"
    assert fragment in output, output


def test_mypy_accepts_correct_usage(tmp_path: Path) -> None:
    """The vocabulary must not be so strict that real code stops checking."""
    returncode, output = run_mypy(
        """
p.add_textbox("cycle~ 440", bgcolor=(0.1, 0.2, 0.3, 1.0), fontsize=12, varname="osc1")
p.add_textbox("gain~", presentation=1, presentation_rect=[0.0, 0.0, 10.0, 10.0])
p.add_message("1 2 3", hidden=1)
p.add_comment("a note", fontname="Arial")
Box(maxclass="toggle", varname="tgl", bgcolor=[1.0, 1.0, 1.0, 1.0])
""",
        tmp_path,
    )
    assert returncode == 0, output


def test_the_overlap_trap_is_absent() -> None:
    """A TypedDict key colliding with a parameter name silently disables checking.

    mypy reports "Overlap between argument names and ** TypedDict items" and then
    stops checking calls to that function altogether -- the failure mode is a
    quiet loss of coverage, so assert the error never appears.
    """
    result = subprocess.run(
        [sys.executable, "-m", "mypy", "--no-color-output", "py2max"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert "Overlap between argument names" not in result.stdout, result.stdout


def test_structural_keys_are_not_in_the_vocabulary() -> None:
    """Keys taken as explicit parameters must be absent, or the trap above fires."""
    for name in ("maxclass", "numinlets", "numoutlets", "id", "patching_rect"):
        assert name not in BoxProps.__annotations__
    for name in ("text", "outlettype", "comment", "comment_pos"):
        assert name not in TextboxProps.__annotations__


def test_textbox_props_is_a_subset_of_box_props() -> None:
    """The narrower dict must flow into the wider one when kwds are forwarded."""
    assert set(TextboxProps.__annotations__) <= set(BoxProps.__annotations__)


def test_vocabulary_covers_what_the_library_writes() -> None:
    """Every property py2max itself emits must be in the vocabulary.

    Regression test for the gap that maxref alone leaves: ``bpatcher`` documents
    12 attributes but not ``viewvisibility``, which py2max writes and Max
    accepts.
    """
    assert "viewvisibility" in BOX_PROP_NAMES
    assert "rnbo_classname" in BOX_PROP_NAMES


def test_vocabulary_covers_the_fixture_corpus() -> None:
    """No key in a real .maxpat may be missing, or round-tripping would not check."""
    import json

    keys: set[str] = set()

    def walk(patcher: dict) -> None:
        for entry in patcher.get("boxes", []):
            box = entry.get("box", {})
            keys.update(box.keys())
            if "patcher" in box:
                walk(box["patcher"])

    for path in sorted((ROOT / "tests").rglob("*.maxpat")):
        with open(path, encoding="utf8") as f:
            walk(json.load(f)["patcher"])

    structural = {
        "id",
        "maxclass",
        "numinlets",
        "numoutlets",
        "patching_rect",
        "patcher",
    }
    missing = {k for k in keys - structural if k.isidentifier()} - set(BOX_PROP_NAMES)
    assert not missing, f"fixture keys missing from BoxProps: {sorted(missing)}"


def test_generated_file_is_not_stale() -> None:
    """props.py is generated; a stale copy must fail here."""
    result = subprocess.run(
        [sys.executable, str(GENERATOR), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
