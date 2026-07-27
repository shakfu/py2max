# Building Patches Inside Max (js2max)

py2max writes `.maxpat` files that Max opens afterwards. **js2max** is the other
direction: a JavaScript bridge that runs *inside* an open patcher through Max's
`v8` object, so a patch can build objects into itself and serialize itself back
out to a `.maxpat`.

Both directions are confirmed against Max, and the runtime ships with py2max --
`pip install py2max` is all you need. There is no toolchain to set up and
nothing to download.

The capability this adds is **a patch that builds patches**: py2max writes a
description as JSON, a `[dict]` in the patch loads it, and the bridge builds it
into the open patcher. Nothing has to be closed and reopened.

## Quick start

```python
from py2max import Patcher

p = Patcher('builder.maxpat')
p.add_v8_bridge()
p.save()
```

That writes two files:

```text
builder.maxpat
js2max.v8.js
```

`add_v8_bridge()` adds a `[v8 js2max.v8.js]` object, and `save()` writes the
runtime beside the patch. Max resolves a bare filename through the folder
holding the patch, so the two sitting together need no configuration.

Nothing is written for a patcher that never called `add_v8_bridge()`, so an
ordinary `save()` never leaves a stray `.js` file behind.

Open `builder.maxpat` in Max, send the `[v8]` object a `demo` message, and three
connected objects appear in the patcher.

## Messages the bridge understands

Send these to the `[v8]` object from a message box.

| Message | Effect |
|---|---|
| `demo` / `synth` | Build a small built-in patch, to check the path works |
| `builddict <name>` | Build the patch description held in a Max `dict` |
| `read <path>` | Open a `.maxpat` from disk and build it here |
| `save <path>` | Write a description straight to a `.maxpat` -- no objects created |
| `write <path>` | Serialize the whole live patcher to a `.maxpat` |
| `write <path> built` | Serialize only what the last build created |
| `extract <path> [match]` | Write only the objects matching `match` (default `~`) |
| `clear` / `clearall` | Remove the last build, or everything but the `[v8]` box |
| `count` | Report the object count |
| `verify` / `diagnose` / `probe` | Diagnostics -- see below |

## Building a patch from Python, into a running patcher

This is the pattern the bridge exists for. py2max writes the description; the
patch loads and builds it.

```python
from py2max import Patcher
from py2max.core.common import Rect

# 1. The patch you want built, written as JSON rather than as a .maxpat.
described = Patcher('described.maxpat')
osc = described.add_textbox('cycle~ 440')
dac = described.add_textbox('ezdac~')
described.add_line(osc, dac)
open('described.json', 'w').write(described.to_json())

# 2. A patch that builds it.
builder = Patcher('builder.maxpat')
bridge = builder.add_v8_bridge(patching_rect=Rect(24, 120, 200, 22))
loader = builder.add_message('import described.json',
                             patching_rect=Rect(24, 24, 200, 22))
holder = builder.add_textbox('dict my_patch',
                             patching_rect=Rect(24, 56, 120, 22))
build = builder.add_message('builddict my_patch',
                            patching_rect=Rect(24, 88, 150, 22))
builder.add_line(loader, holder)
builder.add_line(build, bridge)
builder.save()
```

Open `builder.maxpat`, click `import described.json`, then `builddict my_patch`.
The oscillator and the DAC appear, wired.

Why a `dict` rather than passing the JSON as a message: **a Max message box ends
its message at the first comma**, so a `.maxpat` handed over as a message
arrives truncated a few characters in. A `dict` is passed by *name*, so the
message carries one symbol and the document never meets Max's message parser.
The `build <json>` message exists but cannot carry a real patch; use
`builddict`.

## Reading a live patcher back out

The reverse direction turns a patcher into data.

- `write out.maxpat` serializes the whole patcher.
- `write out.maxpat built` serializes only what the last build created.
- `extract out.maxpat ~` writes only the objects matching a string -- `~` picks
  the signal objects -- with the cords among them.

