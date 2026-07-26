# Changelog

## [Unreleased]

### New: `scripts/py2max.py` is now generated, not hand-maintained

- `scripts/py2max.py` -- the single-file edition -- is now produced by `scripts/build_single_file.py` (`make single-file`) instead of being maintained by hand. It amalgamates the core object model, the grid/flow/columnar/matrix layout managers, `lint()`, connection and attribute validation, `.amxd` read/write and SVG export into one module, with an offline maxref table embedded (port types, method names and attribute names for all 1175 objects, compressed to ~30 KB; the ~8 MB of documentation prose is dropped, so `Box.help()` returns a pointer to the full package while `get_info()` still returns structured data). Graph layouts (`layout="graph:*"`), the CLI and the SQLite maxref database are excluded; `layout="graph:*"` raises `NotImplementedError` naming the package to install.

- **Why:** the hand-maintained version had drifted five releases behind and carried four real defects, including one that broke *every* edit-after-load (`width` read `self.rect.w`, but a loaded patch keeps `rect` as a plain JSON list) and the operator-precedence bug in `add_coll`/`add_dict`/`add_table` that discarded a caller-supplied `text`. Nothing in the repo imported it, so no test caught any of it. Generating the file makes drift structurally impossible: the single file now *is* the package's own code.

- `tests/test_single_file.py` asserts equivalence rather than mere importability: 13 patch builders (layouts, containers, subpatchers, semantic ids, editing, theming) are built with both implementations and their emitted JSON must match exactly, plus per-object agreement on port counts, validation verdicts and messages, `MAXCLASS_DEFAULTS`, object coverage, lint findings and SVG output. A staleness guard runs the generator with `--check` and fails if the committed file differs from a fresh build, so a stale copy can no longer rot unnoticed.

