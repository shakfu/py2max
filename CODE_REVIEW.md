# Repository Code Review

## Findings

- **High – Python version support mismatch** (`py2max/core.py:117`, `py2max/abstract.py:132`, `py2max/layout.py:246`)
  - The codebase uses PEP 585 generics (e.g., `list[str]`, `dict[str, ...]`) while `pyproject.toml` still declares support for Python 3.7. Importing these modules on 3.7/3.8 raises `TypeError`. Either backport with `from __future__ import annotations` everywhere or raise `requires-python` to 3.9+.

- **High – `add_textbox` ignores Max defaults** (`py2max/core.py:620`)
  - Calls such as `p.add_textbox("ezdac~")` produce boxes with `numinlets=1`, `numoutlets=0`, and `outlettype=[""]`, contradicting Max metadata (should be 0/2). Generated `.maxpat` files are inaccurate and break validation. Pull default inlet/outlet counts and types from `maxref.MAXCLASS_DEFAULTS` before constructing boxes.

- **High – `pitch2freq` contradicts its own contract** (`py2max/utils.py:30`)
  - Function docstring promises support for sharp note names (`"A#3"`), yet `notes.index(pitch[:-1])` fails for sharps and multi-digit octaves. Normalize sharps to flats (or extend the lookup) and parse octaves more robustly.

- **Medium – Columnar layout flag undocumented vs. implementation** (`py2max/core.py:356`)
  - The constructor docstring advertises `layout='columnar'`, but `set_layout_mgr` lacks that branch and raises `NotImplementedError`. Either add an alias to `MatrixLayoutManager` with `flow_direction="column"` or adjust docs/tests to the supported values.

- **Medium – Saving to nested paths can fail** (`py2max/core.py:331`)
  - `save_as` uses `path.parent.mkdir(exist_ok=True)` without `parents=True`, so saving to `outputs/new/demo.maxpat` fails when intermediate directories do not exist. Pass `parents=True` to create nested output directories.

- **Low – `scripts/test.sh` helper is broken** (`scripts/test.sh:7`)
  - `basename -s .py` runs without an argument, so the script aborts before comparing files. Provide the script path (`basename -s .py "$PYSCRIPT"`) or rewrite the helper in Python.

## Open Questions

- Can the project raise its minimum Python version to 3.9, or do downstream users still require 3.7 compatibility?

## Feature Suggestions

1. Auto-populate object metadata (inlets/outlets/types, default rectangles) from `maxref` during box creation and expose a refresh command for legacy patches.

2. Implement the `py2max` console entry point advertised in `pyproject.toml` to streamline CLI-driven patch generation and validation.

3. Add a layout preview command (e.g., `make layout-preview`) that renders PNG/SVG snapshots, helping contributors evaluate new layout strategies without opening Max.
