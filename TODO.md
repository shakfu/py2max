# TODO

## High Priority

### Auto-layout: server-side follow-up

The core prerequisite shipped (see Completed: incremental layout API is now
reachable). Everything remaining is **live-editing policy that belongs in
[`py2max-server`](https://github.com/shakfu/py2max-server)**, which owns the
structured `create_object` / `create_connection` handlers and can call
`optimize_layout({new_id})` directly. A `_changed_objects` accumulator in core
was considered and dropped: the server's structured edit handlers already hold
the changed id at edit time (nothing to accumulate), and the REPL/`eval` path has
no per-mutation visibility to populate one.

**Caveat before the server flips incremental on for grid/flow:** no manager
overrides `_incremental_layout` -- the base implementation is a generic
overlap-avoidance nudge, not the manager's own algorithm on a subset, so
incremental output drifts from full-layout output. Matrix/columnar ignore
`changed_objects` entirely and always recompute. Native per-manager incremental
layout is a separate, larger, unscoped effort.

### Validation follow-ups

The message-type validation + linter cycle shipped in 0.3.4 (see Completed).
Two items remain, both gated on field experience:

- [ ] Flip connection validation to raise-by-default once the method-list
  validation is confirmed false-positive-free. Treat as a **breaking change**:
  survey `tests/`, `tests/examples/`, and round-tripped patches for connections
  that would newly error; decide unknown-object policy (warn vs. allow); add a
  CHANGELOG breaking-change entry; fix the docs/CLAUDE.md "enabled by default"
  discrepancy.
- [ ] Expand the curated `_OUTLET_EMIT` set (`maxref/porttypes.py`) as gaps
  surface -- outlet *emission* typing is not in the XML's structured data.

### Database Improvements

- [ ] Add schema versioning for SQLite (enables migrations)
- [ ] Implement FTS5 for search (replace naive `LIKE '%query%'`)

---

## Medium Priority

### Layout Managers

| Manager | Issue |
|---------|-------|
| Grid | Sort clusters by connection count, not ID |
| Flow | Calculate level widths from content, not equal distribution |
| Matrix | Fix cycle handling in signal chain tracing |
| Matrix | Make category row indices configurable |
| Matrix | Use integer sub-columns instead of float offset |
| All | Replace magic numbers with named constants |

- [ ] Implement auto-scale to fit patcher bounds with margin
- [ ] Calculate object sizes from text length and port counts
- [ ] Anchor objects by type (e.g., `ezdac~` bottom-left, `scope~` bottom-right)

### MaxRef

- [ ] Handle non-standard Max installation paths
- [ ] Add XML schema validation for `.maxref.xml`
- [ ] Cache default Rect in `get_legacy_defaults`
- [ ] Batch database inserts in single transaction

---

## Low Priority

### Core Features

- [ ] Recipe-driven scaffolding (`py2max new --from tutorials/basic.yml`)
- [ ] Object groups for layout organization
- [ ] Convert patchlines to send/receive references
- [ ] Optional `id == varname` mode
- [ ] Ensure leaf `box._patcher` is set
- [ ] Add combos (pre-combined elements)
- [ ] Add MIDI inlet/outlets in `add_rnbo`
- [ ] Restructure `.add` method

### Max Objects

- [ ] `funbuff`
- [ ] Other container objects with file state

### Documentation

- [ ] Publish API docs (ReadTheDocs)
- [ ] Fix inconsistent logging (`print()` vs logger)

### CI/CD

- [ ] Enable CI on push/PR (currently workflow_dispatch only)

### Strategic (P3)

Deferred; each is a sizeable, self-contained effort.

- [ ] **gen~/RNBO codebox DSL** -- a small DSP-graph DSL that emits `codebox`
  text, turning py2max into a code-generation backend (`add_gen`/`add_codebox`/`add_rnbo`
  already exist as targets).
- [ ] **Declarative patch DSL / YAML recipes** -- see "Recipe-driven scaffolding" above.

### Code-quality polish (low value)

- [ ] `maxref/db.py`: whitelist the f-string-interpolated table/column names
  (`_insert_inlets_outlets`, `_delete_related_records`, `_get_simple_list`) and
  escape `%`/`_` in `LIKE` search terms. Not currently exploitable (identifiers
  are internal constants); largely superseded by the planned FTS5 migration.
- [ ] `exceptions.py`: trim ~40% -- several exception classes (`InvalidPatchError`,
  `InternalError`, `DatabaseError.operation`) have no raisers. Check for external
  imports before removing.

---

## Elsewhere

- The interactive server and REPL live in the separate
  [`py2max-server`](https://github.com/shakfu/py2max-server) package (since 0.3.0);
  those TODO items are tracked in that repo's `TODO.md`.

---

## Completed

<details>
<summary>Click to expand completed items</summary>

### Incremental layout API reachable (Unreleased)

- `Patcher.optimize_layout(changed_objects=None)` now forwards the change set to
  the layout manager; it previously called the manager with no args and always
  forced a full relayout, leaving the incremental engine unreachable through the
  public API. Backward compatible (`None` = full layout). Tests in
  `tests/test_patcher.py` (`test_optimize_layout_forwards_changed_objects`,
  `test_optimize_layout_incremental_leaves_untouched_objects_fixed`).

### Validation, Linting & Error-Checking (0.3.4)

The full five-phase validation plan shipped in 0.3.4:

- `maxref/porttypes.py` -- message-type model, arg-aware port counts (value-scaled
  `limi~ 2` and arg-count-scaled `select`/`route`/`pack`/`unpack`/`selector~`/`switch`),
  and curated typing.
- Message-type-aware `validate_connection`, driven by each object's `<methodlist>`
  (its real message vocabulary) rather than the placeholder `INLET_TYPE`/`OUTLET_TYPE`
  attributes -- `cycle~` has no `bang` method so `metro -> cycle~` is rejected;
  `adsr~` has `anything` so it is allowed.
- `Patcher.lint()` / `py2max.lint` with the full code set (`E-OUTLET-RANGE`,
  `E-INLET-RANGE`, `E-CTRL-TO-SIGNAL`, `E-SIGNAL-TO-CTRL`, `E-ORPHAN-LINE`,
  `E-DUP-ID`, `W-OVERLAP`, `W-OFFCANVAS`, `W-UNKNOWN-OBJECT`); recurses into
  nested subpatchers with path-qualified findings.
- Lint-on-save (warn by default; `strict=True` raises `InvalidPatchError`).
- Subpatcher/bpatcher port counts derived from contained `inlet`/`outlet` objects.
- `py2max validate` CLI; golden/corpus tests (`test_validation.py`, `test_lint.py`,
  `test_examples.py::TestExamplePatchesLintClean`, `test_bundle_method_data_quality`).
- `bundle.json.gz` regenerated (content-identical to shipped snapshot).

### M4L / .amxd Support (issue #9)

- [x] `.amxd` read/write in `py2max/amxd.py`; `Patcher.save()` / `from_file()`
  auto-detect the `.amxd` extension. Verified in Max 9.
- [x] M4L presentation-mode helpers + integer-coordinate guardrail (`py2max/m4l.py`):
  `Box.add_to_presentation`, `Patcher.enable_presentation`, `Patcher.enforce_integer_coords`,
  plus UI/infrastructure class sets with rejection + float-coord rounding warnings.
- [x] Ship prebuilt maxref JSON in the wheel (fixes Linux) -- `maxref/data/bundle.json.gz`
  (1175 objects, ~1 MiB), used as fallback when no local Max install is found.
  Regenerate with `scripts/build_maxref_bundle.py`.

### SVG Export

- [x] Subpatcher visualization (subpatcher boxes tinted).
- [x] Differentiate signal vs message ports (signal ports green, control dark;
  signal cables thicker).
- [x] Match Max's color scheme (light background + Max-like box/port/cable palette).
- [~] Text truncation with ellipsis -- intentionally **not** done: Max objects size
  to their text and never truncate.

### Tooling

- [x] `mypy --strict` passes across the whole package; `[tool.mypy] strict = true` enforces it.
- [x] Author email / `maintainers` set in `pyproject.toml` (kept the privacy address).

### Earlier

- [x] Reverse-engineer `.maxpat` to Python code
- [x] Transformer pipeline for batch modifications
- [x] SVG preview command (`py2max preview`)
- [x] SQLite database for maxref caching
- [x] Semantic IDs (`cycle_1` instead of `obj-1`)
- [x] `find_object_by_id`, `find_object_by_type`
- [x] `codebox` support
- [x] Nested patcher navigation in editor
- [x] Delta updates for WebSocket (not full state)
- [x] Line crossing minimization (barycenter heuristic)
- [x] Input validation for WebSocket messages
- [x] Incremental layout updates
- [x] ViewBox scaling with aspect ratio
- [x] Patchline animation during layout
- [x] Dagre layout algorithm
- [x] Save As dialog

</details>
