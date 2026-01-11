# TODO

## General

- [x] Reverse-engineer a `.maxpat` file and produce python code (using py2max)

- [x] Apply patcher to a pipeline of transformations. Each of these is a function which takes a patcher and returns it transformed in some way. For example apply new layout add automatic comments or change font size.

- [x] Add a `py2max preview` command that exports patch layouts to PNG/SVG to enable offline visual validation without Max.

- [ ] Introduce recipe-driven project scaffolding (e.g., `py2max new --from tutorials/basic.yml`) so contributors can spin up teaching or demo patches from structured descriptors.

- [x] Convert maxref files to an sqlite database, would make sense for local caching (retrieval).

- [ ] Implement nested patchers in the interactive patcher editor

- [ ] Add object groups (can help in layout)

- [ ] Make the colors of the svg similar to Max's colors

- [ ] Run `mypy --strict py2max` and fix all errors.

- [ ] add optional mode where `id==varname` if id is set

- [ ] ensure leaf `box._patcher` is set

- [ ] add combos (pre-combined elements).

- [ ] add groups (grouped elements).

- [ ] add midi inlet / outlets in `add_rnbo`

- [ ] restructure `.add`

- [x] add option to enable semantic ids (e.g. `cycle-1`)

- [ ] add option to convert patchlines to references (send/receive)

- [x] add `find_object_by_id`, `find_object_by_type`

## Server & WebSocket

- [ ] Make WebSocket port configurable independently (currently hardcoded as `port + 1`)

- [ ] Fix race condition in `_debounced_save` - consider snapshot/copy-on-write approach during save

- [ ] Use logging instead of `print()` for session token display; make token display optional

- [ ] Add reconnection logic to `ReplClient` on transient failures

- [ ] Add command history persistence across REPL sessions (could use `ptpython` history file)

- [ ] Move token from HTML source to HttpOnly cookies or server-side session storage

- [ ] Add rate limiting on WebSocket messages to prevent flooding

- [ ] Implement diff-based SVG updates instead of full re-render on every update

## Layout

- [ ] **Auto-Layout Mode**: Implement automatic layout optimization that repositions objects as they are added or connected, eliminating the need for a manual "Apply Layout" button.

  **Components:**
  1. **Change tracking in Patcher**: Track which objects have been added/modified since last layout
  2. **Incremental layout**: Only reposition affected objects (those changed + their connected neighbors) when <30% of objects affected; full layout otherwise
  3. **Auto-layout toggle**: Add `auto_layout` parameter to Patcher (default: False for backward compatibility)
  4. **Server integration**: Add auto-layout toggle in the interactive editor UI
  5. **UI simplification**: Hide/remove "Apply Layout" button when auto-layout is enabled

  **Benefits:**
  - Patches stay organized as you build them
  - Incremental updates are efficient (O(affected) vs O(all) for small changes)
  - Better user experience - no manual layout steps needed

  **Implementation notes:**
  - Base infrastructure for incremental layout already exists in `layout/base.py`
  - `optimize_layout(changed_objects)` already supports incremental mode
  - Need to add `_changed_objects: Set[str]` tracking to Patcher class
  - Auto-trigger `optimize_layout()` after `add_box()` and `add_patchline()` when enabled

- [ ] Anchor certain objects in expected places in the grid. One way of doing it is to specify x,y ratios as percentages of the grid. So if `x` is 0.10 and the grid width is 500, then x is positioned at 50. The following are typical cases:

  - `ezadc~` to top left

  - `ezdac~` to bottom left

  - visualization object (scope, etc.) to bottom right, etc.

- [ ] **GridLayoutManager**: Sort cluster objects by connection count or topological order instead of ID for better visual layout

- [ ] **FlowLayoutManager**: Calculate level widths based on actual content instead of equal distribution

- [ ] **MatrixLayoutManager**: Fix signal chain tracing to handle cycles (early break on `visited` can fragment chains)

- [ ] **MatrixLayoutManager**: Make category row indices configurable instead of hardcoded (categories get compressed if `num_rows < 4`)

- [ ] **MatrixLayoutManager**: Use integer sub-columns instead of float offset hack for column positions

- [ ] Implement auto-scale layout to fit patcher bounds with margin

- [ ] Calculate optimal object sizes based on text length and port counts

- [ ] Replace magic numbers (`3 * pad`, `1.5 * pad`, `0.8 factor`) with named constants

## SVG Export

- [ ] Add optional text truncation with ellipsis for long object names (text can overflow box)

- [ ] Add subpatcher visualization (currently renders as regular boxes without depth indication)

- [ ] Differentiate signal vs message ports visually in SVG export

## MaxRef & Database

- [ ] Add schema versioning for SQLite database (enables migration path when schema changes)

- [ ] Implement FTS5 for better database search (currently uses naive `LIKE '%query%'`)

- [ ] Batch database inserts within single transaction for efficiency

- [ ] Handle non-standard Max installation paths for `.maxref.xml` discovery

- [ ] Add XML schema validation for `.maxref.xml` files to detect malformed files

- [ ] Cache default Rect instance in `get_legacy_defaults` instead of creating new one each call

## Max Classes

Implement more objects: especially containers / objects with state stored in the `.maxpat` file.

- [x] `codebox`

- [ ] `funbuff`

- ...

## CI/CD & Publishing

- [ ] Enable CI on push/PR in `.github/workflows/ci.yml` (currently set to workflow_dispatch only)

- [ ] Update author email in `pyproject.toml` (currently uses placeholder `me@org.me`)

## Documentation

- [ ] Generate and publish API documentation (ReadTheDocs recommended)

- [ ] Add JSDoc documentation to JavaScript files (`interactive.js`)

- [ ] Fix inconsistent logging (mix of `print()` and proper logging)

## Testing

- [ ] Improve `server.py` test coverage (currently 62%, target 80%+)

- [ ] Add integration tests for server/client WebSocket communication
