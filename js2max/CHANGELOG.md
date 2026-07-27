# Changelog -- js2max

Changes to [`js2max/`](README.md), the JavaScript counterpart to py2max: the
`.maxpat` format as TypeScript types, an object model, and a bridge that builds
patches live inside Max through the `v8` object.

Kept separate from the Python package's [CHANGELOG](../CHANGELOG.md) for one
reason: **audience**. That file ships in py2max's sdist and is read by people who
installed py2max from PyPI, and js2max is not in the wheel -- so entries about
`newobject` signatures and Max's `jbogus` placeholder are noise to every reader
it reaches. js2max also changes far faster than the Python package, which was
turning that noise into most of the file. The root changelog announces js2max's
existence and points here; everything after the announcement lives in this file.

**Not** because js2max is versioned separately -- it is not versioned at all
(`package.json` says `0.0.0`, `private`). It is unpublished, ships by being
committed to this repository, and is generated from and checked against py2max:
`src/objects.ts` comes from py2max's maxref bundle, the verification patches are
emitted by py2max, and `make js2max-check` runs in py2max's CI. The two are
tightly coupled, and this split is about who reads what, not about independence.
Everything below is therefore unreleased, and will stay that way unless js2max
ever ships on its own.

Entries are newest-first, and describe what changed and why. Much of what
follows was established by running the code inside Max rather than by reading
the reference; where the two disagreed, the reference lost.

## [Unreleased]

### New: the TypeScript core builds patches live inside Max via `v8`

**Where this ended up**, since the sections below record how it got there rather
than what it does. `js2max/` builds a patch description into a running
patcher through the `v8` object, and serializes a running patcher back to a
`.maxpat`. Both directions are confirmed against Max, including the part that
matters most: a file js2max wrote **opens in Max**, ten of its fifteen boxes
byte-identical to the patch it was serialized from. A description reaches it
from a file (`read`), from a Max `dict` (`builddict`), or from py2max directly.
Two loadable artifacts are committed, so a Max user needs no toolchain, and
`src/objects.ts` is generated from py2max's maxref bundle so both packages agree
on what every Max object is. 236 tests; `make js2max-check` verifies the lot.

Nine defects were found and fixed along the way. Two were found by reading the
code; **seven were only findable by running it inside Max**, and several had
been shipping since the feature was written -- `newdefault` returning a
placeholder box rather than null for an unknown class, message boxes needing
`newobject` to receive their text at all, `getattrnames()` returning null, and
four fidelity bugs in what a serialized patch carried. `js2max/src/max.d.ts`
now marks each host declaration with its provenance, `MEASURED` meaning
established by running it rather than taken from the reference -- because two of
those bugs were ones the declared types had certified as correct.

- The spike below was closed as failing its own decision gate, with one stated reopening condition: the in-Max runtime argument. **`v8` ships in current Max, so that condition is met**, and `js2max/` is now built out around the one capability the Python package cannot have -- Python writes `.maxpat` files that Max later opens; a `v8` script runs *inside* an open patcher and can build it in place, from the same description.

- **`src/scripting.ts` is the bridge.** `instantiate(patcher, description)` turns boxes into `newdefault` calls and patchlines into `connect` calls, deriving the class name and typed-in arguments from a box's `text` (numeric tokens become numbers, because Max distinguishes the symbol `440` from the int `440`), converting `patching_rect` `[x,y,w,h]` to `Maxobj.rect` `[l,t,r,b]`, and recursing into subpatchers. It never throws for a bad box: an unknown class, or a patchline to a box that failed, lands in `result.skipped` with a reason and the rest still builds.

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

- **`extract <path> [match]`** writes out only the objects matching `match` -- default `~`, the signal objects -- with the cords among them. This is the operation that justifies reading a live patcher at all: serializing a whole patcher and saving it is a worse `cp`, since a file copy is exact and `serialize` is not. Filtering produces a patch that did not exist before, which no copy can.

- **Three patches, all generated by py2max**, one per thing worth showing. `v8-harness.maxpat` exercises every message. `save-demo.maxpat` covers the exact route out -- `save` as a message, `writePatch` from your own script. `serialize-demo.maxpat` covers the lossy one, and does not pretend copying is the use: it holds a mixed patch of five control objects and three signal ones, and `extract` writes the three out on their own. `serialize-example.js` shows two further things data allows and a copy does not -- reporting which boxes are connected to nothing, and rewriting every position to tidy the layout in place.

