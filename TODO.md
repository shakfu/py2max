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
