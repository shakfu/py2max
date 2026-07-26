# Experimental TypeScript core -- spike results

A spike, not a port. It implements the `.maxpat` format as types plus a minimal
`Box`/`Patcher`/`Patchline` model with JSON round-trip, and nothing else: no
layout managers, no maxref, no database, no CLI, no SVG. The question it was
built to answer is whether typing the patch format in TypeScript buys enough to
justify a second implementation.

**Verdict: no. The type-system benefits are real and measurable, but every one of
them is reachable inside Python with the `TypedDict`/`Unpack` work already
planned in `TODO.md`. Per the spike's own decision gate, that means killing it.**
The one thing TypeScript could offer that Python cannot -- running inside Max
itself -- is untested here and out of scope.

Keep this directory as the evidence for that decision, not as a foundation to
build on.

## Running it

```bash
cd ts
bun install
bun run check     # tsc --noEmit, then bun test
```

Requires [Bun](https://bun.sh) (developed against 1.3) and TypeScript 5.9 via
`bunx`. 32 tests, all passing: 14 real fixture round-trips plus the type-checking
cases below.

## What the spike confirmed

### 1. The format types replace machinery, not just annotations

The Python package reaches the wire format by reflection. `to_dict` is
`vars(self)` minus underscore keys (`core/serialization.py:26`), which forces
three supporting mechanisms that simply have no analogue here:

| Python | TypeScript |
|---|---|
| `_remove_none_entries` strips `None` before emit (with its own `TODO: make recursive`) | `JSON.stringify` omits absent optionals; nothing to strip |
| `from_dict` deletes seeded public defaults the source lacked, so subpatchers round-trip faithfully | a loaded patcher is a separate type that owns no defaults |
| `render()` converts objects into dicts before serializing | a `Box` already *is* the wire shape |

That is a genuine structural simplification, and the round-trip tests pass
against all 14 `.maxpat` fixtures in `tests/` on the first attempt.

### 2. `tsc` catches what `**kwds: Any` cannot -- measured both ways

`test/typecheck.test.ts` compiles each snippet in a subprocess and asserts the
compiler rejects it for the right reason. The Python column was produced by
running the equivalent code against the package:

| input | Python (default) | Python (`validate_attrs=True`) | `mypy --strict` | `tsc` |
|---|---|---|---|---|
| `bgcolour=[0,0,0,1]` (typo) | **shipped into the `.maxpat`** | warns, **still emits it** | passes | rejects |
| `fontsize="twelve"` | **shipped as a string** | **no warning** | passes | rejects |
| 3-element `patching_rect` | shipped | no warning | passes | rejects |
| box missing `id` | shipped | no warning | passes | rejects |
| non-exhaustive `switch` on maxclass | n/a | n/a | n/a | rejects |
| `numoutlets: 1` on a `comment` | shipped | no warning | passes | rejects |

Reproduce the Python side:

```python
p = Patcher("x.maxpat")
p.add_textbox("cycle~ 440", bgcolour=[0, 0, 0, 1], fontsize="twelve")
print(json.loads(p.to_json())["patcher"]["boxes"][0]["box"])
# -> {'bgcolour': [0, 0, 0, 1], 'fontsize': 'twelve', ...} both present
```

The sharpest finding is the second row: `validate_attrs=True` catches misspelled
*names* at runtime but says nothing about *types*, and `mypy --strict` -- which
this project already runs and passes -- catches neither, because `Any` is
strict-legal. So the gap is real and currently unguarded.

### 3. Conciseness is not the payoff, as predicted

868 lines of TypeScript (571 source, 297 test) against 722 Python lines for the
comparable scope. The TS version does *less* -- no `add_*` factory family, no
semantic ids, no validation, no linting -- so at equal functionality it would be
larger, not smaller. The `TODO.md` estimate of "single-digit percent" net
reduction was, if anything, optimistic.

## Why it still fails the decision gate

The gate was: *demonstrate something the `TypedDict`/`Unpack` route cannot
reach*. That route was then prototyped and run under `mypy --strict` rather than
argued about. It caught **every** case the spike did:

| case | mypy + `Unpack[BoxProps]` reports |
|---|---|
| `bgcolour=...` (typo) | `Unexpected keyword argument "bgcolour"; did you mean "bgcolor"?` |
| `fontsize="twelve"` | `Argument "fontsize" has incompatible type "str"; expected "float"` |
| 3-element `patching_rect` | `incompatible type "tuple[float, float, float]"` |
| `varname=None` | `Argument "varname" has incompatible type "None"; expected "str"` |
| non-exhaustive maxclass handling | `Argument 1 to "assert_never" has incompatible type "Literal['comment']"` |

On the headline case Python is arguably *better*: mypy suggests the correct
spelling, which `tsc` does not. `NotRequired[...]` already makes an explicit
`None` an error, so `exactOptionalPropertyTypes` has a direct equivalent.
TypeScript remains more ergonomic -- a discriminated union beats a pile of
`@overload`s -- but ergonomics is not the gate.

One concrete constraint the prototype turned up for the Python work: a key
declared in the `TypedDict` may not also be a positional parameter, or mypy
reports `Overlap between argument names and ** TypedDict items`. So
`add_textbox(text, **kwds)` requires `BoxProps` to omit `text`. Worth knowing
before starting; it is recorded in `TODO.md`.

Against that, the costs from `TODO.md` stand unchanged and unrefuted: users are
in Python (music21, librosa, numpy, mido), the graph-layout dependencies
(networkx, pygraphviz) have no JS equal, and Node has no stdlib XML parser, so
porting `maxref/` would end the library's zero-runtime-dependency property.

## The one open question this spike did not answer

Max embeds JavaScript -- the `v8` object, and Node for Max via `node.script` --
so a TS core is the only option that could run both offline as a generator and
*inside a patch at runtime*, sharing one set of format types. Nothing here tests
that, and the Max version requirements are still unverified against the Cycling
'74 documentation.

If in-patch runtime manipulation ever becomes a goal, reopen this on that
argument alone. The type system is not a sufficient reason, and this spike is the
evidence for why.

## Layout

```
ts/
├── src/
│   ├── format.ts     # the .maxpat wire format as types
│   ├── maxclass.ts   # per-maxclass discriminated union + exhaustiveness proof
│   ├── model.ts      # Patcher / LoadedPatcher, construction and round-trip
│   └── index.ts
└── test/
    ├── roundtrip.test.ts   # all 14 fixtures under ../tests, plus construction
    └── typecheck.test.ts   # compiles bad snippets, asserts tsc rejects them
```