- The generator refuses to emit a broken file: it fails on top-level name collisions between amalgamated modules, and on any undefined name left behind when included code calls into an excluded module (which is how the missing SVG exporter was caught). Builds are byte-reproducible (the gzip header's timestamp is zeroed), so the staleness check is meaningful.

### New: box properties are typed -- a misspelled property is now an error, not a silent key

- Max box properties reached the emitted `.maxpat` through `**kwds: Any`, so `p.add_textbox("cycle~ 440", bgcolour=[0,0,0,1])` wrote `bgcolour` into the patch and `fontsize="twelve"` wrote a string where Max wants a number. Neither was caught by anything: `mypy --strict` passes on `Any`, and `validate_attrs=True` warns about unknown property *names* at runtime but says nothing about *types* and emits the key regardless.

- **`py2max/core/props.py` (generated) defines `BoxProps` / `TextboxProps`**, and `Box.__init__`, `add_textbox`, `add_message` and `add_comment` now accept `**kwds: Unpack[BoxProps]`. Under the `mypy --strict` this project already runs, a misspelled property is rejected *with a suggestion* (`did you mean "bgcolor", "bgcolor2", or "hbgcolor"?`), as are a wrongly-typed value and an explicit `None` for an optional property.

- Zero runtime cost and no new dependency: `Unpack` is imported under `if TYPE_CHECKING` with postponed annotations, so nothing is evaluated at runtime and the library keeps shipping zero runtime dependencies (verified by running the single-file build on a Python with no `typing_extensions` installed). `BoxProps` and `TextboxProps` are exported from the top level for callers annotating their own helpers.

- **Two TypedDicts rather than one, deliberately.** A TypedDict key that collides with a named parameter makes mypy report `Overlap between argument names and ** TypedDict items` **and then stop checking calls to that function altogether** -- a silent loss of coverage, which is the worst possible failure for a change whose entire purpose is coverage. `BoxProps` therefore omits `Box.__init__`'s five structural parameters and `TextboxProps` additionally omits `text`/`outlettype`/`comment`/`comment_pos`/`justify`; the narrower flows into the wider when kwds are forwarded. `tests/test_box_props.py::test_the_overlap_trap_is_absent` guards against a regression.

- **The 850-property vocabulary is generated from four sources** by `scripts/gen_box_props.py` (`make box-props`), but they are nowhere near equal partners. maxref attributes whose `save` meta-attribute is 1 -- exactly those Max persists into a file -- supply 830 names, 785 of them found nowhere else. A hand-written table adds 20 more and, more usefully, **retypes 7** that maxref declares too widely: the generator unions an attribute's type across every object declaring it, which is correct where the key genuinely differs but costs real checking on the handful users actually pass (`range` arrives as `Union[Sequence[float], Sequence[int], float, int]` and is pinned to `Sequence[Atom]`). Three keys are dropped for not being valid Python identifiers (`one/column`, `one/matrix`, `one/row`).
- **The other two sources contribute one name each -- and that is why they exist.** An AST scan of every keyword py2max itself passes to `Box(...)` adds `viewvisibility`: maxref documents `bpatcher` with 12 attributes and omits this one, which the library writes and Max accepts, so a maxref-only vocabulary would have rejected py2max's own output. A sweep of the repository's `.maxpat` fixtures adds `comment`. Both scans are cheap, and they are the only defence against maxref being incomplete, which it demonstrably is.
- The result is typed rather than nominally typed: of the 850 properties only five are bare `Any` (`comment`, `data`, `outlettype`, `patcher`, `viewvisibility`); the rest resolve to `int` (481), `Sequence[float]` (154), `str` (92), `float` (68) and small unions.
- **Known limitation:** the vocabulary is a flat union across all 1175 objects, and the median maxref attribute is declared by exactly one of them (the most widely shared, `bgcolor`, by 76). So `BoxProps` cannot tell that a property is invalid *for the maxclass it was passed to*: 547 of the 850 belong to a single object, and `p.add_textbox("cycle~ 440", activedialcolor=[1.0, 0.0, 0.0, 1.0])` type-checks cleanly and writes `activedialcolor` into the patch even though only `live.dial` declares it. Misspelled and wrongly-typed properties are rejected; real properties on the wrong object are not. Recorded in `TODO.md`.

- `add_floatparam` / `add_intparam` now pass `minimum`/`maximum` through `kwds_filter` instead of forwarding `None`, so an unset bound is absent from the patch rather than present as null.

- `tests/test_box_props.py` (13 tests) runs mypy in subprocesses to assert each failure mode is rejected and that correct usage still checks -- a static guarantee is not observable at runtime, so an ordinary assertion cannot see it. A staleness guard fails if the generated file drifts from its sources.

- Those subprocesses pass `--no-color-output`. mypy honours a `FORCE_COLOR` inherited from the developer's shell, and the assertions match on message text, so without it the tests failed for anyone who has it set -- and `test_the_overlap_trap_is_absent`, which asserts a fragment is *absent*, would instead have passed for the wrong reason.

### Fixed: `add_comment` had its port counts backwards

- A comment box takes a `set` message and emits nothing -- 1 inlet, 0 outlets. `add_comment` passed neither to `Box`, so the constructor's defaults applied and produced 0 inlets and 1 outlet on every comment py2max has ever written.
- **Found by round-tripping a py2max patch through Max**: js2max serialized a patcher back to a `.maxpat`, and diffing it against the py2max original showed Max had rewritten the values on save. Max is the authority, and it disagreed.
- Related, in the generated js2max object table: `Box.__init__` defaults `numoutlets` to 1, and for the **73 objects maxref does not state it** that default is simply wrong -- `print` came out with an outlet it does not have. The table now reads maxref directly and omits a count maxref is silent about, since Max derives ports from the instantiated object anyway.

### New: the TypeScript core builds patches live inside Max via `v8`

- The spike below was closed as failing its own decision gate, with one stated reopening condition: the in-Max runtime argument. **`v8` ships in current Max, so that condition is met**, and `js2max/` is now built out around the one capability the Python package cannot have -- Python writes `.maxpat` files that Max later opens; a `v8` script runs *inside* an open patcher and can build it in place, from the same description.
- **`src/scripting.ts` is the bridge.** `instantiate(patcher, description)` turns boxes into `newdefault` calls and patchlines into `connect` calls, deriving the class name and typed-in arguments from a box's `text` (numeric tokens become numbers, because Max distinguishes the symbol `440` from the int `440`), converting `patching_rect` `[x,y,w,h]` to `Maxobj.rect` `[l,t,r,b]`, naming objects after their model id so `getnamed` finds them afterwards, and recursing into subpatchers. It never throws for a bad box: an unknown class, or a patchline to a box that failed, lands in `result.skipped` with a reason and the rest still builds.
- **Two artifacts, both committed so a Max user needs no toolchain.** `js2max/max/js2max.v8.js` is an IIFE drop-in (`[v8 js2max.v8.js]`, then `demo` / `build <json>` / `clear` / `count`); `js2max/max/js2max.js` is a CommonJS build for `var js2max = require("js2max.js")` in your own script. Bundling is required rather than tidy: **`v8` supports CommonJS `require()` and `include()` but not ESM `import`**, and this core is written as ES modules.
- **`.maxpat` file I/O** (`src/fileio.ts`), over Max's `File` class -- the only file access a `v8` script has, since there is no `fs`. `readPatch(path)` parses a `.maxpat` and `writePatch(path, patcher)` serializes one; `read <path>` / `write <path>` expose both as messages, so js2max can now open a patch py2max wrote rather than waiting to be handed its contents. Two details the reference forced: `readstring` returns *up to* the count asked for, so reading loops -- and watches `position`, because a loop that never advances would lock Max rather than merely hang; and opening for write does not truncate, so `eof = 0` comes first, or a shorter document leaves the tail of the longer one it replaced. The `File` constructor is injected rather than referenced directly, which keeps both behaviours testable outside Max and avoids a name collision with the DOM `File` that TypeScript and Bun both define.
- **`write <path>` serializes a live patcher back to a `.maxpat`** (`src/serialize.ts`), built on what a `probe` run inside Max actually reported rather than on what the reference implied. Two earlier theories were wrong: writing `Maxobj.maxclass` straight into the file (it is the *object* class -- `cycle~` -- where the file needs `maxclass: "newobj"` plus the text), and reading box attributes (`getboxattr("maxclass")`, `("numinlets")`, `("numoutlets")` and `text` **all return null**; `getboxattrnames()` lists colours, fonts, rects and `varname`, never the class or the ports).
- What Max does supply is `Maxobj.maxclass` -- the object class, which is a usable key -- and `Maxobj.boxtext`, which returns every box's text including a comment's prose. The rest is static per class, so **`js2max/src/objects.ts` is generated from py2max** (`scripts/gen_js2max_objects.py`): 43 classes that keep their own `maxclass`, and port counts for all 1175 objects in the maxref bundle. The generator calls py2max's dedicated `add_comment`/`add_message`/`add_umenu`/... where they exist, because `add_textbox("comment")` reports 1 inlet where a real comment box has 0. An object class with no entry -- a third-party external -- omits its port counts rather than guessing, since Max derives them from the instantiated object.
- `{ allAttributes: true }` copies everything `getboxattrnames()` reports rather than the curated subset.
- **`write <path> full` also records each object box's own attributes** under `saved_object_attributes`, read through `getattr`. Scoped by measurement rather than by guess: `getattrnames()` minus `getboxattrnames()`, because for a UI box the two lists are **identical** -- a comment reports the same 33 names either way, so reading both would write every box attribute a second time. Only object boxes have anything of their own (`print`: `level`, `popup`, `time`; `[v8]`: `embed`, `parameter_enable`), and that is what gets captured.
- **`filename` and `textfile` turned out not to be recoverable**, which is what prompted this. Neither appears in `getattrnames()`, so both are bookkeeping Max writes on save rather than object state -- and asking anyway is actively bad: `getattr("textfile")` returns a Max object the JS bridge cannot wrap and logs `v8_wrapobject: couldn't wrap instance of class textfile`. Values that are not plain data are now skipped, and `probe` only reads names the object actually reports.
- **Attribute selection is deliberately narrow.** `getboxattr` answers for every attribute a box has, including ones sitting at their defaults, and offers no way to ask which those are -- so a wide list writes Max's own defaults back into the file. Measured against a real round trip: including colours and fonts added nine keys to every box and took a 7 KB patch to 18 KB, none of which Max writes itself. Falsy flags are dropped and fonts/colours are out of the default set; `{ allAttributes: true }` opts into everything.
- **`write` refuses to overwrite the patch it is serializing.** `serialize` describes the whole patcher, so writing to your own filename produces a copy of yourself -- and for a generated patch that silently replaces a build artifact.
- **It refuses rather than writing a file Max cannot load.** Any box that cannot be fully described is named in the console and the write is abandoned; `write <path> partial` overrides. An object box missing its `text` counts as incomplete, because it would reopen empty -- silent data loss is worse than a refusal. A cord to a box that was dropped is dropped with it, never left referencing a missing id.
- **`probe` logs what each box actually reports.** Every assumption in `serialize` comes from the API reference rather than from a Max run, and the previous version of this feature was wrong for exactly that reason. `probe` turns the next round-trip into data instead of a guess.
- **`save <path>` writes a description straight to a `.maxpat`, creating no objects at all.** This is the export path, and it is exact by construction: a description already *is* the shape of a `.maxpat`, so nothing has to be read back out of Max -- no accessor, no default to guess at, no live patcher. Verified byte-identical to its input.
- That matters because **`write` / `serialize` is necessarily lossy**: every field has to be rebuilt from whatever the JS API exposes, and a font matching the patcher default is indistinguishable from an unset one, port counts maxref does not state are omitted, and `linecount` / `filename` / `textfile` have no accessor at all. Building objects only to read them back is the wrong shape for an export -- which is how the write demo worked at first, and why `save` replaced it. `write` remains the right tool for capturing a patcher someone edited by hand.
- **`write <path> built` exports only what the last build created**, rather than the whole patcher. "Save this patcher" and "export what I built" are different requests: a script that builds an instrument into a host patch wants the instrument, not the `[v8]` box and message boxes that built it. Cords are kept only where both ends are in the set, so the result is self-contained, and ids are renumbered from `obj-1`.
- The bundle sets **`autowatch = 0`**. With it on, rebuilding `js2max.v8.js` reloads the script and resets the `built` list, so a `make js2max` in another window silently discards what `synth` had created and the next `write ... built` reports nothing to write. This is a built artifact, not a file anyone edits in place.
- **Two verification patches**, both generated by py2max. `v8-harness.maxpat` exercises every message. `write-demo.maxpat` exists because serializing the harness produces something resembling the harness, so it cannot show that `write` does anything: there, `synth` builds a nine-object instrument and `write ... built` saves those nine alone -- input and output share no box at all. `synth` also covers what the harness does not, with classes that keep their own `maxclass` (`toggle`, `flonum`, `ezdac~`) alongside object boxes and a fan-out to two inlets.
- **Fonts are filtered against the patcher's own defaults.** Dropping them wholesale lost a comment deliberately set to 14pt; including them wrote Max's default onto every box. A `.maxpat` records `default_fontsize` / `default_fontname` / `default_fontface`, and `Patcher.getattr` reads them back -- the one case Max gives a reference point for, so a box font is written only when it differs.
- `js2max/max/v8-harness.maxpat` is the verification patch, **generated by py2max itself** (`scripts/gen_v8_harness.py`) -- the Python package emits a patch that loads the TypeScript bundle that builds objects from the format the Python package writes.
- **Confirmed by running it in Max**, via the harness: `this` binds as expected inside the bundled IIFE scope (the global-handle fallback was not needed), `newdefault` / `connect` / the rect conversion all work -- `demo` produced a correctly wired `cycle~ 440 -> gain~ -> ezdac~` -- and `outlet()` reports correctly. Still unverified: `message("set", ...)` on a message box, whether `newdefault` returns null or throws for an unknown class, and `build <json>` / subpatcher recursion / `snapshotBoxes`, none of which the harness exercises.
- **Fixed by that run: `clear` deleted the `[v8]` object running the script.** Removing the box that hosts a running script does not fail cleanly -- Max frees it, execution continues against the freed pointer, and the next `post()` reports `bad object` / `typedmess: post: corrupt object` / `doesn't understand "post"`. `clear` now removes only what the last build created, which is both safe and what anyone wants after `demo`; the destructive option is a separately named `clearall` that keeps the script's own box and refuses to run if it cannot identify it. `scripting.ts` gained a `keep` option and a `remove(target, objects)` for the same reason, with regression tests.
- The bridge is otherwise tested against `MockPatcher`, a recording double for the Max host: The bridge is tested against `MockPatcher`, a recording double for the Max host, and `MockFileSystem` for the file layer: 90 tests covering class-name derivation, argument coercion, rect conversion, connection indices, subpatcher recursion and failure collection. That proves the mapping is right; only running it in Max proves Max accepts the calls. `js2max/README.md` lists the three specific things a real run would settle, including whether `this` binds as expected inside a bundled scope -- `patcherOf` tries the call's `this`, then a global handle, then fails with a readable message rather than a `TypeError`.
- **Corrected against the Max JS API reference.** An earlier revision claimed connections could not be enumerated from a live patcher and cut the reverse direction down to boxes only. That was wrong: `Maxobj.patchcords` returns `inputs` and `outputs` arrays of `MaxobjConnection` (`srcobject`/`srcoutlet`/`dstobject`/`dstinlet`). `snapshot` now returns lines as well as boxes, reading only the `outputs` side so each cord is reported once rather than once per endpoint. It still describes the *patcher*, not the *file* -- a live object exposes class, name, position and cords, but not typed-in text or per-class attributes.
- Also from that reference: `instantiate` now honours `patchline.hidden` via `hiddenconnect` (it previously called `connect` unconditionally, so a hidden cord came back visible), and the host declarations cover `Maxobj.valid`, `understands`, `getattr`/`setattr`, plus `applydeep` / `applyif` / `getlogical` / `parentpatcher` on `Patcher`.
- `make ts` builds, `make js2max-check` typechecks, tests, and fails if either artifact or the harness has drifted from its source -- the same staleness guard the Python single-file edition uses.

### Previously: `js2max/` -- experimental TypeScript core spike (built, evaluated, closed)

- Added `ts/` (since renamed `js2max/`): the `.maxpat` format as TypeScript types plus a minimal `Patcher`/`Box`/`Patchline` model with JSON round-trip (868 lines, 32 passing tests, `make js2max-check`; needs [Bun](https://bun.sh)). Layout, maxref, the database, the CLI and SVG export were out of scope by design. `js2max/README.md` is the write-up.

- **Outcome: the spike fails its own decision gate and should not be built on.** It confirmed the type-system benefits are real and measured them: `tsc` rejects a misspelled box property, a wrong value type, a bad `patching_rect` arity, a missing structural key and a non-exhaustive maxclass `switch` -- all of which the Python package currently writes straight into the emitted patch. Notably `validate_attrs=True` warns about unknown property *names* but says nothing about *types*, and `mypy --strict` (which this project already passes) catches neither, because `Any` is strict-legal.

- **But every one of those cases is caught by the planned `TypedDict`/`Unpack` work**, which was prototyped and run under `mypy --strict` rather than assumed: mypy flags the typo (with a "did you mean `bgcolor`?" suggestion that `tsc` does not offer), the wrong type, the wrong arity, an explicit `None` for an optional key, and non-exhaustive handling via `assert_never`. Since nothing in the spike is out of Python's reach, the TODO item is closed in favour of "Typed box properties"; the in-Max runtime argument (`v8` / `node.script`) is the only remaining reason to reopen it, and this spike did not test it.

- The prototype also turned up a constraint worth knowing before that work starts: a key declared in the `TypedDict` may not also be a positional parameter, or mypy reports `Overlap between argument names and ** TypedDict items` **and silently stops checking calls to that function** -- so `BoxProps` must omit `text`. Recorded in `TODO.md`.

- Round-tripping all 14 `.maxpat` fixtures under `tests/` through the typed model passed on the first attempt, and the format types eliminate three pieces of Python machinery outright: `_remove_none_entries` (absent optionals are simply not emitted), the `from_dict` step that deletes seeded defaults a source patch lacked, and the `render()` pass that converts objects into dicts.

### Fixed: importing py2max no longer logs, nor hijacks the host's logging

- **`import py2max` is now silent.** DEBUG-level logging was previously the shipped default (`log.py`: `DEBUG = getenv("DEBUG", default=True)`), so simply constructing a `Patcher` printed internal diagnostics to the console. Logging is now opt-in.

- **Breaking (bad default removed): the library no longer calls `logging.basicConfig(..., force=True)` at import.** That call replaced the host application's logging configuration -- handlers, format and level -- as a side effect of importing py2max. A program that configured `basicConfig(format="APP: %(message)s")` and then imported py2max silently lost its own format. The `py2max` logger now carries a `NullHandler` and nothing else is touched, which is the standard way for a library to participate in logging without imposing any.

- **New `py2max.setup_logging(level=..., color=..., log_file=...)`** opts in to py2max's colored console output. It attaches handlers to the `py2max` logger only, never to root, and is idempotent (repeat calls replace their own handlers rather than stacking duplicates). It deliberately leaves `propagate` alone: disabling it would be a global side effect that silently blinds anything capturing py2max records through an ancestor logger, including pytest's `caplog`.

- **Env vars are namespaced and default off:** `PY2MAX_DEBUG=1` (was the bare, extremely common `DEBUG`, which meant any unrelated `DEBUG=1` in the environment turned py2max verbose), plus `PY2MAX_LOG_LEVEL`, `PY2MAX_LOG_FILE` and `PY2MAX_COLOR`. Setting any of the first three enables logging at import; an explicit `PY2MAX_DEBUG=0` stays silent.

- **The CLI, being an application rather than a library, now configures logging explicitly** and gained `-v`/`-vv` (INFO/DEBUG) and `-q` flags. It previously got its output purely as a side effect of importing the package.

- `config()` is retained as a no-op alias of `get_logger()` for backwards compatibility.

- `tests/test_logging.py` covers all of it, using subprocesses for the import-time behaviour that cannot be re-tested in an already-imported module. A `tests/conftest.py` fixture now snapshots and restores the `py2max` logger around every test: `setup_logging()` mutates process-global state, and without isolation a CLI test's configuration made `caplog` blind in a later lint test -- a failure that passed in isolation and only appeared in the full run.

### Fixed: the maxref cache no longer prints to stderr

- Building the one-time object cache announced itself with four `print(..., file=sys.stderr)` calls. A library does not get to decide whether that is visible or where it goes; it is now logged at INFO on the `py2max` logger, so `py2max.setup_logging("INFO")` shows it and the default stays silent. The CLI still prints -- it is an application, and its output is the product.

### Fixed: `add()` raised `TypeError` when a keyword named the target's own parameter

- `Patcher.add()` derives the first argument of its target method from the value it was handed (the text tail, the number) and then forwards `**kwds` to the same call, so a caller naming that parameter passed it twice: `p.add("cycle~ 440", text="saw~ 220")`, `p.add(5, initial=3)` and `p.add("coll x", name="y")` all failed with `got multiple values for argument`. An explicit keyword now wins over the derived value.

- **This was a family, not a list of cases.** The `_maxclass_methods` branch fills *every* specialized method's first parameter positionally, so `add_coll(name=)`, `add_dict(name=)`, `add_table(name=)`, `add_itable(name=)`, `add_umenu(prefix=)`, `add_bpatcher(name=)`, `add_message(text=)` and `add_comment(text=)` collided as well, alongside `add_textbox(text=)`, `add_subpatcher(text=)`, `add_gen_codebox(code=)`, `add_rnbo(text=)` and `add_floatparam`/`add_intparam`'s `initial=`. A single `_dispatch` helper now applies one rule at every branch, and finds the parameter name by introspection rather than from a table, so adding an entry to `Patcher._maxclass_methods` cannot silently reintroduce the collision. The test drives off that table for the same reason.

- **`.add(<number>, name=...)` no longer leaks a stray `name` property into the patch.** The keyword names the *parameter* (it becomes `parameter_longname`), but it was read without being removed from `**kwds`, so it was also emitted as a box property. The positional form, `.add(1.5, "freq")`, is unchanged and still wins over a `name=` keyword.

- **Fixed alongside: `add_umenu()` crashed unless `items` was given** -- `TypeError: object of type 'NoneType' has no len()` -- despite the parameter being optional, which also meant `p.add("umenu")` had never worked. The `cast(List[str], items)` masking the `Optional` from mypy was the tell.

### Fixed: box port counts -- explicit zeros, and subpatchers that track their contents

- `Box.__init__` used `numoutlets or 1` / `numinlets or 0`, so an explicit `numoutlets=0` was silently promoted to 1: an object deliberately created with no outlets still claimed one, and could therefore be used as a connection source. Both now use `x if x is not None else default`, so a meaningful 0 survives. (The `numinlets` line was not actually defective -- its default is already 0 -- but is spelled the same way for clarity.)

- **A subpatcher box now declares as many ports as it really has.** `inlet` / `outlet` objects are normally added to a nested patcher *after* the subpatcher box exists, so the counts fixed at construction went stale, and Max renders a box's declared count -- a `p sub` holding three `outlet` objects but declaring one emitted a patch whose other two outlets could not be connected. `Box.render()` now syncs the counts (and `outlettype`) from the nested patcher's `inlet`/`outlet` objects, reusing the same derivation `lint()` already used to report the discrepancy.

- The sync only overrides a dimension it actually counted objects for, because a nested patcher can hold I/O that this cannot interpret: `gen~` and `rnbo~` declare theirs with `in`/`out` objects, and an empty subpatcher is a stub the caller has yet to fill. Zeroing those boxes' ports would be worse than keeping the constructed default, so they are left alone.

- `add_subpatcher` now states its port defaults (1 inlet, 1 outlet) explicitly instead of passing a falsy `0` and relying on `Box.__init__` to promote it -- which is what the previous `numoutlets or 0` did in practice. This keeps `gen~`/`rnbo~` boxes, which are created through this path, exactly as before.

- Regression tests in `tests/test_subpatch.py` cover all four cases: explicit zeros, port tracking, empty-subpatcher defaults, and `gen~`/`rnbo~` ports surviving.

### Fixed: nulls no longer reach the patch -- `_remove_none_entries` recurses

- `Box._remove_none_entries` dropped None-valued keys only at the top level, so anything one level down survived. `add_intparam` writes `parameter_mmax` unconditionally, which meant an unset maximum shipped as `"parameter_mmax": null` inside `saved_attribute_attributes` -- and Max distinguishes an absent key from a null one. (`add_floatparam` omits the key entirely; the asymmetry was the tell, and the method's own `TODO: make recursive` was the same symptom.) Fixed by making the scrub recursive rather than special-casing the key, which closes the class instead of the instance.

- Lists are walked but **not** filtered: a None *element* is positional -- an `outlettype` slot, say -- so dropping it would change the arity. Tuples are left alone so `Rect`, a NamedTuple, survives as itself. Loading is unaffected, since `Box.from_dict` bypasses `__init__` entirely.

- `tests/test_param.py` now asserts that a representative patch contains no nulls at any depth. It reads back `to_json()` rather than `to_dict()`, because only the former renders the boxes -- asserting over `to_dict()` inspects an empty patcher and passes for the wrong reason. That trap is recorded in `TODO.md`.

### Fixed: matrix layout fragmented a signal chain when boxes were added in reverse order

- `MatrixLayoutManager` treated any object with *at most one* input as the start of a signal chain, which makes every mid-chain object a chain start. A chain stops as soon as it reaches an object another chain already claimed, so whichever mid-chain object came first in iteration order consumed the tail and stranded the real source: `cycle~ -> gain~ -> ezdac~` was detected as **three** chains -- and therefore laid out as three matrix columns -- purely because the boxes were added in reverse signal order. A chain start is now an object with no inputs at all.

- The recorded symptom for this was "fix cycle handling", but cycles were never the defect: pure cycles, cycles with an external feeder, and self-loops all traced correctly before and after. Regression tests in `tests/test_layout_matrix.py` cover creation order, parallel chains meeting at a shared sink, all three cycle shapes, and disconnected objects.

### Fixed: `MaxRefDB.search()` treated `%` and `_` as wildcards

- The query was interpolated into a `LIKE` pattern unescaped, so SQL metacharacters in a search term were executed rather than matched. `search("%")` returned the entire database (1175 objects), `search("_")` likewise, and `search("gain_")` returned 16 unrelated objects because `_` matches any single character. Since Max object names routinely contain `_` (`jit_kernel`), this was reachable in ordinary use. The term is now escaped and the clause declares `ESCAPE '\'`.

- **`search()` with no recognized field now raises `ValueError`** instead of building `WHERE  ORDER BY` and failing inside sqlite with `OperationalError: near "ORDER": syntax error`. The recognized set is exposed as `MaxRefDB.SEARCHABLE_FIELDS`.

## [0.3.6]

### Removed: incremental layout; `optimize_layout()` is batch-only again

- `Patcher.optimize_layout()` no longer takes the `changed_objects` parameter added in 0.3.5 -- it takes no arguments and always performs a full, whole-patch layout. The incremental machinery in the layout managers was removed with it: `LayoutManager.should_use_incremental`, `get_affected_objects`, `get_connected_objects`, `_incremental_layout`, `_find_non_overlapping_position`, and the `INCREMENTAL_THRESHOLD` constant (`layout/base.py`); the `optimize_layout(changed_objects)` overrides in `layout/grid.py` and `layout/flow.py` (they now implement `_full_layout` and inherit the batch entry point, with flow's `<2 objects` guard moved into `_full_layout`); and `layout/matrix.py`'s override (now `_full_layout`, with `ColumnarLayoutManager` inheriting it).

- **Rationale (scope split):** py2max owns *batch* layout -- arranging a whole patch once, typically at the end of programmatic creation. Interactive, per-edit ("live") relayout belongs to the editor that owns the editing session (`py2max-server`), which handles it client-side. The incremental path existed only to serve that live case and was never exercised by a batch caller (batch `optimize_layout()` always passed `changed_objects=None`), so it was dead weight in the library. This reverses the 0.3.5 change, which had added the parameter as a prerequisite for a server-side auto-layout approach that was subsequently dropped.

- **Breaking:** calling `optimize_layout()` with an argument (e.g. `optimize_layout({obj.id})`) now raises `TypeError`; drop the argument. The `test_optimize_layout_forwards_changed_objects` / `..._incremental_leaves_untouched_objects_fixed` regression tests were replaced by `test_optimize_layout_is_batch_only`.

## [0.3.5]

### Fixed: `Patcher.optimize_layout()` now reaches the incremental layout path

- `Patcher.optimize_layout()` gained an optional `changed_objects: Optional[Set[str]]` parameter and forwards it to the layout manager. It previously called the manager with no arguments, silently discarding any change set, so the incremental layout engine (`layout/base.py` `optimize_layout(changed_objects)` / `should_use_incremental` / `_incremental_layout`) was unreachable through the public API -- every call forced a full relayout. Passing a set of object IDs now lets managers that support it (grid, flow) reposition only those objects and their patchline neighbours; `None` (the default) preserves the previous full-relayout behaviour, so the change is backward compatible. Matrix/columnar managers still recompute in full (they ignore the argument by design). This is the core prerequisite for server-side auto-layout, which lives in `py2max-server`.

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
