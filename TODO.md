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

