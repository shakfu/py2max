# TODO

## High Priority

### M4L / .amxd Support (issue #9)

- [x] **.amxd read/write** — implemented in `py2max/amxd.py`; `Patcher.save()` / `from_file()` auto-detect the `.amxd` extension. Verified in Max 9 (issue #9).

- [x] **M4L presentation-mode helpers + integer-coordinate guardrail** — `py2max/m4l.py`: `Box.add_to_presentation(rect)`, `Patcher.enable_presentation(devicewidth=...)`, `Patcher.enforce_integer_coords()`, plus `M4L_PRESENTATION_UI_CLASSES` / `M4L_INFRASTRUCTURE_CLASSES` with rejection of infrastructure objects and float-coord rounding warning (issue #9).

- [x] **Ship prebuilt maxref JSON in the wheel (fix Linux)** — `py2max/maxref/data/bundle.json.gz` (1175 objects, ~1 MiB compressed) is bundled in the wheel. `MaxRefCache._get_refdict()` falls back to it when no local Max install is found, pre-seeding `_cache` with full parsed data. Regenerate with `uv run python scripts/build_maxref_bundle.py` on a Max-equipped machine. See https://github.com/shakfu/py2max/issues/9

### Auto-Layout Mode

Implement automatic layout optimization that repositions objects as they are added or connected.

**Components:**
1. Change tracking in Patcher (`_changed_objects: Set[str]`)
2. Auto-trigger `optimize_layout()` after `add_box()` and `add_patchline()`
3. Add `auto_layout` parameter to Patcher (default: False)
4. Server integration with UI toggle
5. Hide "Apply Layout" button when auto-layout enabled

**Notes:** Base infrastructure exists in `layout/base.py` - `optimize_layout(changed_objects)` already supports incremental mode.

### Server Security & Reliability

> **Moved to the separate [`py2max-server`](https://github.com/shakfu/py2max-server) package** (0.3.0). The interactive server and REPL no longer live in this repo; track these there. The RPC REPL now requires token authentication.

- [ ] Move session token from HTML source to HttpOnly cookies *(py2max-server)*
- [ ] Add rate limiting on WebSocket messages *(py2max-server)*
- [ ] Fix race condition in `_debounced_save` (use snapshot during save) *(py2max-server)*

### Database Improvements

- [ ] Add schema versioning for SQLite (enables migrations)
- [ ] Implement FTS5 for search (replace naive `LIKE '%query%'`)

### Validation, Linting & Error-Checking (headline focus)

Layout is in good shape after the last few releases; **validation is now the weak
link and the focus of the next cycle.** The goal is that a patch built with
py2max is *correct by default*: obvious Max errors (bad connections, out-of-range
ports, off-canvas or overlapping objects, orphaned lines) are caught
automatically, without the user opting in.

**Current gaps (evidence, mostly from the 0.3.3 cycle):**

- Connection validation is **off by default** (`Patcher.__init__` `validate_connections=False`, `core/patcher.py`), contradicting the docs/CLAUDE.md prose ("enabled by default").
- The type check in `maxref.validate_connection` (`maxref/parser.py`) is **one-directional**: it rejects signal-outlet -> non-signal-inlet, but *not* control-outlet -> signal-only-inlet. So `metro -> cycle~` (a bang into a signal inlet, which Max rejects with "error connecting outlet ... to ... inlet") passes validation even when enabled.
- The **maxref type data it rests on is unreliable**: placeholder types (`OUTLET_TYPE`/`INLET_TYPE` for `metro`, `loadbang`, `noise~`, `flonum`, ...), arg-dependent port counts not modeled (`limi~ 2` really has 2 in/out; maxref reports 1), dynamic ports not handled (`bpatcher`, subpatch `inlet`/`outlet`), and mis-typings (`cycle~` phase inlet is typed `signal/float` but is signal-only in Max).
- **Nothing checks patch-level health**: out-of-range outlet/inlet indices (Max silently deletes the patchcord), object overlaps, objects outside the patcher window, orphaned/dangling patchlines, duplicate IDs.
- **Tests verify JSON shape, not Max-validity** -- the overlap / off-canvas / invalid-connection bugs fixed in 0.3.3 all shipped under ~99% coverage because nothing asserted the generated patches were Max-legal.

**Target end-state:** every built/saved patch is checked automatically (warnings by default, `strict=True` raises on errors), backed by a `Patcher.lint()` that returns structured findings, underpinned by trustworthy maxref message-type data, and enforced in CI so the whole test corpus stays lint-clean.

**Status (landed 0.3.4-dev / Unreleased):** the core of all five phases shipped --
`py2max/maxref/porttypes.py` (message-type model + arg-aware counts + curation),
message-type-aware `validate_connection`, `Patcher.lint()` / `py2max.lint` with the
full code set, lint-on-save (warn by default; `strict=True` raises), the `py2max
validate` CLI, and golden/lint tests (`test_validation.py`, `test_lint.py`).
Design note: rather than regenerate the bundle to fix raw placeholder types (Phase 1)
and flip `validate_connections=True` to raise-by-default (Phase 4), port typing is
normalized/curated at query time and on-by-default checking is delivered via
lint-on-save warnings -- the warn-then-raise transition this plan called for.
Arg-dependent counts now cover both value-scaled (`limi~ 2`) and arg-count-scaled
(`select` / `route` / `pack` / `unpack` / `selector~` / `switch`) objects; a
corpus test (`test_examples.py::TestExamplePatchesLintClean`) re-lints every
shipped example patch and fails on any error; subpatcher/bpatcher port counts are
derived from contained `inlet`/`outlet` objects; and `lint()` recurses into nested
subpatchers with path-qualified findings.
Inlet acceptance is now derived from each object's `<methodlist>` (its real
message vocabulary), which resolves the control-port typing problem without the
raw `type` attribute: `INLET_TYPE`/`OUTLET_TYPE` are placeholders in Max's *own*
XML, so regeneration cannot fix them -- but the method list is present and now
drives validation (`cycle~` has no `bang` method -> rejected; `adsr~` has
`anything` -> allowed). `bundle.json.gz` was regenerated (content-identical to
the shipped snapshot -- it already matched this Max install) and a
`test_bundle_method_data_quality` guard was added.
**Still open:** once field experience confirms the method-list validation is
false-positive-free, consider flipping validation to raise-by-default. Outlet
*emission* typing is still curated (not in the XML's structured data); expand the
curated `_OUTLET_EMIT` set as needed.

#### Phase 1 -- Trustworthy port/type data (foundation)

Validation is only as good as this data; do it first.

- [ ] Classify every port by **message type**, not the current placeholder strings: `signal`, `signal/float`, and control kinds (`bang` / `int` / `float` / `list` / `symbol`). Kill `OUTLET_TYPE` / `INLET_TYPE` (`maxref/parser.py` type extraction, ~L665).
- [ ] Model **arg-dependent port counts** (`limi~ N`, `mc.*`, `matrix~`, `zl` group, etc.) -- derive from the box's own args/attrs, not the fixed maxref entry.
- [ ] Handle **dynamic-I/O objects** (`bpatcher`, `patcher`/subpatch inlets from contained `inlet`/`outlet`, `js`) -- derive counts from actual content; extend the existing `DYNAMIC_IO_MAXCLASSES` path in `core/factory.py`.
- [ ] Audit and correct **signal-only inlets** (e.g. `cycle~` phase, `gain~`/`lores~` inlet 0, MSP right inlets) that maxref currently reports as `signal/float`.
- [ ] Regenerate `maxref/data/bundle.json.gz`; add a data-quality test that fails on any remaining placeholder type.

#### Phase 2 -- Message-type-aware connection validation

- [ ] Replace the one-directional signal check in `maxref.validate_connection` with a **bidirectional message-type compatibility matrix**: `signal->signal` ok; `int|float->(signal/float | number-accepting)` ok; `bang->(bang-accepting: counter, adsr~, flonum, ...)` ok; `bang|number->signal-only inlet` **error**; `signal->control-only inlet` **error**.
- [ ] Keep index-bounds checks and treat **out-of-range outlet/inlet as a hard error** (Max deletes the patchcord on load).
- [ ] Separate "**unknown object -> cannot validate**" (skip/warn) from "**known-invalid**" (error); decide the policy for maxref-unknown maxclasses.

#### Phase 3 -- Patch-level linter (`Patcher.lint()`)

- [ ] `lint() -> list[Finding]` where `Finding` carries `severity` (error/warning), `code`, `message`, and object/line refs. Suggested codes: `E-OUTLET-RANGE`, `E-INLET-RANGE`, `E-CTRL-TO-SIGNAL`, `E-SIGNAL-TO-CTRL`, `E-ORPHAN-LINE`, `E-DUP-ID`, `W-OVERLAP`, `W-OFFCANVAS`, `W-UNKNOWN-OBJECT`.
- [ ] Checks: (a) connection validity (Phase 2), (b) out-of-range ports, (c) orphaned/dangling patchlines, (d) duplicate object IDs, (e) dimension-aware object overlaps, (f) objects outside the patcher window `rect`, (g) unknown maxclass. (a)-(g) are exactly the ad-hoc scans that surfaced the 0.3.3 bugs -- productize them.
- [ ] Wire into the CLI: extend `cmd_validate` (`py2max validate`) to report lint findings with severities and a non-zero exit on errors.

#### Phase 4 -- On-by-default policy & UX (subsumes the old "Connection Validation Default" item)

- [ ] **Lint automatically on `save()` / `to_dict()`** -- warnings emitted by default (no exception); a `strict=True` (or `validate_connections=True`) path raises `InvalidPatchError` on any error-severity finding.
- [ ] Flip connection validation on by default (or route it through the linter). Treat as a **breaking change** and audit the fallout first:
  - **Backwards compatibility**: patches that silently build invalid/maxref-unknown connections would start failing. Survey the test suite, `tests/examples/`, and reverse-engineered/round-tripped patches for connections that would newly error.
  - **maxref coverage gaps**: validation no-ops for objects with no maxref entry; decide whether unknown objects warn or are silently allowed.
  - **Dynamic-I/O**: confirm codebox / `bpatcher` / subpatch paths don't reject legitimate patches under the stricter default.
  - **False positives**: gate the flip on Phase 1 data quality -- do not turn on strict checking while the type data still misfires.
  - **Migration / UX**: prefer a warn-then-raise transition window; document the opt-out; add a CHANGELOG breaking-change entry; fix the docs/CLAUDE.md "enabled by default" discrepancy.

#### Phase 5 -- Test / CI enforcement (close the confidence gap)

- [ ] CI scan: **every generated `.maxpat` in the corpus must be lint-clean** (zero error-severity findings) -- the exact checks that would have caught the 0.3.3 overlap / off-canvas / invalid-connection regressions.
- [ ] Golden tests for the message-type matrix (`metro -> cycle~` rejected, `flonum -> cycle~` accepted, `saw~` inlet 1 signal-only, out-of-range outlet rejected, ...).
- [ ] A deliberately-invalid fixture patch that asserts each lint `code` fires exactly once.

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

### Server & WebSocket

> **Moved to [`py2max-server`](https://github.com/shakfu/py2max-server)** (0.3.0).

- [ ] Make WebSocket port configurable (currently hardcoded as `port + 1`) *(py2max-server)*
- [ ] Add REPL reconnection logic on transient failures *(py2max-server)*
- [ ] Add command history persistence across sessions *(py2max-server)*
- [ ] Implement diff-based SVG updates (not full re-render) *(py2max-server)*
- [ ] Use proper logging instead of `print()` for tokens *(py2max-server)*

### SVG Export

- [~] Text truncation with ellipsis for long names — intentionally **not** done: Max objects size to their text and never truncate, so truncating would be less faithful (and would hide info).
- [x] Subpatcher visualization (show depth indication) — subpatcher boxes are tinted.
- [x] Differentiate signal vs message ports visually — signal ports green, control dark; signal cables thicker/distinct.
- [x] Match Max's color scheme — light patcher background + Max-like box/port/cable palette.

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
- [ ] Add JSDoc to `interactive.js`
- [ ] Fix inconsistent logging (`print()` vs logger)

### Testing

- [ ] Improve server test coverage (62% -> 80%+)
- [ ] Add WebSocket integration tests

### CI/CD

- [ ] Enable CI on push/PR (currently workflow_dispatch only)
- [x] Update author email in `pyproject.toml` — intentionally kept the `users.noreply.github.com` privacy address; `maintainers` added.
- [x] Run `mypy --strict` and fix all errors — whole package passes `mypy --strict`; `[tool.mypy] strict = true` enforces it.

### From REVIEW.md — Strategic (P3)

Deferred; each is a sizeable, self-contained effort.

- [ ] **gen~/RNBO codebox DSL** — a small DSP-graph DSL that emits `codebox` text, turning py2max into a code-generation backend (`add_gen`/`add_codebox`/`add_rnbo` already exist as targets).
- [ ] **Declarative patch DSL / YAML recipes** — see "Recipe-driven scaffolding" above (`py2max new --from tutorials/basic.yml`).
- [ ] **Publish API docs (ReadTheDocs)** — see Documentation above.

### From REVIEW.md — Code-quality polish (low value)

- [ ] `maxref/db.py`: whitelist the f-string-interpolated table/column names (`_insert_inlets_outlets`, `_delete_related_records`, `_get_simple_list`) and escape `%`/`_` in `LIKE` search terms. Not currently exploitable (identifiers are internal constants); largely superseded by the planned FTS5 migration.
- [ ] `exceptions.py`: trim ~40% — several exception classes (`InvalidPatchError`, `InternalError`, `DatabaseError.operation`) have no raisers. Low value; check for external imports before removing.

---

## Completed

<details>
<summary>Click to expand completed items</summary>

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
