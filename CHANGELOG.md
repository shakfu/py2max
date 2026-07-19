# Changelog

## [Unreleased]

## [0.3.4]

### New: Param docking in layouts

- `Patcher(..., param_placement=True)` docks value/UI "param" objects (`flonum`, `number`, `message`, `toggle`, `slider`, `dial`, `live.*`) next to the single object they drive, instead of spreading them through the signal graph. During `optimize_layout()`, a param whose outgoing connections all go to one non-param target is placed perpendicular to the signal flow -- above the target for a horizontal flow, to its left for a vertical flow (and to the right / below when the flow hugs that edge) -- ordered by, and for a lone param aligned to, the inlet it feeds, then de-overlapped. Works across every built-in layout (grid, flow, columnar, matrix). Off by default; a control that fans out to more than one object is left in the flow. Implemented as `LayoutManager.place_params()`.

### New: Patch linting and message-type-aware connection validation

- Added `Patcher.lint()` (and the `py2max.lint` module: `lint()`, `Finding`) -- a patch-level health check returning structured findings with a `severity`, a `code`, and object/connection references. It covers invalid connections, out-of-range outlet/inlet indices, orphaned patchlines, duplicate IDs, overlapping objects, off-canvas objects, and unknown object classes.
- **Linting runs automatically on `save()`**: error-severity findings (bad connections, out-of-range ports, orphaned lines, duplicate IDs) are logged. Pass `Patcher(strict=True)` to raise `InvalidPatchError` on any error instead. Layout warnings (overlaps / off-canvas / unknown objects) are left to an explicit `lint()` or `py2max validate` to keep normal saves quiet. This is on by default and non-breaking -- saves still succeed unless `strict=True`.
- Connection validation is now **message-type aware and bidirectional**. The previous check only rejected a signal outlet wired into a non-signal inlet; it now also catches a control outlet (a bang from `metro` / `loadbang` / `button`) wired into an oscillator's signal inlet -- e.g. `metro -> cycle~`, which Max rejects. The rules are deliberately conservative (ambiguous cases and maxref-unknown objects are allowed) so on-by-default checking never rejects a valid patch; notably a bang into `adsr~` (a legitimate envelope trigger) is *not* flagged.
- Port typing is now modeled in `py2max/maxref/porttypes.py`, normalizing maxref's placeholder control types (`OUTLET_TYPE` / `INLET_TYPE`) into message kinds, and resolving **argument-dependent port counts** that maxref reports as the arg-less default -- both value-scaled (`limi~ 2` -> 2 in/out) and arg-count-scaled (`select a b c` -> 4 outlets, `route`, `pack`/`unpack`, `selector~`/`switch`) -- plus curated overrides for the handful of objects maxref mis-types.
- `py2max validate` (CLI) now reports the full lint result -- errors and warnings with codes -- and exits non-zero on any error.
- A corpus test re-lints every shipped layout example patch and fails on any error, so Max-invalid wiring can no longer ship unnoticed.
- Subpatchers are handled: a subpatcher/bpatcher box's inlet/outlet count is derived from the `inlet` / `outlet` objects it contains (not the maxref default), and `lint()` recurses into nested patchers -- findings inside a subpatcher are reported path-qualified (e.g. `sub-box-id/obj-1`).
- Inlet acceptance is now derived from each object's `<methodlist>` -- its real message vocabulary in Max's own docs -- rather than the placeholder inlet `type` (Cycling '74 ships `INLET_TYPE`/`OUTLET_TYPE` for control ports, so the type attribute alone is useless). This is what distinguishes a bang into `cycle~` (no `bang` method -> rejected) from a bang into `adsr~` (has an `anything` wildcard method -> allowed), replacing hand-curation with data that generalizes to all ~1050 objects that carry method lists. The shipped `bundle.json.gz` was regenerated so no-Max users get the same data (a `test_bundle_method_data_quality` guard prevents a future regeneration from dropping it).

## [0.3.3]

### Removed: `serve` and `repl` CLI subcommands

- The `py2max serve` and `py2max repl` subcommands -- thin stubs that only pointed at the separate `py2max-server` package since v0.3.0 -- have been removed. The interactive live editor and remote REPL still live in `py2max-server` (`pip install py2max-server`).

### Fixed: Graph layouts (`graph:*`) are overlap-free and open on-screen

- `GraphLayoutManager` now runs the dimension-aware overlap sweep (`prevent_overlaps`) after placement, so constraint/force engines no longer leave large UI objects (e.g. `scope~` at 130x130) overlapping their neighbours -- matching the guarantee the grid/flow managers already gave.
- The patcher window is grown to enclose the laid-out graph plus a margin, so `optimize_layout()` output opens with the whole graph visible instead of spilling past the default 640x480 canvas (the window never shrinks below the default).

### Fixed: Clustered grid layout squashed object sizes

- The connection-aware clustering path of `GridLayoutManager` (`cluster_connected=True`) still wrote the manager's uniform 66x22 size back onto every clustered object, squashing UI objects (`scope~`, `ezdac~`, `dial`, ...) to text-box size. It now preserves each object's real width/height, matching the already-fixed non-clustered path.

### Fixed: Example patches use valid Max connections

- The layout example scripts (`tests/examples/layout/`) and matrix-layout tests wired control objects (`metro`, `loadbang`) straight into oscillator signal inlets, which Max rejects ("error connecting outlet ... to ... inlet"). They now use the correct idiom -- a float number box sets the oscillator frequency, `metro` triggers envelopes, and envelopes modulate amplitude through a `*~` VCA -- so the generated demo patches load cleanly.

### New: `kwds_filter` utility

- Added `py2max.utils.kwds_filter(kwds, **elems)`: returns `kwds` merged with the `elems` whose value is not `None` (legitimate falsy values such as `0` / `""` are kept, and the input is not mutated). Lets a method keep an optional parameter in its signature but omit it from the forwarded `**kwds` when the caller leaves it unset.

### Improved: Build and test-output hygiene

- Coverage HTML now writes to `build/coverage-html` and the test suite writes its artifacts under `build/test-output/` -- both within the git-ignored `build/` tree -- instead of a tracked `outputs/` directory. A new `make test-outputs` target writes all test artifacts flat into `build/test-outputs/` for quick inspection.

## [0.3.2]

### New: Patch editing and removal API

- Loading a patch (`Patcher.from_dict` / `load`) now restores all ID-generation state -- object, node, edge, and semantic-ID counters -- so `add_*` calls made after a load no longer collide with existing object IDs. This fixes the headline "edit an existing patch" round-trip, which previously emitted duplicate IDs on the first post-load add.
- Added a removal / editing API with referential-integrity cleanup: `remove_line` / `disconnect`, `remove_box` / `remove`, and `replace`. Removing a box also prunes its dangling patchlines and clears the associated node/edge/index bookkeeping, so no orphaned lines or stale IDs are left behind.

### New: Graph-layout engines as layout managers

- Three optional graph-layout backends -- HOLA (`hola-graph`), COLA plus force-directed / geometric layouts (`graph-layout`), and OGDF's layered / force-directed / planar layouts (`ogdf-py`) -- are now selectable as first-class layout managers via `layout="graph:<algo>"` (e.g. `graph:hola`, `graph:cola`, `graph:ogdf-sugiyama`). Because these algorithms need the whole graph, positions are applied on `optimize_layout()` rather than as each box is added, and each box's width/height is preserved so UI objects are not squashed. Eleven algorithms are available: `hola`, `cola`, `sugiyama`, `fruchterman-reingold`, `kamada-kawai`, `spectral`, `circular`, `shell`, `ogdf-sugiyama`, `ogdf-fmmm`, `ogdf-planarization`.
- The engines are lazy-imported inside the manager, so `import py2max` still pulls **zero runtime dependencies**; a missing backend raises a clear error naming the package to install. Install with `pip install "py2max[graph]"` -- the `graph` extra now also bundles `hola-graph` alongside `graph-layout` and `ogdf-py`. Implemented as `GraphLayoutManager` in `py2max/layout/external.py`.

### New: Layout gallery generator and docs page

- `scripts/gen_layout_gallery.py` (run via `make gallery`) renders every supported graph layout over one shared sample patch to transparent SVGs under `docs/assets/imgs/`, using py2max's own SVG exporter so the results are directly comparable. Backends that are not installed are skipped rather than failing the run.
- A new published **Layout Gallery** page (`docs/user_guide/layout_gallery.md`, linked in the User Guide navigation) shows the rendered layouts and documents the `graph:<algo>` layout-manager API. The older networkx / graphviz / tsmpy experiments were dropped in favor of the three maintained backends.
- The generator also renders py2max's **built-in** managers (grid, flow, columnar, matrix) via `optimize_layout()` -- no external dependencies -- and the **Layout Managers** guide (`docs/user_guide/layout_managers.md`) now embeds these as inline visuals so each layout strategy can be seen, not just described.

### Fixed: Generation correctness

- `add_coll` / `add_dict` / `add_table` no longer discard a caller-supplied `text` argument when `name` is `None` (an operator-precedence bug that let the fallback string win).
- `add_beap` strips the `.maxpat` suffix correctly; previously `rstrip(".maxpat")` could truncate names such as `drum.maxpat` down to `dru`.
- Parallel patchlines between the same source and destination now receive incrementing `order` values, so they spread apart in Max instead of overlapping.
- Comments created with `comment=` are emitted on every save path (`save_as`, `to_json`, `to_dict`), not only `save()` / `optimize_layout()`.
- Hand-typed objects that are not in the built-in defaults now get one outlet instead of zero, so they can act as a connection source.
- Load/save round-trip no longer injects `autosave` / `dependency_cache` defaults into nested subpatchers the source patch did not have; patches containing subpatchers now round-trip faithfully.

### Fixed: Layout managers

- `layout="columnar"` now works; it previously raised `NotImplementedError` despite being documented.
- Layout optimizers preserve each object's real width and height. UI objects (`scope~`, `dial`, `slider`, `function`, `live.*`, comments) are no longer squashed to text-box size by `optimize_layout()`.
- The managers now share a single directed-graph model (`PatchGraph`) rather than re-deriving adjacency from patchlines in each manager, and object classification no longer carries contradictory category assignments (its context inference uses maxref signal typing with word-boundary matching).

### Improved: maxref bundle loading (lazy and thread-safe)

- In bundle mode (no local Max install), the shipped catalog is no longer eagerly materialized into the cache on first access. The name-to-source map still loads once, but each object is now built from the in-memory bundle on demand, so a single-object query no longer constructs all ~1175 entries. A bundle object whose cache slot is empty is re-materialized from the bundle rather than returning nothing.
- The process-wide maxref cache is now thread-safe: an `RLock` guards the lazy refdict / category-map initialization and cache population, so concurrent `Box.help()` / validation lookups no longer race on first load or mutate the cache unsafely.

### Fixed: maxref outlet digests and parser robustness

- Outlet `<digest>` text is now extracted symmetrically with inlets. A condition bug previously required the `<outlet>` element to have leading text and then stored that text instead of the digest, so outlet descriptions were dropped for almost every object (~2000 digests across ~1093 objects). `Box.help()` / `get_info()` now report outlet descriptions. The shipped offline `bundle.json.gz` was regenerated so bundle-mode users (Linux/Windows/no-Max) get the corrected data.
- A raw `&` in reference prose no longer drops the whole object on parse. Ampersands that do not begin a valid XML entity are escaped before parsing, hardening against `.maxref.xml` markup variations across Max versions (valid entities like `&amp;`, `&quot;`, `&#181;` are left intact).

### Improved: Cross-platform maxref discovery

- Reference-page resolution now honors the `PY2MAX_MAX_REFPAGES` environment override on all platforms and auto-discovers a Windows `refpages` directory, so Windows users with Max installed read live reference data instead of always falling back to the bundled snapshot. A wheel-build test now asserts the offline `bundle.json.gz` actually ships in the built artifact.

### Improved: SVG preview fidelity

- The SVG exporter (`Patcher.to_svg` / `py2max preview`) now renders a more faithful preview instead of a uniform grey schematic:
  - **Box colors are honored.** Colors set via `Box.set_color` / `apply_theme` (`bgcolor`, `bordercolor`, `textcolor`) are drawn, converted from Max's `[r, g, b, a]` floats to CSS.
  - **UI objects get recognizable affordances** rather than an identical rectangle: message boxes draw the right-edge flag notch, `toggle` an X, `button` a circle, number boxes (`flonum` / `number`) the left triangle marker, `dial` a circle with a pointer, and `slider` a thumb bar.
  - **Ports resolve from the box's own `numinlets` / `numoutlets`** (what is written to the `.maxpat`) rather than a maxref lookup. Ports therefore render correctly for objects maxref does not know and without a Max install, and patchline endpoints line up with the ports they connect to (both use the same counts).
- `export_svg_string` now builds the document in memory instead of round-tripping through a temporary file.

### Fixed: Layout classification and overlap resolution

- Object classification (matrix / columnar layouts) is now factored into a clear precedence -- curated functional intent, then maxref signal typing for the unknown audio tail, then name patterns -- with the rationale documented. Curated sets must win because functional categories do not map to raw signal I/O (even `cycle~` exposes a signal inlet, so signal typing alone would call it a processor; `adc~` is an input though it is a signal source). The dead, never-effective `_refine_column_assignments_by_flow` no-op and its call site were removed.
- `LayoutManager.prevent_overlaps` now converges. The previous version cached each object's rect before mutating it (so pushes stopped accumulating) and clamped boxes back inside the canvas (re-introducing the overlaps it had just removed), leaving dense layouts overlapping at the 50-iteration cap. It is replaced with a monotone sweep that pushes each object clear of already-placed ones along the axis of least penetration; it converges in a few passes, early-exits when nothing overlaps, and preserves each object's real size.

### Improved: Patch transformers

- `run_pipeline` now delegates to `compose`, removing a duplicated apply loop and giving the previously-unused (but exported) `compose` helper a real use.
- The `add-comment` transformer's position is now reachable from the CLI: prefix the value with `above|below|left|right:` to place the comment (e.g. `--apply "add-comment=below:tempo"`), defaulting to `above`. A leading token that is not a position is kept as comment text, so `"note: hi"` is left intact.
- Added two transformers backed by existing APIs: `apply-theme` (apply a named color theme -- `light` / `dark` / `blue` / `high-contrast`) and `scale-positions` (scale every object's x/y position by a factor, sizes unchanged).

### Fixed: Converters module cleanup

- Importing `py2max.export.converters` no longer constructs a `Patcher` as an import-time side effect (which pulled in maxref, layout, etc.). The default-attribute set is now computed lazily on first use and cached. Also removed a dead `_infer_category` helper and an unreachable `NotImplementedError` guard (the caller strips subpatcher dicts before that path).

### Removed: Honest CLI help for the moved `serve` / `repl` subcommands

- The `serve` and `repl` subcommands (whose implementations moved to `py2max-server` in 0.3.0) no longer advertise themselves as live in `--help`; they now removed.

### Removed: MaxRefDB deprecated alias methods

- Removed 12 long-deprecated `MaxRefDB` aliases in favor of the canonical API: `populate_from_maxref` / `populate_all_*` -> `populate([category=...])`, `search_objects` -> `search`, `get_objects_by_category` -> `by_category`, `get_all_categories` -> `.categories`, `get_object_count` -> `.count`, and `export_to_json` / `import_from_json` -> `export` / `load`. The database module is already off the import path (lazily loaded, stdlib-only), so this only trims its API surface. Callers, tests, and docs were updated to the canonical names.
- While updating the SQLite demo scripts, also fixed two pre-existing broken examples: `from py2max import MaxRefDB` (correct: `from py2max.maxref import MaxRefDB`) and `create_database(...)` used as a free function (it is `MaxRefDB.create_database(...)`). Both `tests/examples/db/` scripts now run.

### Removed: Obsolete layout experiments and vendored editor assets

- Deleted the old graph-layout experiment tests (`tests/test_layout_hola{1,2,3}`, `test_layout_hola_graph`, `test_layout_networkx{1,2}`, `test_layout_nx_graphviz`, `test_layout_nx_orthogonal`, `test_layout_nx_tsmpy`). They exercised backends that are no longer supported (raw adaptagrams, networkx, pygraphviz, tsmpy) or duplicated the new `GraphLayoutManager` coverage, and only ever skipped. The maintained path is covered by `tests/test_layout_graph_manager.py`.
- Removed the vendored browser libraries under `docs/js/` (SVG.js, WebCola, D3) -- reference copies for the interactive editor that moved to the separate `py2max-server` package in 0.3.0 -- and the stale Sphinx build output under `docs/build/` that predated the MkDocs migration and was being copied into the published site.
- Pruned 30 obsolete design notes from the `docs/notes/` dev journal (REPL, SSE/WebSocket live-preview server, and interactive SVG-editor implementation notes), all for features that moved to `py2max-server`. The 13 still-relevant library/journal notes were kept.

## [0.3.1]

### New: Standalone `gen.codebox~` Support

- `Patcher.add_gen_codebox(code)` adds a self-contained `gen.codebox~` object -- a complete gen patch in a single box that lives directly in a regular Max patcher, distinct from the inner `codebox~` (emitted by `add_codebox`) that belongs inside a `gen~`/`rnbo~` subpatcher. This is the form emitted by gen transpilers. Code newlines are normalized to CRLF as Max expects, and `fontname`/`fontsize` default to the monospaced gen style.
- Inlet/outlet counts are derived automatically from the code (the highest `inN` / `outN` references, floor of 1), matching gen's dynamic-I/O semantics. Explicit `numinlets` / `numoutlets` still override.
- Available via the `add()` string shortcut too: `p.add("gen.codebox~ out1 = in1 * 0.5;")`. The shortcut suits single-line / `;`-terminated code; pass multi-line source to `add_gen_codebox()` directly.
- Connection validation for `gen.codebox~` (and `codebox` / `codebox~`) now bound-checks against the box's own declared inlet/outlet counts rather than the static `.maxref.xml` entry, since codebox I/O is code-dependent. This both allows valid connections to/from wider codeboxes (e.g. from a second outlet) and rejects genuinely out-of-range ones.

## [0.3.0]

### Removed: Interactive Server Split Into `py2max-server` (breaking)

The browser-based live editor and remote REPL have moved to a separate companion package, [`py2max-server`](https://github.com/shakfu/py2max-server), so the core library stays small, offline, and dependency-free.

- Removed `Patcher.serve()` and the `py2max serve` / `py2max repl` CLI commands; those CLI subcommands now print a pointer to `py2max-server`.
- Removed the `[server]` optional-dependency extra (`websockets`, `ptpython`) and the bundled browser assets (`py2max/static/`).
- Install the server features with `pip install py2max-server` and use `py2max-server serve <patch>` / `py2max-server repl …`. The remote REPL now requires token authentication (passed via `--token` or `PY2MAX_REPL_TOKEN`).

### New: `Patcher.encapsulate()`

- `Patcher.encapsulate(boxes, text="p sub")` wraps a selection of boxes into a subpatcher, auto-generating `inlet`/`outlet` objects for any connections that cross the selection boundary and rewiring the parent through the new subpatcher box. Connections wholly inside the selection move into the subpatcher; connections wholly outside it are untouched. Ports are de-duplicated by source, matching how patches are built by hand. Returns the new subpatcher `Box`.

### New: Preset / `pattrstorage` Scaffolding

- `Patcher.add_pattrstorage(name)`, `Patcher.add_autopattr()`, and `Patcher.add_preset_system(name)` (which adds both and wires `autopattr` -> `pattrstorage`) scaffold a Max preset system. Any object with a scripting name (`varname`) or `parameter_enable=1` participates.
- `Patcher.enable_parameter(box, longname, shortname="", ptype=0, initial=None)` turns an existing UI box into a Max parameter (sets `parameter_enable` and the `saved_attribute_attributes`), so it participates in presets and, in a Max for Live device, appears as an automatable parameter.

### New: Keyword-Attribute Validation (`validate_attrs`)

- `Patcher(validate_attrs=True)` warns (`UserWarning`) when an object is given a keyword that is not a known attribute for its Max class -- catching typos like `inital=` for `initial=`. The known set is the object's maxref attributes plus a universal box-attribute whitelist; objects with no maxref entry are skipped. Off by default and warn-only, so it never changes generated output.

### New: Multichannel (`mc.`) / Polyphony Helpers

- `Patcher.add_mc(text, chans=None)` adds a multichannel object, prefixing `mc.` and appending `@chans` (e.g. `add_mc("cycle~ 440", chans=4)` -> `mc.cycle~ 440 @chans 4`).
- `Patcher.add_poly(target, voices=1)` adds a `poly~` object hosting N voices of a target patch.

### Improved: SVG Export (Max-faithful preview)

- The `preview` / `to_svg` output now approximates Max's look: a light patcher background, signal vs message/control **ports colored distinctly** (signal green, control dark), signal **cables drawn thicker and in a distinct color**, and subpatcher boxes tinted so they stand out. Object text is intentionally not truncated, matching Max (objects size to their text).

### Changed: Documentation moved to MkDocs

- Documentation migrated from Sphinx/reStructuredText to **MkDocs + Material + mkdocstrings** (all Markdown, matching the rest of the repo). The API reference is generated from the (now fully typed) docstrings, including `Patcher`'s mixin-provided methods. The changelog and contributing pages are single-source includes of `CHANGELOG.md` / `CONTRIBUTING.md`. Build with `make docs`, preview with `make docs-serve`, publish with `make docs-deploy`. `docs/notes/` is retained as a historical journal but excluded from the published site.

### New: Color / Theme Helpers

- `Box.set_color(bg=..., text=..., border=...)` sets a box's `bgcolor`/`textcolor`/`bordercolor`; each accepts a named color (e.g. `"red"`), a hex string (`"#ff8800"`), or an `[r, g, b(, a)]` float sequence. Returns the box for chaining.
- `Patcher.apply_theme(theme)` applies a color theme to every box (recursing into subpatchers). Built-in themes: `"light"`, `"dark"`, `"blue"`, `"high-contrast"`; or pass a dict of `bg`/`text`/`border` colors.
- `py2max.core.colors` exposes the `MAX_COLORS` named palette and `resolve_color()`.

### Security

- **Removed a misleading path-traversal check** in `Patcher.save_as()`. The previous `..`/`/etc` allowlist was trivially bypassable and gave a false sense of safety; for an offline file generator it provided no real protection. Genuinely unresolvable paths still raise `PatcherIOError`.

### Typed: Full `mypy --strict`

- The entire package is now annotated and passes `mypy --strict`, backing the shipped `py.typed` marker. `[tool.mypy]` enforces `strict = true`. Core has **no runtime dependencies**.

### Changed: Lighter Core Imports

- `import py2max` no longer eagerly imports `sqlite3`, the maxref database layer, or `py2max.m4l`. `MaxRefDB` is now available lazily via `from py2max.maxref import MaxRefDB` (removed from the top-level `py2max` namespace).

### Internal: `Patcher` Decomposition

- Split the ~1660-line `Patcher` class into focused mixins composed via inheritance: object creation (`BoxFactoryMixin` in `core/factory.py`) and serialization (`SerializationMixin` in `core/serialization.py`). The public API is unchanged; adding a new object type now means editing `core/factory.py` rather than the core class.

### Fixed

- Object-name resolution (used by connection validation and object classification) now reads the box `text` property, so it resolves correctly for boxes loaded from a file. Previously it inspected only programmatic kwargs and returned `newobj` for loaded boxes.
- `Box.oid` now returns the trailing numeric part of any id (e.g. `cycle_1` -> 1) instead of raising `ValueError` under `semantic_ids=True`.
- The `py2max` CLI now reports all `Py2MaxError`s (not just `InvalidConnectionError`) as a clean error message instead of leaking a traceback.
- Fixed an `inital` -> `initial` keyword typo in the simple-synthesis tutorial.

### Testing & Tooling

- The test suite is now hermetic: a `conftest.py` autouse fixture isolates each test in a temporary working directory, so relative `outputs/` writes no longer accumulate in the repo. Fixture reads are anchored at the test file.
- Promoted the `.amxd` byte-for-byte fixtures from the gitignored `outputs/` into tracked `tests/data/`, so that verification runs in CI and on fresh checkouts instead of only on the author's machine.
- Repo-wide `ruff` lint and format cleanup.

### New: Max for Live Support (`py2max.m4l`)

Implements [issue #9](https://github.com/shakfu/py2max/issues/9). See [`docs/notes/amxd.md`](https://github.com/shakfu/py2max/blob/main/docs/notes/amxd.md) for the on-disk format, embedded-project block, and verification details.

- **`.amxd` read/write**: byte-for-byte compatible with Max-exported devices; verified against real fixtures and end-to-end in Live 12.
- **Device-type discrimination**: Audio Effect / Instrument / MIDI Effect via `Patcher(device_type=...)` or the `pack_amxd` / `write_amxd` `device_type` argument.
- **Presentation-mode helpers**: `Patcher.enable_presentation(devicewidth=...)`, `Patcher.enforce_integer_coords()`, `Box.add_to_presentation([x, y, w, h])` (rejects M4L infrastructure objects, rounds fractional coords with a warning).
- `Patcher.save()` / `Patcher.from_file()` auto-detect the `.amxd` extension; `.maxpat` path is unchanged.

### Changed: M4L Module Layout & Imports

- All M4L code (binary format + presentation helpers) lives in a single module `py2max/m4l.py`. Previously briefly split as `py2max/amxd.py`.
- M4L symbols are reachable only via `from py2max.m4l import …`; nothing is re-exported from the top-level `py2max` namespace.

### New: Prebuilt MaxRef Bundle (Linux Support)

- Ship `py2max/maxref/data/bundle.json.gz` in the wheel (1175 objects, ~1 MiB compressed, ~7 MiB raw).
- `MaxRefCache._get_refdict()` falls back to the bundle when no local Max installation is found, pre-seeding the parser cache so `Box.help()`, `get_inlet_count`, `get_outlet_count`, and connection validation work identically on Linux.
- Regenerate with `uv run python scripts/build_maxref_bundle.py` on a machine with Max installed; commit the result.
- Bundle stores full parsed data (methods, attributes, inlets/outlets, digests, descriptions) — not a trimmed subset — so introspection parity with macOS/Windows is preserved.

## [0.2.1] - 2026-01-11

### New: Dagre Layout Algorithm

- Added Dagre (Directed Acyclic Graph) as third layout algorithm option alongside WebCola and ELK
- Integrated `dagre-bundle.js` combining graphlib with require shim for browser compatibility
- Added Dagre-specific controls: Ranker (network-simplex, longest-path, tight-tree) and Align options
- Supports all flow directions: top-bottom, bottom-top, left-right, right-left

### Improved: Interactive Editor Visualization

- **ViewBox Scaling**: Dynamic padding (10% of content, min 30px, max 100px) with aspect ratio preservation
- **Port Position Safety**: Added bounds checking with `safeIndex` clamping to prevent invalid port positions
- **Patchline Animation**: Added `animatePatchlines()` method for smooth patchline transitions during layout
- **Layout Centering**: Added `centerLayout()` helper method - all three algorithms now center content within canvas
- **Delta Updates**: Position updates now send only changed box data instead of full patcher state
  - Added `updateBoxPosition()` for efficient single-box DOM updates
  - Added `updateConnectedLines()` to update patchlines without full re-render
  - Significantly reduces bandwidth during drag operations

### Improved: FlowLayoutManager

- **Line Crossing Minimization**: Added `_minimize_crossings()` method using barycenter heuristic
  - Objects within each level are reordered based on average position of connected objects in previous level
  - Reduces visual line crossings for cleaner layouts
- **Negative Position Prevention**: Added bounds clamping and auto-scaling when content exceeds available space
- **Incremental Layout**: Supports `optimize_layout(changed_objects)` for efficient partial updates

### Improved: GridLayoutManager

- Fixed integer division to float division for consistent cluster positioning
- Now uses consistent float spacing within clusters
- **Incremental Layout**: Supports `optimize_layout(changed_objects)` for efficient partial updates

### Improved: WebSocket Server Security

- **Input Validation**: Added comprehensive schema-based message validation
  - `MESSAGE_SCHEMAS` defines required fields and types for each message type
  - `MAX_STRING_LENGTHS` prevents abuse (256 chars for IDs, 10000 for text, 4096 for filepaths)
  - `COORDINATE_BOUNDS` validates positions (-100000 to 100000)
  - Checks for control characters in strings
  - Validates optional fields (outlet/inlet indices 0-255)
  - Validation errors sent back to client as error messages

### New: Save As Dialog

- Added `save_as_required` message type when patcher has no filepath
- Added `handle_save_as()` handler for saving with specified filepath
- Added `showSaveAsDialog()` in JavaScript with filename prompt
- Automatically adds `.maxpat` extension if not provided

### Fixed: ELK Layout

- Fixed "Referenced shape does not exist" errors by validating edges before creating ports
- Ports now created based on actual connections, not just declared counts

### Fixed: Static File Paths

- Fixed 404 error for `interactive.html` by correcting static file path resolution

### Improved: Base LayoutManager

- Added `prevent_overlaps()` method for iterative overlap prevention
- **Incremental Layout System**: Added smart layout optimization that only repositions affected objects
  - `optimize_layout(changed_objects)` accepts optional set of changed object IDs
  - `should_use_incremental()` determines when to use incremental vs full layout (30% threshold)
  - `get_affected_objects()` finds changed objects plus their connected neighbors
  - `_incremental_layout()` repositions only affected objects using spiral search
  - `_find_non_overlapping_position()` finds nearby positions that don't overlap with fixed objects
  - `_full_layout()` for complete layout recalculation (subclasses override)

## [0.2.0]

### Updated: Optional Layout Dependencies

- Updated `pycola` dependency to `graph-layout` package (<https://github.com/shakfu/graph-layout>)
  - Renamed test file from `test_layout_pycola.py` to `test_layout_graph_layout.py`
  - Updated API to use `ColaLayoutAdapter` from `graph_layout` module

- Updated `pyhola` dependency to `hola-graph` package (<https://github.com/shakfu/hola-graph>)
  - Renamed test file from `test_layout_pyhola.py` to `test_layout_hola_graph.py`
  - Updated imports to use `hola_graph._core` module

- Fixed `test_layout_networkx2.py` to properly check for `pygraphviz` dependency
  - Test now correctly skips when pygraphviz is not installed

### Simplified: Optional Dependencies

- Consolidated optional dependencies in `pyproject.toml` to single `server` option
  - Removed `repl` and `all` options
  - `server` now includes both `websockets` and `ptpython`
  - Install with: `pip install py2max[server]`

### New: Interactive Editor - Advanced Layout with SVG.js, WebCola, and D3.js

- Added complete SVG.js (v3.2.5) integration for all SVG manipulation and animation in the interactive editor

- Added WebCola constraint-based force-directed graph layout engine with D3.js (v7) integration

- Added interactive auto-layout controls panel with real-time parameter adjustment

- Added 5 adjustable layout parameters via sliders and controls:
  - **Link Distance** (50-300): Controls spacing between connected objects
  - **Iterations** (10-200): Controls layout quality and convergence
  - **Canvas Width** (400-1600): Adjustable layout area width
  - **Canvas Height** (300-1200): Adjustable layout area height
  - **Avoid Overlaps** (checkbox): Toggle automatic overlap prevention

- Added constraint-based layout system with 4 presets:
  - **None**: Natural force-directed layout without alignment constraints
  - **Horizontal Flow**: Aligns objects in horizontal rows (left-to-right signal flow)
  - **Vertical Flow**: Aligns objects in vertical columns (top-to-bottom signal flow)
  - **Grid**: Strict grid alignment with both row and column constraints

- Added smooth SVG.js animations (500ms ease-in-out) for layout transitions

- Added constraint generation algorithm that analyzes object positions and creates alignment constraints

- Added collapsible controls panel with "Apply Layout" and "Hide" buttons

- Added visual feedback showing active parameters and constraint count

**SVG.js Implementation:**

- Refactored all SVG rendering to use SVG.js declarative API instead of native DOM manipulation
- `initializeSVG()`: Creates SVG canvas and layer groups using SVG.js
- `createBox()`: Renders boxes with rectangles, text, and clipping paths using SVG.js
- `createLine()`: Renders connection lines with hitboxes using SVG.js
- `addPorts()`: Renders inlet/outlet circles using SVG.js
- `autoLayout()`: Animates box movements using SVG.js transforms

**WebCola Integration:**

- Force-directed graph layout with configurable parameters
- Constraint-based positioning using alignment constraints
- Automatic overlap avoidance with adjustable node dimensions
- Handles disconnected graph components gracefully
- Jaccard link lengths for natural connection spacing

**Constraint System:**

- Automatic constraint generation based on object proximity (50px threshold)
- Alignment constraints for horizontal rows (Y-axis alignment)
- Alignment constraints for vertical columns (X-axis alignment)
- Grid constraints combining both row and column alignment
- Real-time constraint application with visual feedback

**Documentation:**

- Added comprehensive `docs/LIBRARIES_INTEGRATION.md` (518 lines)
- Detailed parameter descriptions and effects
- Constraint preset usage examples
- Testing procedures and expected behavior
- Code examples and API documentation
- Performance considerations for different patch sizes

**Demo Scripts:**

- Added `examples/auto_layout_demo.py`: Complex synthesizer with randomized positions (13 objects, 16 connections)
- Hierarchical layout demo: Tree structure with multiple processing layers (12 objects)

**Benefits:**

- Professional animated transitions for all layout operations
- Interactive experimentation with layout parameters
- Structured layouts matching typical Max patch patterns
- Clean, maintainable SVG.js codebase
- Four layout presets for different use cases
- Real-time visual feedback
- Minimal overhead (234KB total: D3 + SVG.js + WebCola, minified)

**Example Usage:**

```bash
# Start interactive editor
py2max serve outputs/auto_layout_demo.maxpat

# In browser:
# 1. Click "Auto-Layout" to show controls
# 2. Adjust Link Distance slider (50-300)
# 3. Select Constraint Preset (Grid/Horizontal/Vertical/None)
# 4. Adjust Iterations for convergence quality
# 5. Click "Apply Layout" to see smooth animations
# 6. Experiment with different parameter combinations
```

### New: Interactive Editor - Nested Patcher Navigation

- Added full nested patcher (subpatcher) navigation support in interactive editor
- Double-click on subpatcher boxes (blue dashed border) to navigate into them
- Navigate back using "Parent" button or ESC key
- Breadcrumb navigation displays current location (e.g., "Main / Oscillator / Envelope")
- Subpatcher boxes are fully interactive: draggable, connectable, deletable
- Visual distinction: subpatcher boxes have blue dashed borders and bold blue text
- Event delegation for reliable double-click detection even with dynamic DOM updates
- Automatic parent reference restoration when loading patches from files

**Server-Side Changes:**

- Modified `get_patcher_state_json()` to include `has_subpatcher` flag and `patcher_path` breadcrumb
- Added `handle_navigate_to_subpatcher()`, `handle_navigate_to_parent()`, `handle_navigate_to_root()` handlers
- Fixed inlet/outlet count detection to use `numinlets`/`numoutlets` attributes from loaded files
- Handler now tracks both `root_patcher` (for saving) and `patcher` (current view)

**Client-Side Changes:**

- Added breadcrumb UI showing patcher hierarchy
- Implemented event delegation for double-click handling on dynamically created boxes
- Fixed object positioning by flattening `patching_rect` into `x`, `y`, `width`, `height`
- CSS styling for subpatcher boxes with distinct visual appearance
- ESC key navigation support

**Core Changes:**

- Modified `Patcher.from_dict()` to set `_parent` references for nested subpatchers when loading from files
- Ensures bidirectional parent-child relationships for proper navigation

**Tests:**

- Added 14 comprehensive tests in `tests/test_nested_patchers.py`
- All tests passing (326 passed, 14 skipped)

**Demo:**

- Added `examples/nested_patcher_demo.py` with three demonstration patches:
  - Synthesizer with nested envelope subpatcher
  - Effects chain with parallel subpatchers
  - Deeply nested hierarchy (6 levels)

### New: SVG Preview Feature

- Added `py2max preview` CLI command for offline visual validation of Max patches

- Added `py2max.svg` module with complete SVG rendering engine (330 lines)

- Added `export_svg()` and `export_svg_string()` functions for programmatic SVG generation

- Added SVG rendering for boxes with type-specific styling:
  - Regular objects: Light gray fill
  - Comments: Yellow fill (#ffffd0)
  - Messages: Medium gray fill

- Added patchline rendering with correct inlet/outlet connection points

- Added optional inlet/outlet port visualization (blue inlets, orange outlets)

- Added automatic port detection from MaxRef metadata via `get_inlet_count()` and `get_outlet_count()`

- Added support for both Rect objects and list/tuple coordinate formats

- Added proper XML text escaping for special characters

- Added automatic viewBox calculation with padding

- Added browser integration with `--open` flag

- Added 17 comprehensive tests covering all SVG functionality

- Added `tests/examples/preview/svg_preview_demo.py` demonstration script

- Added `docs/SVG_PREVIEW.md` complete documentation

**CLI Usage:**

```bash
# Basic preview (saves to /tmp)
py2max preview my-patch.maxpat

# Specify output path
py2max preview my-patch.maxpat -o output.svg

# Custom title
py2max preview my-patch.maxpat --title "My Synth"

# Hide inlet/outlet ports
py2max preview my-patch.maxpat --no-ports

# Open in browser automatically
py2max preview my-patch.maxpat --open

# Combine options
py2max preview synth.maxpat -o docs/synth.svg --title "Synth" --open
```

**Python API:**

```python
from py2max import Patcher, export_svg, export_svg_string

# Create and export
p = Patcher('synth.maxpat', layout='grid')
osc = p.add_textbox('cycle~ 440')
dac = p.add_textbox('ezdac~')
p.add_line(osc, dac)
p.optimize_layout()
export_svg(p, 'synth.svg', title="Simple Synth", show_ports=True)

# Export to string
svg_content = export_svg_string(p, show_ports=True)
```

**Benefits:**

- No Max installation required for visual validation
- High-quality, scalable vector graphics
- Works with all py2max layout managers
- Perfect for CI/CD, documentation, and version control
- Pure Python implementation with no binary dependencies
- Viewable in any web browser

### New: SQLite Database Support

- Added `py2max.db` module with comprehensive SQLite database support for Max object reference data

- Added `MaxRefDB` class for creating, querying, and managing Max object databases

- Added 14 normalized database tables: objects, metadata, inlets, outlets, methods, method_args, attributes, attribute_enums, objargs, examples, seealso, misc, palette, parameter

- Added support for both in-memory and file-based databases

- Added database query API: `search_objects()`, `get_objects_by_category()`, `get_all_categories()`

- Added bidirectional conversion: .maxref.xml → SQLite → JSON

- Added `export_to_json()` and `import_from_json()` methods for database portability

- Added `create_database()` convenience function for database creation and population

- Added category-based population methods: `populate_all_objects()`, `populate_all_max_objects()`, `populate_all_jit_objects()`, `populate_all_msp_objects()`, `populate_all_m4l_objects()`

- Added maxref category helper functions: `get_all_max_objects()`, `get_all_jit_objects()`, `get_all_msp_objects()`, `get_all_m4l_objects()`, `get_objects_by_category()`

- Added category tracking to maxref module (462 Max, 448 MSP, 210 Jitter, 37 M4L objects)

- Added complete test suite with 17 test cases

- Added `examples/maxref_db_demo.py` demonstration script

- Added `examples/category_db_demo.py` category-specific examples

- Added `docs/database.md` API documentation

### Improved: MaxRefDB API Enhancements

**Python API Improvements:**

- Added Pythonic properties: `.count`, `.categories`, `.objects` for cleaner access
- Added magic methods: `len(db)`, `'obj' in db`, `db['obj']`, `repr(db)` for natural Python usage
- Added simplified methods: `populate()`, `search()`, `by_category()`, `export()`, `load()` with cleaner naming
- Added `summary()` method for database statistics with category breakdown
- Maintained full backward compatibility with deprecated methods
- All 18 database tests pass

**CLI Improvements:**

- Added comprehensive `py2max db` subcommand with 7 operations:
  - `db create` - Create new databases with optional category filtering
  - `db populate` - Add objects to existing databases
  - `db info` - Show database information with summary and listing options
  - `db search` - Search objects by text or category with verbose mode
  - `db query` - Get detailed object information (JSON, dict, or human-readable)
  - `db export` - Export database to JSON
  - `db import` - Import JSON data into database
- Updated `convert maxref-to-sqlite` to use MaxRefDB internally
- Added 7 new CLI tests covering all db subcommands
- All 272 tests pass (258 passed, 14 skipped)

**Example Usage:**

```python
# New Pythonic API
db = MaxRefDB('maxref.db')
db.populate(category='msp')
print(len(db))  # Total objects
if 'cycle~' in db:
    cycle = db['cycle~']
results = db.search('filter')
db.export('backup.json')
```

```bash
# New CLI commands
py2max db create msp.db --category msp
py2max db info msp.db --summary
py2max db search msp.db "oscillator" -v
py2max db query msp.db cycle~ --json
py2max db export msp.db backup.json

# Cache management
py2max db cache location
py2max db cache init
py2max db cache clear
```

### New: Automatic Cache System

**Platform-Specific Cache:**

MaxRefDB now automatically creates and populates a cache database on first use:

- **macOS**: `~/Library/Caches/py2max/maxref.db`
- **Linux**: `~/.cache/py2max/maxref.db`
- **Windows**: `~/AppData/Local/py2max/Cache/maxref.db`

**Benefits:**

- One-time population of all 1157 Max objects
- Instant access on subsequent use
- No manual setup required
- Platform-appropriate cache location

**New Static Methods:**

- `MaxRefDB.get_cache_dir()` - Get platform-specific cache directory
- `MaxRefDB.get_default_db_path()` - Get default database path

**Updated API:**

- `MaxRefDB()` - Now uses cache by default
- `MaxRefDB(db_path, auto_populate=True)` - Control auto-population
- `MaxRefDB(':memory:')` - In-memory database (no caching)

**New CLI Commands:**

- `py2max db cache location` - Show cache location and status
- `py2max db cache init` - Manually initialize cache
- `py2max db cache clear` - Clear cache database

**Example Usage:**

```python
# Automatic caching (default)
from py2max.db import MaxRefDB
db = MaxRefDB()  # Auto-populates cache on first use
print(f"Objects: {len(db)}")  # 1157

# Get cache location
print(f"Cache: {MaxRefDB.get_default_db_path()}")
```

## [0.1.2]

### Improvements in Type Safety

- Added type safety improvements via compliance with `mypy` checks

### Improvements in Layout

- Added `optimize_layout()` method for post-connection layout optimization

- Added `cluster_connected` parameter to `GridLayoutManager` for connection-aware object clustering

- Added `flow_direction` parameter support for both horizontal and vertical layouts in all layout managers

- Added backward compatibility for legacy layout manager APIs

- Enhanced layout performance with connection-aware clustering algorithms

- Improved layout manager consistency with unified `GridLayoutManager` and `FlowLayoutManager` APIs

- Added `FlowLayoutManager` with intelligent signal flow analysis and hierarchical positioning

- Added `GridLayoutManager` with connection-aware clustering and configurable flow direction

### Improvements in Max Object Introspection

- Added optional connection validation system with inlet/outlet validation and `InvalidConnectionError`. This is early stages, and may have some false positives, but planned improvements in handling of excepttions should make this accurate and useful.

- Added object introspection methods: `get_inlet_count()`, `get_outlet_count()`, `get_inlet_types()`, `get_outlet_types()`

- Added `Box.help()`, `Box.help_text()` and `Box.get_info()` methods for rich object documentation.

- Added `maxref` integration system with dynamic help for 1157 Max objects using `.maxref.xml` files

### Bug Fixes

- Fixed `maxclass` assignment bug that was preventing patchlines from connecting properly

### Improvements in Project Management

- Converted to [uv](https://github.com/astral-sh/uv) for project and dependency management.

## [0.1.1]

- Added `Makefile` frontend

- Changed package manager to `uv`

- Improved compatibility with Python 3.7

- Improved core Coverage: 99%

- Added clean script: `./scripts/clean.sh`

- Added coverage script and reporting: `./scripts/coverage.sh`

- Moved `tests` folder from `py2max/py2max/tests` to `py2max/tests`

- Added gradual types to `py2max/core`, no errors with `mypy`

- Added `number_tilde` test

- Fixed `comment` positioning

- Added `pyhola` layout.

- Added `graphviz` layouts.

- Fixed `Adaptagrams` layout.

- Added graph layout comparison and additional layouts.

- Added vertical layout variant.

- Added boolean `tilde` parameter for objects which have a tilde sibling.

- Added preliminary support for `rnbo~` include rnbo codebox

## [0.1.0]

- Added a generic `.add` method to `Patcher` objects which include some logic to to figure out to which specialized method to dispatch to. See: `tests/test_add.py` for examples of this.

- Major refactoring after `test_tree_builder` design experiment, so we have now only one simple extendable Box class, and there is round trip conversion between .maxpat files and patchers.

- Added `test_tree_builder.py` which shows that the json tree can be converted to a python object tree which corresponds to it on a one-on-one basis, which itself can be used to generate the json tree for round-trip conversion.

- Added `from_file` classmethod to `Patcher` to populate object from `.maxpat` file.

- Added `coll`, `dict` and `table` objects and tests

- Added some tests which try to use generic layout algorithm in Networkx but the results are quite terrible using builtin algorithms so probably better to try to create something fit-for-purpose.

- Added `gen` subpatcher

- Moved `varname` to optional kwds instead of being an explicit parameter since it's optional and its inclusion when not populated is sometimes problematic.

- Renamed odb to maxclassdb since it only relates to defaults per `maxclass`

- Added smarter textbox which uses odb to improve object creation.

- Added separate test folder

- Added `odb.py` in package with a number of default configs of objects

- Converted to package.

- Added some notes on graph drawing and layout algorithms

- Added comments keyword in box objects + PositionManager for easy documentation

- Added Comments objects

- Refactor: MaxPatch and Patcher objects are now one.

- Initial release