- **Two example scripts ship alongside** -- `max/save-example.js` and `max/serialize-example.js` -- showing each pair as a user would write it, `require("js2max.js")` and all. They are plain ES5 JavaScript, and `tests/examples.test.ts` checks every `js2max.<name>` they reference against the real CommonJS bundle, so a rename cannot break them silently.

- **Fonts are filtered against the patcher's own defaults.** Dropping them wholesale lost a comment deliberately set to 14pt; including them wrote Max's default onto every box. A `.maxpat` records `default_fontsize` / `default_fontname` / `default_fontface`, and `Patcher.getattr` reads them back -- the one case Max gives a reference point for, so a box font is written only when it differs -- and the defaults are recorded in the emitted patcher, without which the comparison loses the font it was equal to (see the review pass below).

- `js2max/max/v8-harness.maxpat` is the verification patch, **generated by py2max itself** (`scripts/gen_v8_harness.py`) -- the Python package emits a patch that loads the TypeScript bundle that builds objects from the format the Python package writes.

- **Confirmed by running it in Max**, via the harness: `this` binds as expected inside the bundled IIFE scope (the global-handle fallback was not needed), `newdefault` / `connect` / the rect conversion all work -- `demo` produced a correctly wired `cycle~ 440 -> gain~ -> ezdac~` -- and `outlet()` reports correctly. Still unverified: `message("set", ...)` on a message box, whether `newdefault` returns null or throws for an unknown class, and `build <json>` / subpatcher recursion / `snapshot`, none of which the harness exercises.

- **Fixed by that run: `clear` deleted the `[v8]` object running the script.** Removing the box that hosts a running script does not fail cleanly -- Max frees it, execution continues against the freed pointer, and the next `post()` reports `bad object` / `typedmess: post: corrupt object` / `doesn't understand "post"`. `clear` now removes only what the last build created, which is both safe and what anyone wants after `demo`; the destructive option is a separately named `clearall` that keeps the script's own box and refuses to run if it cannot identify it. `scripting.ts` gained a `keep` option and a `remove(target, objects)` for the same reason, with regression tests.

- The bridge is otherwise tested against `MockPatcher`, a recording double for the Max host, and `MockFileSystem` for the file layer, covering class-name derivation, argument coercion, rect conversion, connection indices, subpatcher recursion and failure collection. That proves the mapping is right; only running it in Max proves Max accepts the calls. `js2max/README.md` lists the three specific things a real run would settle, including whether `this` binds as expected inside a bundled scope -- `patcherOf` tries the call's `this`, then a global handle, then fails with a readable message rather than a `TypeError`.

- **Corrected against the Max JS API reference.** An earlier revision claimed connections could not be enumerated from a live patcher and cut the reverse direction down to boxes only. That was wrong: `Maxobj.patchcords` returns `inputs` and `outputs` arrays of `MaxobjConnection` (`srcobject`/`srcoutlet`/`dstobject`/`dstinlet`). `snapshot` now returns lines as well as boxes, reading only the `outputs` side so each cord is reported once rather than once per endpoint. It still describes the *patcher*, not the *file* -- a live object exposes class, name, position and cords, but not typed-in text or per-class attributes.

- Also from that reference: `instantiate` now honours `patchline.hidden` via `hiddenconnect` (it previously called `connect` unconditionally, so a hidden cord came back visible), and the host declarations cover `Maxobj.valid`, `understands`, `getattr`/`setattr`, plus `applydeep` / `applyif` / `getlogical` / `parentpatcher` on `Patcher`.

- `make js2max` builds, `make js2max-check` typechecks, tests, and fails if either artifact or the harness has drifted from its source -- the same staleness guard the Python single-file edition uses.

### Fixed: a review pass over the `v8` bridge

A read-through of the feature above, which found seven defects. Tests went from 126 to 236; `make js2max-check` covers all of it, and there is now a CI job that runs it.

- **The parent's offset was applied again inside every subpatcher.** `instantiate` forwarded its options verbatim into the recursion, so a nested box landed at the parent's offset plus its own position -- in a window where the offset means nothing, since a subpatcher's coordinates are its own. The existing subpatcher test asserted counts only, which is why it passed.

