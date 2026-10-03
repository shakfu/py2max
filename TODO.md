# TODO

## Critical

## High

- [ ] **`add_textbox` declares class-default port counts, not argument-aware ones.** `MAXCLASS_DEFAULTS` (`maxref/parser.py:859`) is keyed by class name only, so the box written to the file declares the wrong `numinlets`/`numoutlets`/`outlettype` whenever the ports depend on arguments. `porttypes.port_counts()` already resolves these correctly, and `lint` and `validate_connection` use it, so the box and its cords disagree: `validate_connections=True` accepts `route phase info` outlet 2 while the box declares 2 outlets.

  | text | declared by `add_textbox` | `port_counts()` | Max |
  |-|-|-|-|
  | `route phase info` | 2 out | 3 | 3 |
  | `unpack 0. 0 0 0. 0. 0. 0` | 2 out | 7 | 7 |
  | `sel 0 1 2 3` | 1 out | 5 | 5 |
  | `t f f` | 1 out | unknown | 2 |

  Fix: have `add_textbox` (`core/factory.py:418`) take counts from `porttypes.port_counts(name, text)` when it resolves them, and add `t`/`trigger` to `_ARG_RESOLVERS` (one outlet per argument). Whether Max rebuilds the ports from the text on load is unverified; `to_svg` and any consumer reading `numoutlets` see the wrong count either way. Found generating softkut~'s help patch, which now passes explicit counts.

- [ ] **`add_textbox` mishandles UI objects.** `add_textbox("flonum")` writes `maxclass: newobj` with `text: "flonum"` (the defaults entry has no `maxclass`), and UI boxes such as `waveform~` and `ezdac~` get a `text` key. Route known UI classes to their box form (`add_floatbox` already does it right for `flonum`) and omit `text` for non-`newobj` boxes.

- [ ] **`lint` gives a file-referenced `bpatcher` 0 ports.** `_effective_counts` (`lint.py:72`) takes counts from the nested patcher (`porttypes.subpatcher_counts`, `maxref/porttypes.py:194`); a `bpatcher` that loads a file by `name` has none, so it falls back to the maxref entry, `(0, 0)`, and every cord to it is an `E-INLET-RANGE`/`E-OUTLET-RANGE` error. Fall back to the box's declared `numinlets`/`numoutlets`, or read the referenced `.maxpat` when it resolves.

- [ ] **`graph:ogdf-*` layouts are not reproducible.** `_run_ogdf` (`layout/external.py:193`) neither seeds OGDF nor limits its runs. Sugiyama's crossing minimization runs several randomized passes and keeps the best; ties differ between processes, so the same patch builds differently each time (23 of 28 boxes moved between runs). `ogdf.set_seed(n)` plus `SugiyamaLayout().set_runs(1)` gave identical output in 5 separate processes, with the same crossing count (0) on that graph. The COLA and Fruchterman-Reingold adapters already pass `random_seed`. Seed every OGDF call, and expose `runs` (default 1) for callers who want best-of-n.

- [ ] `to_svg` does not wrap comment text, so long comments run past their boxes in previews.

### Validation follow-ups

- [ ] Turn connection validation on by default, in two stages. "Off vs. raise" is a false binary: raising is the highest-blast-radius option and it is gated on evidence only the opted-in minority can produce today.

  **Stage 1 (non-breaking): validate by default, warn on failure.** Add an `on_invalid` policy to `Patcher` (`"warn"` default, `"raise"`, `"ignore"`); keep `validate_connections=True` as the sugar for `on_invalid="raise"`. On a failed check `add_patchline` (`core/factory.py:255`) logs the same `InvalidConnectionError` message instead of raising. This matches the save-time linter, which already logs error-severity findings unless `strict=True`, and it collects false-positive data from every user rather than from the few who opt in. No existing script changes behaviour.

  **Stage 2 (breaking): flip the default to `"raise"`** once stage-1 warnings show the method-list accept-sets (`_accepts_from_methods`, `maxref/porttypes.py:234`) are false-positive-free. The gate is that maxref `<methodlist>` data is real but not guaranteed exhaustive -- an object whose XML omits a message it actually accepts would reject a legal connection. Then: survey `tests/`, `tests/examples/`, and round-tripped patches for connections that would newly error; decide unknown-object policy (warn vs. allow); add a CHANGELOG breaking-change entry.

  Notes for either stage:
  - The load path bypasses validation entirely -- `Patcher.from_dict` (`core/patcher.py:388`) appends `Patchline.from_dict` objects directly and never calls `add_patchline`. Loading a real `.maxpat` will not newly fail; the exposure is edits made after loading, plus save-time lint noise.

  - `core/factory.py:1241` already suppresses validation around the subpatcher rewrite, i.e. internally generated wiring does not always satisfy the checker. Fix or justify that before stage 2.

