# TODO

## Critical

## High

### Validation follow-ups

- [ ] **Connection validation stage 2: raise by default.** Stage 1 (`on_invalid="warn"` default) is done. Its first data found two false-positive classes: 53 signal-typed right inlets that take numbers, and codebox port counts. Both are fixed; 527 cords from 60 Max-written patches now pass. Do not flip until warnings from real use show no new class: one class this size appeared in the first hour. Then decide the unknown-object policy and add a CHANGELOG breaking-change entry.

  `encapsulate()` keeps validation off while it rewires. Its generated cords pass validation; the reason is that they restate existing cords, so under `"raise"` an old fault would abort the move halfway.

- [ ] Expand the curated `_OUTLET_EMIT` set (`maxref/porttypes.py`) as gaps surface -- outlet *emission* typing is not in the XML's structured data.

### Typed box properties

- [ ] **Per-maxclass property checking, static.** `BoxProps` is a flat union across all 1175 objects, so mypy accepts a real property on the wrong object (`activedialcolor` on `cycle~`). The runtime check (`validate_attrs`, now on by default) catches it. A static check needs a TypedDict per maxclass plus overloads on `add_textbox`; 1175 dicts is likely unworkable -- measure mypy's time on a subset before committing.

### Database Improvements

- [ ] **FTS5 search: only for ranking, not speed.** `LIKE` search over 1175 objects takes 0.3-0.6 ms, so FTS5 buys no speed. Its gain would be relevance order (bm25) instead of alphabetical; a `trigram` tokenizer keeps substring semantics. Decide whether ranked results are wanted.

## Medium

### Layout Managers

- [ ] **`graph:ogdf-planarization` is not reproducible even when seeded.** On a 30-box graph, 8 processes with `ogdf.set_seed(7)` gave 2 distinct layouts (5/3). Sugiyama and FMMM are stable under the same seed. Likely `SubgraphPlanarizer`'s multithreaded permutation runs; fix in ogdf-py (expose a thread count) rather than here.

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

- [ ] `exceptions.py`: `InvalidObjectError`, `LayoutError` and `MaxRefError` are never raised, but are exported and imported elsewhere in the package; removing them breaks public imports. Either raise them where they fit (an unknown maxclass, a failed layout, an unreadable `.maxref.xml`) or deprecate them.