- **Box fonts were filtered against the patcher's defaults, and the defaults were then not written.** A box attribute equal to the patcher default is omitted -- that is how Max writes a file, and the only way to tell a styled box from a normal one -- but the emitted patcher recorded no `default_fontsize` / `default_fontname` / `default_fontface` to be equal *to*. A patcher defaulting to 14pt therefore lost `fontsize: 14` from every box as "unstyled" and reopened at Max's 12pt: every box changed, and nothing reported it. The defaults are now written alongside the boxes, and compared as text, since the box read and the patcher read are different calls and Max is not consistent about returning `12` versus `"12"`.

- **A message box's content lost its types.** `set` content was passed through as symbols while typed-in arguments were coerced, so a message box `1 2 3` was built holding three symbols where the file said three ints, and clicking it sent the wrong thing. Both directions now share one tokenizer. It is deliberately narrower than `Number()`, which would rewrite `gate 0x10` into `gate 16`: only Max's own number syntax converts, so `0x10`, `1e3` and `Infinity` stay symbols.

- **Commas could not be fixed, so they are reported.** `1, 2` is two messages in Max -- `A_COMMA` atoms that nothing in the JS API can produce -- so `instantiate` gained `result.warnings` for boxes that *were* built but not as described, kept separate from `skipped`, which means "does not exist". `save` writes such a patch correctly, because a description reaches the file without passing through Max.

- **Cords that did not reach the file were dropped silently.** `serialize` matched endpoints by object identity and `continue`d on a miss, so if that assumption ever failed the result was a patch with no connections and no diagnostic -- while `snapshot`, for the same lookup, already carries a `varname` fallback on the grounds that the API does not promise two reads of an object give the same wrapper. Now counted and returned as `unresolved`: expected under `extract`, where cutting the boundary is the point, and loss when serializing a whole patcher, where every endpoint is in the set by construction.

- **`keep` matched by identity alone**, on the one call whose failure frees the running script. Matching now falls back to the scripting name, then class and position. The asymmetry is deliberate: a false match leaves an object in the patcher, a missed match leaves Max executing against freed memory.

- **A typo in a `write` mode was ignored**, so `write out.maxpat buit` serialized the whole patcher -- `[v8]` box and message boxes included -- and reported success, when the request was for the last build. Unknown mode words are now refused.

### New: `verify` -- the bridge's assumptions, checked by Max itself

- Everything in `scripting.ts` is tested against `MockPatcher`, which proves the *mapping* is right and proves nothing about whether Max accepts the calls. Four assumptions sit underneath the rest of the bridge and had never been exercised by anything: that `message("set", ...)` fills a message box created by `newdefault`, that `newdefault` returns null for an unknown class rather than throwing, that a box carrying a nested patcher exposes it through `subpatcher()`, and that `snapshot` reads a live patcher. **`verify` settles all four in one click**, building what each check needs, reading back what Max actually did, and removing it again -- so it is safe to click on any patch and leaves the patcher as it found it.

- Each is reported with its observation rather than a bare verdict, because the observation is the point: a `[NO ]` line names what Max returned. What each failure would cost is recorded alongside it -- if `set` does not fill a message box then every message box js2max builds is empty and the patch looks right while doing nothing; if `newdefault` throws then every "skipped" reason js2max has ever logged has named the wrong cause.

- **The checks are themselves tested** (`test/verify.test.ts`), against a mock host configured to fail in each of those ways -- a check that cannot fail reports "yes" whether or not the assumption holds, and a verification harness nobody verified is worth about as much as the assumption it was meant to settle. `MockPatcher` grew `setFillsMessageBox` and `throwingClasses` for exactly that, and `MockMaxobj.message` now models a message box's `set` rewriting its own text, which is what makes the first check's read-back meaningful.

- **`build <json>` now takes every atom rather than the first.** Max splits a message into atoms at whitespace, so a JSON document never arrives as one symbol and the old single-argument signature could not work from a message box at all. Rejoining is as far as the script can get on its own: a message box also *ends* the message at the first `,`, so the document is expected to arrive truncated. On a parse failure the handler now reports the atom count and the text it reconstructed, which is as far as the script can get on its own. It is deliberately *not* in the harness: there is nothing to learn from watching a message box truncate a document at its first comma, and the fix is a `dict`-based route rather than another experiment.

### Fixed: two assumptions the bridge rested on turned out to be false

`verify` was run in Max. Two of its four checks failed, and both had been believed since the bridge was written.