Serializing a whole patcher and saving it is a worse `cp`: a file copy is exact
and this is not. The value is in the operations a copy cannot do -- filtering a
subset into its own patch, measuring what is connected to what, or rewriting
positions and pushing them back.

`save <path>` is different, and is the one to reach for when you simply want a
file: it writes a *description* straight to disk, creating no objects, so
nothing has to be read back out of Max and nothing is lost.

## Placing the runtime yourself

```python
from py2max import js2max_runtime

js2max_runtime.path()             # -> Path to js2max.v8.js inside the package
js2max_runtime.path('commonjs')   # -> Path to js2max.js
js2max_runtime.install('~/Max/library')   # copy it somewhere on the search path
```

Installing the runtime once into a folder on Max's search path means every patch
can find it, and you can stop py2max writing a copy next to each patch by naming
the bundle yourself:

```python
p.add_v8_bridge(bundle='js2max.v8.js')   # still the shipped name -> still installed
p.add_v8_bridge(bundle='my-bridge.js')   # your file -> nothing is installed
```

Passing a name other than the shipped one tells py2max you have placed the file,
so it writes nothing.

## Writing your own `v8` script

When the message set is not enough, `require()` the CommonJS build and drive the
model and the bridge directly:

```js
var js2max = require("js2max.js");

function bang() {
    var p = new js2max.Patcher();
    var osc = p.add("cycle~ 440");
    var dac = p.add("ezdac~");        // box class and ports come from the object
    p.connect(osc, dac, 0, 0);
    p.connect(osc, dac, 0, 1);

    var result = js2max.instantiate(this.patcher, p.toPatcherDict());
    post("built " + result.created + " objects\n");
}
```

`js2max_runtime.install(dest, 'commonjs')` puts `js2max.js` where Max can
`require` it.

## Why the runtime ships with py2max

Not only convenience. js2max's table of box classes, port counts and outlet
types for 1098 object classes is **generated from py2max's own maxref data**. A
runtime paired with a different py2max version declares wrong port counts for
whatever changed between them, and a box that declares a port it does not have
silently loses the cord attached to it when Max opens the file.

Shipping both in one artifact makes that mismatch impossible. If you vendor the
runtime by hand, take it from the py2max version you are generating with.

## Checking it works

Two diagnostic messages, useful when something behaves unexpectedly:

- **`verify`** runs the five assumptions the bridge rests on -- message box
  content, unknown-class detection, subpatcher recursion, comment content, and
  reading a live patcher -- building what each needs and removing it again. One
  click; any line logged `[NO ]` is a real finding.
- **`probe`** logs what each box in the patcher reports about itself, and the
  patcher's own attributes.

Both leave the patcher as they found it.

## Things to know

- **Message boxes cannot carry commas or semicolons through the bridge.** Those
  are message separators in Max and cannot be passed as atoms, so a message box
  built from `1, 2` holds them as ordinary symbols. `instantiate` reports this in
  `result.warnings`. Writing the patch to a file with `save` is unaffected --
  a description reaches the file without passing through Max.
- **`serialize` is lossy where `save` is not.** Reading a live patcher back can
  only recover what the JS API exposes; `filename`, `textfile` and `linecount`
  have no accessor at all. A patch written this way does open in Max -- that is
  confirmed -- but it is not a byte-for-byte copy of its source.
- **The single-file edition cannot carry the runtime.** `scripts/py2max.py` is
  one dependency-free module and 160 KB of bundled JavaScript does not belong in
  it. `add_v8_bridge()` still builds the box there; `save()` raises
  `NotImplementedError` unless you pass `bundle=` for a runtime you placed
  yourself.

## Further reading

[`js2max/README.md`](https://github.com/shakfu/py2max/blob/main/js2max/README.md)
covers the TypeScript sources, the object model, what has and has not been
confirmed against Max, and how to rebuild the bundles (which needs
[Bun](https://bun.sh); using them does not).