- [ ] Expand the curated `_OUTLET_EMIT` set (`maxref/porttypes.py`) as gaps surface -- outlet *emission* typing is not in the XML's structured data.

### Typed box properties

- [ ] **Per-maxclass property checking.** `BoxProps` is a flat union across all 1175 objects, so it catches a misspelled or wrongly-typed property but not a real property applied to the wrong object. 547 of the 850 properties are declared by exactly one object (the most widely shared, `bgcolor`, by 76), so the union is far more permissive than any individual object warrants:

  ```python
  # type-checks cleanly, and writes activedialcolor into the patch,
  # though only live.dial declares it
  p.add_textbox("cycle~ 440", activedialcolor=[1.0, 0.0, 0.0, 1.0])
  ```

  The data already exists: `maxref_saved_attributes()` in `scripts/gen_box_props.py` returns `(annotations, objects_by_attribute)` and the caller discards the second element as `_owners`. Two routes:
  - *Runtime*, cheap: extend the existing `validate_attrs` check to consult the owners map, so an unknown-for-this-maxclass property warns like an unknown one does. Catches it late but costs a table, not a type system.

  - *Static*, expensive: a TypedDict per maxclass plus overloads on `add_textbox` keyed by the object name. 1175 dicts is likely unworkable as written -- measure mypy's time on a subset before committing.

  Do the runtime route first; it is most of the value for a fraction of the cost, and it establishes whether the owners data is accurate enough to be worth enforcing statically.

### Database Improvements

- [ ] Add schema versioning for SQLite (enables migrations)

- [ ] Implement FTS5 for search (replace naive `LIKE '%query%'`)

## Medium

### Layout Managers

- [ ] **Lay out a subset of boxes.** `optimize_layout()` moves every box. A patch whose UI must stay put (a `bpatcher` view, a presentation area) needs its logic laid out around fixed boxes. softkut~ works around this by copying the subgraph into a scratch patcher, laying it out, and copying positions back. Add `optimize_layout(boxes=...)` or a per-box `pinned` flag.

- [ ] **External engines discard their own spacing.** `_normalize` (`layout/external.py:219`) rescales every engine's result to a fixed span (`max(300, 2.2 * box_width * sqrt(n))`). OGDF and HOLA already compute coordinates from the real box sizes; rescaling makes gaps arbitrary. For size-aware engines, translate to the margin and keep the scale.

- [ ] **`graph:sugiyama` lays out bottom to top.** With graph-layout's `SugiyamaLayout`, sources (`inlet`, `loadbang`) land at the bottom and cords run upward, against Max's top-down convention. Flip y, or set the engine's direction.

- [ ] **`flow` crossing reduction is weak.** On a 28-box message graph with two independent components, `FlowLayoutManager` (`_minimize_crossings`, `layout/flow.py:110`) interleaved the components and left many crossings that OGDF's Sugiyama removed entirely. Lay out connected components separately, and consider a barycenter pass per level.

- [ ] **`graph:hola` left two boxes overlapping** on the same graph, after its `prevent_overlaps()` pass. Cause not investigated; possibly the 50-iteration cap.

- [ ] Implement auto-scale to fit patcher bounds with margin

- [ ] Calculate object sizes from text length and port counts

- [ ] Anchor objects by type (e.g., `ezdac~` bottom-left, `scope~` bottom-right)

### MaxRef

- [ ] Handle non-standard Max installation paths

- [ ] Add XML schema validation for `.maxref.xml`

- [ ] Cache default Rect in `get_legacy_defaults`

- [ ] Batch database inserts in single transaction

## Low

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

### CI/CD

- [ ] Enable CI on push/PR (currently workflow_dispatch only)

### Strategic (P3)

- [ ] **gen~/RNBO codebox DSL** -- a small DSP-graph DSL that emits `codebox` text, turning py2max into a code-generation backend (`add_gen`/`add_codebox`/`add_rnbo` already exist as targets).

- [ ] **Declarative patch DSL / YAML recipes** -- see "Recipe-driven scaffolding" above.

- [ ] Rename `toFile()` -- it returns the document object, not a file, which is actively confusing now that real file I/O exists beside it.

- [ ] **Colours are still all-or-nothing** -- for `serialize` only; `save` is unaffected, since it never reads anything back. `bgcolor` / `textcolor` are out of the default attribute set, so a deliberately coloured box loses its colour on a round trip; `allAttributes` recovers it at the cost of writing Max's defaults everywhere.

  The rationale recorded here was wrong and is worth correcting, because it also rules out the obvious fix. Fonts do **not** work by reading the patcher's `default_fontsize`: `getattr` returns null for that and for both its siblings, measured in Max. They work because the filter falls back to Max's *own* defaults -- Arial, 12, face 0 -- which are fixed values a box can be compared against. Colours cannot use the same trick: the default `textcolor` observed on a real box was `[0.9, 0.9, 0.9, 1]`, a **dark-theme** value, so Max's default colours move with the theme while its default font does not. A discriminator would have to come from elsewhere -- reading a freshly created object of the same class is precise, but creates and destroys objects in the user's patch.

