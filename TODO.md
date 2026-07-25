# TODO

## High Priority

### Validation follow-ups

The message-type validation + linter cycle shipped in 0.3.4.
Two items remain, both gated on field experience:

- [ ] Turn connection validation on by default, in two stages. "Off vs. raise"
  is a false binary: raising is the highest-blast-radius option and it is gated
  on evidence only the opted-in minority can produce today.

  **Stage 1 (non-breaking): validate by default, warn on failure.** Add an
  `on_invalid` policy to `Patcher` (`"warn"` default, `"raise"`, `"ignore"`);
  keep `validate_connections=True` as the sugar for `on_invalid="raise"`. On a
  failed check `add_patchline` (`core/factory.py:255`) logs the same
  `InvalidConnectionError` message instead of raising. This matches the
  save-time linter, which already logs error-severity findings unless
  `strict=True`, and it collects false-positive data from every user rather than
  from the few who opt in. No existing script changes behaviour.

  **Stage 2 (breaking): flip the default to `"raise"`** once stage-1 warnings
  show the method-list accept-sets (`_accepts_from_methods`,
  `maxref/porttypes.py:234`) are false-positive-free. The gate is that maxref
  `<methodlist>` data is real but not guaranteed exhaustive -- an object whose
  XML omits a message it actually accepts would reject a legal connection.
  Then: survey `tests/`, `tests/examples/`, and round-tripped patches for
  connections that would newly error; decide unknown-object policy
  (warn vs. allow); add a CHANGELOG breaking-change entry.

  Notes for either stage:
  - The load path bypasses validation entirely -- `Patcher.from_dict`
    (`core/patcher.py:388`) appends `Patchline.from_dict` objects directly and
    never calls `add_patchline`. Loading a real `.maxpat` will not newly fail;
    the exposure is edits made after loading, plus save-time lint noise.
  - `core/factory.py:1241` already suppresses validation around the subpatcher
    rewrite, i.e. internally generated wiring does not always satisfy the
    checker. Fix or justify that before stage 2.

- [ ] Expand the curated `_OUTLET_EMIT` set (`maxref/porttypes.py`) as gaps
  surface -- outlet *emission* typing is not in the XML's structured data.

### Typed box properties

- [ ] Replace `**kwds: Any` with a `BoxProps` TypedDict accepted via `Unpack`.
  This is the property-level analogue of the connection-level checks above, and
  the largest remaining silent-failure mode in the library.

  *Problem.* `mypy strict = true` (python_version 3.9) already runs and backs the
  shipped `py.typed`, but `Any` is strict-legal: the entire Max property
  vocabulary (`presentation_rect`, `bgcolor`, `varname`,
  `saved_attribute_attributes`, ...) enters through `**kwds: Any` at
  `core/box.py:44` and `core/patchline.py:28`, is None-stripped, and is written
  straight to the file. A misspelled or wrongly-typed property produces a
  silently wrong `.maxpat`, not an error -- neither the type checker nor the
  save-time linter sees it.

  *Approach.* `class BoxProps(TypedDict, total=False)` + `**kwds:
  Unpack[BoxProps]`. Must thread through the `factory.py` forwarders
  (`add_textbox` and the `add_*` family at `392`, `565`, `601`, `618`, ...,
  plus `add`/`_add_str`'s `**kwds` relays) or checking stops at the first hop
  and the annotation is decorative.

  *3.9 constraint.* PEP 692 (`Unpack[TypedDict]` in `**kwargs` position) is a
  3.12 runtime feature; `typing.Unpack` arrived in 3.11. On the current floor use
  `from __future__ import annotations` plus `if TYPE_CHECKING: from
  typing_extensions import Unpack`, so annotations stay strings and no runtime
  dependency is added (typing_extensions is already present transitively via
  mypy in dev). Verify that downstream consumers of `py.typed` still resolve the
  annotation.

  *The vocabulary is derivable from data already shipped.* maxref attribute
  entries carry a `type` (`int`/`float`/`symbol`/`atom`) and nested
  meta-attributes including `save` and `default`; `save == 1` marks the
  attributes Max persists into the patch file. Verified: `umenu.align` is
  `type=atom, save=1`. So generate per-class property sets from the bundle and
  hand-write only the universal box properties (`patching_rect`,
  `presentation_rect`, `varname`, ...). Codegen must honour the `renamed` and
  `obsolete` meta-attributes (`align` is `renamed -> textjustification`).

  *Open questions.* Diff maxref attribute names against the actual JSON keys in
  the `tests/` `.maxpat` fixtures before trusting the mapping. Keep a permissive
  escape hatch for unknown keys -- a closed `BoxProps` would reject
  round-tripping any patch containing properties newer than our vocabulary,
  which `Patcher.from_dict` must continue to accept.

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
  text, turning py2max into a code-generation backend (`add_gen`/`add_codebox`/`add_rnbo` already exist as targets).
- [ ] **Declarative patch DSL / YAML recipes** -- see "Recipe-driven scaffolding" above.
- [ ] **Experimental TypeScript core (spike, not a port)** -- evaluate a TS
  implementation of the patch format and object model only.

  *Motivation.* `.maxpat` is JSON, but the Python model reaches it by
  reflection and is largely unchecked: `Box.__init__` (`core/box.py:36`) declares
  five parameters and funnels the entire Max property vocabulary
  (`presentation_rect`, `bgcolor`, `varname`, `saved_attribute_attributes`, ...)
  through `**kwds: Any`; `to_dict` is `vars(self)` minus underscore keys
  (`core/serialization.py:26`); `_remove_none_entries` exists only because Max
  distinguishes absent keys from null ones (its own `TODO: make recursive` is a
  symptom). A TS interface with optional fields describes the same JSON at zero
  cost -- omitted optionals are absent, `JSON.stringify` drops `undefined`, and
  `tsc` catches a misspelled property that today ships silently into the file.
  Discriminated unions on `maxclass` add exhaustiveness checking; `as const` on
  the maxref tables replaces `Dict[str, Any]`.

  *The real differentiator is not the type system.* Max embeds JavaScript (the
  `v8` object, and Node for Max via `node.script`), so a TS core is the only
  option that runs both offline as a generator and inside a patch at runtime,
  sharing one set of format types. If in-patch runtime manipulation ever enters
  scope, this stops being a spike and becomes the main argument. Confirm the
  Max version requirements for `v8`/`node.script` in the Cycling '74 docs first.

  *Spike scope.* Format types + `Box`/`Patcher`/`Patchline` + JSON round-trip,
  validated against the existing `.maxpat` fixtures in `tests/`. Explicitly out
  of scope: layout, maxref, db, cli, svg.

  *Decision gate.* The spike must beat "Typed box properties" under High
  Priority, which closes the same silent-failure mode inside Python for a few
  hundred annotations, mostly generated from the maxref bundle. Kill the spike
  unless it demonstrates something that cannot reach. (Note that mypy strict
  already runs -- the gap TS would close is `Any`, not laxness.)

  *Costs, stated up front.* Conciseness is not the payoff: of ~12k lines, the
  serialization/model layer TS would shrink is a few hundred; layout, XML
  parsing, sqlite, and cli are at par or longer. Node has no stdlib XML parser
  and `node:sqlite` is recent, so the "zero runtime dependencies" property does
  not survive a full port of `maxref/`. The library's users are already in
  Python (music21, librosa, numpy, mido) and the graph-layout dependencies
  (networkx, pygraphviz) have no equal in JS -- so any TS core stays a second
  front end to the format, never a replacement for the Python api.

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