- **`newdefault` does not return null for an unknown object class.** Max logs `<name>: No such object` to the console and **returns a box anyway**, whose `maxclass` is **`jbogus`** -- the dashed-border placeholder you get by typing a bad name into a patcher. `valid` is 1 and `boxtext` is the text asked for, so nothing short of the class name gives it away, and `instantiate` had never detected an unknown class: `skipped` stayed empty, `created` counted the dead box, and the patch quietly contained one. Every "unknown object class" reason js2max could log was unreachable in practice. It now tests for `jbogus`, reports the box, and removes the placeholder -- `skipped` means "not built", and a caller that trusts it should not be handed a patcher containing a box it was told nothing about.

  The obvious alternative detector -- `maxclass` equalling the class asked for -- is wrong, and the run that found `jbogus` proved it in the same breath: Max resolves aliases, so `t b i` comes back as `trigger` and would have read as broken.

- **`getattrnames()` returns null for some objects** -- `trigger` and `jbogus` both do -- rather than an empty array or an error. A `try` around the call does not help: the null arrives cleanly and the `TypeError` lands wherever the result is first treated as an array, several frames away. This crashed `write <path> full` on any patcher containing a `trigger`, and aborted `probe` halfway through. Every such read now goes through one guard. Found because the diagnostic reported the `TypeError` instead of dying of it.

- **`understands()` does not return a boolean**: `cycle~` answered `0` for `bang` and `trigger` answered `4342878924`. Truthy, but not `true`.

- **A message box needs `newobject`, not `newdefault`, and every message box js2max had ever built was empty.** Four routes through `newdefault` were tried in Max and all four failed: `set` with separate atoms, `set` with a single symbol, the content as creation arguments, and `setboxattr("text", ...)`. The box was real -- its attribute list matches a file-loaded message box exactly -- and it did not even resize, which a message box does to fit its contents. The accessor was not the cause either: the same run read `"diagnose"` from a file-loaded message box, and a name-by-name dump of both boxes showed the *same 27 attributes* with the text in none of them, so the content is reachable only through `boxtext` and there was no hidden key to read instead.

  `newobject` takes the box's parameters explicitly, and two calls decoded its signature between them: `newobject("message", 24, 720, 1, 2, 3)` produced `boxtext "3"` -- consuming `1` and `2` as width and font size -- while `newobject("message", 24, 752, 100, 0, "1 2 3")` produced `boxtext "\"1 2 3\""`, Max quoting a single symbol that contains spaces. So the signature is `(class, left, top, width, fontsize, ...text atoms)` and **the atoms must be passed separately**; joining them yields a box holding the literal string. `instantiate` now builds message boxes this way.

  **Confirmed in Max**: `verify` reads the box back as `"1 2 3"`. Comments are built the same way, by inference from the same signature rather than by observation, and `verify` gained a fifth check that holds them to the same standard instead of leaving it assumed. No box class is sent a `set` message any more.

- **Confirmed by the same run:** subpatcher recursion works (3 objects from 1 box plus 2 inside), and `snapshot` read 18 boxes and 10 cords with **0 unresolved** -- which is worth more than the check it was written for, since resolving every cord means object identity held across separate reads. That is the assumption `serialize` matches endpoints by, and the one `snapshot` carries a `varname` fallback against.

- `diagnose` is a new message and, like `verify`, cleans up after itself and is tested against the mock. Where `verify` reports whether an assumption held, this reports what the thing that broke it looks like -- because after a failed check the next thing needed is not another verdict but evidence to write the fix from.

### New: `builddict <name>` -- handing a patch over through a Max `dict`

- **`build <json>` cannot be made to work, and this is what replaces it.** A Max message box splits its message at every space and *ends* it at the first `,`, so a `.maxpat` handed to `[v8]` as a message arrives truncated a few characters in. No amount of argument handling fixes that; `build` already rejoins every atom it is given, and that is the ceiling of the message path.

- A `dict` has none of those limits: it is passed by **name**, so the triggering message carries one symbol and the document never meets Max's message parser; it holds nested structure natively; and it can load a document off disk itself. The harness wires it up as a three-click chain needing nothing from outside the patch -- `save js2max-dict-test.json` writes the built-in synth description, `import js2max-dict-test.json` loads it into `[dict js2max_patch]`, and `builddict js2max_patch` builds the nine boxes.