- [ ] `js2max/src/objects.ts` is 44 KB of the 92 KB `js2max.v8.js` bundle (the CommonJS build is 68 KB). Acceptable for a Max artifact, but if it matters: only the 43 own-maxclass entries are needed for correctness, since port counts can be omitted and Max derives them -- confirmed, since the patch that opened in Max has no ports on its `print` box. Consider splitting the table so `serialize` can be used without it.

- [ ] **Use more of the Max JS API rather than hand-rolling.** Partly done: `File` backs `src/fileio.ts` and `Dict` backs `src/dict.ts`, and the `firstobject` walk that was copied five times is now one exported `objectsOf`. Still unused: `applydeep` / `applyif` / `getlogical` for iteration, and `MaxobjListener` and `Task` entirely. Check the [API reference](https://docs.cycling74.com/apiref/js/) before adding to `scripting.ts` -- one wrong assumption about it (that patchlines could not be enumerated) already cost a feature, and a second (that `newdefault` reports an unknown class) hid a bug for the life of the bridge.

- [ ] **Decide whether Python should emit v8 scripts.** Now that `v8` is a target, the alternative to a TS core is codegen: py2max writes the patch *and* the script inside it, the way `add_gen_codebox` already emits gen~ code. That needs no second language and keeps one implementation. Worth settling before the TS core grows further, since the two answers pull in opposite directions.

  The original rationale is kept below for the record.

  *Motivation.* `.maxpat` is JSON, but the Python model reaches it by reflection and is largely unchecked: `Box.__init__` (`core/box.py:36`) declares five parameters and funnels the entire Max property vocabulary (`presentation_rect`, `bgcolor`, `varname`, `saved_attribute_attributes`, ...) through `**kwds: Any`; `to_dict` is `vars(self)` minus underscore keys (`core/serialization.py:26`); `_remove_none_entries` exists only because Max distinguishes absent keys from null ones (its own `TODO: make recursive` is a symptom). A TS interface with optional fields describes the same JSON at zero cost -- omitted optionals are absent, `JSON.stringify` drops `undefined`, and `tsc` catches a misspelled property that today ships silently into the file. Discriminated unions on `maxclass` add exhaustiveness checking; `as const` on the maxref tables replaces `Dict[str, Any]`.

  *The real differentiator is not the type system.* Max embeds JavaScript (the `v8` object, and Node for Max via `node.script`), so a TS core is the only option that runs both offline as a generator and inside a patch at runtime, sharing one set of format types. If in-patch runtime manipulation ever enters scope, this stops being a spike and becomes the main argument. Confirm the Max version requirements for `v8`/`node.script` in the Cycling '74 docs first.

  *Spike scope.* Format types + `Box`/`Patcher`/`Patchline` + JSON round-trip, validated against the existing `.maxpat` fixtures in `tests/`. Explicitly out of scope: layout, maxref, db, cli, svg.

  *Decision gate.* The spike must beat "Typed box properties" under High Priority, which closes the same silent-failure mode inside Python for a few hundred annotations, mostly generated from the maxref bundle. Kill the spike unless it demonstrates something that cannot reach. (Note that mypy strict already runs -- the gap TS would close is `Any`, not laxness.)

  *Costs, stated up front.* Conciseness is not the payoff: of ~12k lines, the serialization/model layer TS would shrink is a few hundred; layout, XML parsing, sqlite, and cli are at par or longer. Node has no stdlib XML parser and `node:sqlite` is recent, so the "zero runtime dependencies" property does not survive a full port of `maxref/`. The library's users are already in Python (music21, librosa, numpy, mido) and the graph-layout dependencies (networkx, pygraphviz) have no equal in JS -- so any TS core stays a second front end to the format, never a replacement for the Python api.

### Code-quality polish (low value)

- [ ] `maxref/db.py`: whitelist the f-string-interpolated table/column names in `_insert_inlets_outlets`, `_delete_related_records` and `_get_simple_list`. Not exploitable (the identifiers are internal constants) and largely superseded by the planned FTS5 migration. The `LIKE` half of this item is done: `search()` escapes `%`/`_`/`\` and validates its `fields` against a `SEARCHABLE_FIELDS` whitelist.

- [ ] `exceptions.py`: trim ~40% -- several exception classes (`InvalidPatchError`, `InternalError`, `DatabaseError.operation`) have no raisers. Check for external imports before removing.
