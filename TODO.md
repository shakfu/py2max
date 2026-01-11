# TODO

## High Priority

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

- [ ] Move session token from HTML source to HttpOnly cookies
- [ ] Add rate limiting on WebSocket messages
- [ ] Fix race condition in `_debounced_save` (use snapshot during save)

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

- [ ] Make WebSocket port configurable (currently hardcoded as `port + 1`)
- [ ] Add REPL reconnection logic on transient failures
- [ ] Add command history persistence across sessions
- [ ] Implement diff-based SVG updates (not full re-render)
- [ ] Use proper logging instead of `print()` for tokens

### SVG Export

- [ ] Text truncation with ellipsis for long names
- [ ] Subpatcher visualization (show depth indication)
- [ ] Differentiate signal vs message ports visually
- [ ] Match Max's color scheme

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
- [ ] Update author email in `pyproject.toml`
- [ ] Run `mypy --strict` and fix all errors

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