- **Confirmed in Max**: `save` wrote the description, `[dict]` imported it, and `builddict` built the nine boxes and nine cords. So `Dict.stringify()` returns JSON that `JSON.parse` accepts for a whole patch, which was the last assumption the route rested on.

- Two corrections from running it: the message is **`import`**, not `import_json`, which does not exist (`dict` answers `doesn't understand "import_json"`); and the file is written `.json` rather than `.maxpat`, because `import` picks its reader by extension and a `.maxpat` is JSON by content but not by name. The payload is `save`'s output rather than `write`'s deliberately: `write` serializes the whole patcher, `[v8]` box included, so building it would drop a second copy of the running script into the patch.

- `read <path>` opens a file *this script* chooses; `builddict` builds whatever the patch has already assembled, from a file, from a dictionary other objects built, or from JSON that arrived over the network. Both shapes of description are accepted -- a whole `.maxpat` document or a bare patcher -- through one shared unwrapper, so `build` and `builddict` cannot disagree about what a description is.

- Reached through an injectable factory rather than the `Dict` global directly, the same seam `fileio.ts` uses for `File`: the parsing and every failure path are tested outside Max (`test/mockdict.ts`), and a script run outside Max gets a sentence instead of a `ReferenceError`. The failures name the cause -- and one of them was found by the first run: **an empty dictionary stringifies to `{}`, not to an empty string**, so it parses cleanly and then failed much later as "no patcher.boxes", blaming the description for a load that never happened. Since Max creates an empty dictionary for any name nothing has bound, a typo in the name and a failed load look identical, which makes this the commonest failure rather than an exotic one; it now reports as empty and names the fix. Text that will not parse is quoted back, because Max's dictionary format is close to JSON but not confirmed to *be* JSON in every case, and a near-miss needs a different response from something else entirely.

### New: a written `.maxpat` opens in Max

The claim the whole feature rests on, finally tested rather than argued. The v8 harness -- 15 boxes, 10 cords, comments, message boxes, a `[v8]` object and a `print` -- was serialized from the live patcher, written to a file, and **opened in Max**. It loads cleanly, and ten of the fifteen boxes come back byte-identical to the source they were serialized from.

Three differences remain, all understood and none of them a defect: `fontsize: 14` on the one comment the harness deliberately styles (the other fourteen sit at Max's default and are correctly omitted); four comment heights that Max recomputed itself when wrapping the text; and `print js2max` written without port counts, because maxref states none for `print` -- and the file opening is the proof that omitting them is safe, since Max derives them from the instantiated object exactly as the design assumed.

### Fixed: three things a round-tripped patch carried that its source did not

Found by writing a real patcher to a file in Max and diffing it against the patch it came from (`scripts/check_js2max_roundtrip.py`), which is the first time a file js2max produced has been examined after a live run.

- **`fontname` and `fontsize` on every box.** A box's fonts are omitted when they match the patcher's defaults -- that is how Max writes a file -- but `getattr` returns **null** for `default_fontname`, `default_fontsize` and `default_fontface` alike, so there was nothing to compare against and the filter was inert. Fifteen boxes came back carrying `"Arial"` and `12`, which the source file records on none of them, because they are Max's own defaults. The comparison now falls back to Max's defaults when the patcher will not report its own; a patcher whose real default differs simply writes the size per box, which is verbose and still correct on screen.

- **`presentation_rect` on every box.** Max reports it whether or not the box is in presentation mode, as a copy of the patching rect, so writing it on sight put one on all fifteen. It is now written only when `presentation` is actually set.

- **The window geometry was the default, not the patcher's.** `serialize` refused to read `rect` back because `.maxpat` stores `[x, y, w, h]` while every *box* rect in the JS API is `[left, top, right, bottom]`, and guessing wrong means a patch that opens at the wrong size. Settled by `probe`: a patcher 640x560 at (85, 104) reads back `[85, 104, 640, 560]`, so a patcher's rect answers in the file's convention. It is read now.

### Changed: what a box knows, and what it is called

- **`Patcher.add` derives the box class, port counts and outlet types from the object class.** py2max's knowledge of all 1098 classes was already exported into `src/objects.ts` for the serializer and simply not used here: every box got 2 inlets and 1 outlet regardless. So `p.add("ezdac~")` is now a `maxclass: "ezdac~"` box with two inlets and no outlets, and the README's own example loses its boilerplate. This is not only ergonomics -- the demo patch had `gain~` hand-written with 2 inlets where it has 1, and a box that declares a port it does not have loses the cord attached to it, silently, when Max opens the file. Anything passed explicitly still wins.

- **`instantiate` applies the description's box attributes** -- colours, fonts, `presentation`, `hidden` -- through `setboxattr`, closing the asymmetry with `serialize`, which worked to preserve exactly what the bridge then dropped. Only attributes the box reports through `getboxattrnames()` are attempted, since asking for one it does not have is how the Max console fills up over a file that is otherwise fine; an attribute the object refuses becomes a warning and the rest of the box is still applied.

- **`nameById` now defaults to off.** Naming every created object after its model id put a `varname` on boxes that never asked for one, which `serialize` then wrote into the file -- a key py2max never writes -- and two builds into one patcher collided on those names, leaving `getnamed` answering with whichever it found first. The stated justification was that a script could not otherwise address what it built, and that was not true: `result.objects` maps every model id to its live object. Turned on explicitly, names are made unique against the patcher; a `varname` the description carries is applied either way.

- `src/commands.ts` holds the decisions the `v8` messages make -- mode parsing, the own-file refusal, `extract`'s matching -- because `entry.v8.ts` assigns to `inlets` / `outlets` / `autowatch` at load and so cannot be imported by any test. That was where the code with the edge cases had accumulated. The `firstobject` walk went from five copies to one exported `objectsOf`, and `STRUCTURAL` / `isPlain` are now shared between the two directions rather than restated in each.

- **The Max version is generated from py2max** (`MAX_VER_*`) rather than restated as a literal in `model.ts`, where it would have gone quietly stale at the first bump. `src/index.ts` was missing the bridge, the file I/O and `serialize`, so a TypeScript consumer reading it would have concluded js2max could not do the thing it exists for; it now re-exports the full surface, with a `/// <reference>` for the ambient Max globals that everything reachable from it needs.

- Two mock fidelity gaps, both found by tests failing for the right reason: `MockPatcher` recorded connections by `varname`, which read correctly only while `instantiate` happened to name every box, and `MockMaxobj` held `varname` separately from the box attribute, where Max has one piece of state -- so a box named by the bridge reported no name to the serializer and the two directions agreed only by accident.

### Previously: an experimental TypeScript core spike (built, evaluated, closed)

- Added `ts/` (since renamed `js2max/`): the `.maxpat` format as TypeScript types plus a minimal `Patcher`/`Box`/`Patchline` model with JSON round-trip (868 lines, 32 passing tests, `make js2max-check`; needs [Bun](https://bun.sh)). Layout, maxref, the database, the CLI and SVG export were out of scope by design. `js2max/README.md` is the write-up.

- **Outcome: the spike fails its own decision gate and should not be built on.** It confirmed the type-system benefits are real and measured them: `tsc` rejects a misspelled box property, a wrong value type, a bad `patching_rect` arity, a missing structural key and a non-exhaustive maxclass `switch` -- all of which the Python package currently writes straight into the emitted patch. Notably `validate_attrs=True` warns about unknown property *names* but says nothing about *types*, and `mypy --strict` (which this project already passes) catches neither, because `Any` is strict-legal.

- **But every one of those cases is caught by the planned `TypedDict`/`Unpack` work**, which was prototyped and run under `mypy --strict` rather than assumed: mypy flags the typo (with a "did you mean `bgcolor`?" suggestion that `tsc` does not offer), the wrong type, the wrong arity, an explicit `None` for an optional key, and non-exhaustive handling via `assert_never`. Since nothing in the spike is out of Python's reach, the TODO item is closed in favour of "Typed box properties"; the in-Max runtime argument (`v8` / `node.script`) is the only remaining reason to reopen it, and this spike did not test it.

- The prototype also turned up a constraint worth knowing before that work starts: a key declared in the `TypedDict` may not also be a positional parameter, or mypy reports `Overlap between argument names and ** TypedDict items` **and silently stops checking calls to that function** -- so `BoxProps` must omit `text`. Recorded in `TODO.md`.

- Round-tripping all 14 `.maxpat` fixtures under `tests/` through the typed model passed on the first attempt, and the format types eliminate three pieces of Python machinery outright: `_remove_none_entries` (absent optionals are simply not emitted), the `from_dict` step that deletes seeded defaults a source patch lacked, and the `render()` pass that converts objects into dicts.
