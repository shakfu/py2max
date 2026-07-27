# py2max

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A pure Python library for generating Max/MSP patcher files (`.maxpat`,
`.maxhelp`, `.rbnopat`) -- offline, and, via its
[js2max](#building-patches-inside-max-js2max) bridge, *inside a running Max
patcher*.

If you are looking for Python 3 externals for Max/MSP, check out the [py-js](https://github.com/shakfu/py-js) project.

## Installation

```bash
pip install py2max
```

For the browser-based live editor and remote REPL, install the companion
[`py2max-server`](https://github.com/shakfu/py2max-server) package:

```bash
pip install py2max-server
```

For development:

```bash
git clone https://github.com/shakfu/py2max.git
cd py2max
uv sync
source .venv/bin/activate
```

## Quick Start

```python
from py2max import Patcher

p = Patcher('my-synth.maxpat')
osc = p.add('cycle~ 440')
gain = p.add('gain~')
dac = p.add('ezdac~')
p.link(osc, gain)
p.link(gain, dac)
p.save()
```

That's it! Open `my-synth.maxpat` in Max to see your patch.

## Features

### Core Capabilities

- **Offline Patch Generation** - Create Max patches programmatically without Max running
- **Round-trip Conversion** - Load, modify, and save existing `.maxpat` files
- **Max for Live (.amxd)** - Read/write binary `.amxd` device files with presentation-mode helpers
- **Universal Object Support** - Works with any Max/MSP/Jitter object
- **Fully typed** - Passes `mypy --strict`; no runtime dependencies
- **Live Patch Building ([js2max](#building-patches-inside-max-js2max))** - Add generated objects to a patch that is already open in Max, and read an edited patch back into Python -- no save-and-reopen cycle
- **High Test Coverage** - 700+ tests, plus 230+ for the js2max bridge

### Max for Live (.amxd)

Generate Max for Live devices directly. `Patcher.save()` / `Patcher.from_file()`
auto-detect the `.amxd` extension and read/write the binary device format,
byte-for-byte compatible with Max-exported devices.

```python
from py2max import Patcher

# device_type: "audio_effect" (default), "instrument", or "midi_effect"
p = Patcher('gain.amxd', device_type='audio_effect')
p.enable_presentation(devicewidth=120)        # render Ableton's device strip

plugin = p.add_textbox('plugin~')             # audio in from Live
gain = p.add('live.gain~', maxclass='live.gain~')
plugout = p.add_textbox('plugout~')           # audio back to Live
gain.add_to_presentation([20, 20, 60, 136])   # show the fader in the device

p.add_line(plugin, gain, outlet=0, inlet=0)
p.add_line(gain, plugout, outlet=0, inlet=0)
p.save()                                       # writes a binary .amxd
```

Helpers: `Patcher.enable_presentation(devicewidth=...)`,
`Box.add_to_presentation([x, y, w, h])` (rejects M4L infrastructure objects and
rounds fractional coordinates), and `Patcher.enforce_integer_coords()`. M4L
binary helpers live in `py2max.m4l`.

### Building patches inside Max (js2max)

py2max writes `.maxpat` files that Max later opens. [`js2max/`](js2max/) is the
JavaScript counterpart, and does the one thing Python cannot: Max embeds a
JavaScript engine, so a `v8` script runs **inside an open patcher** and builds
into it directly, from the same patch description py2max writes.

```text
[import my-patch.json(        [builddict my_patch(
        |                              |
[dict my_patch]                [v8 js2max.v8.js]
```

Both directions work and are confirmed against Max: a description becomes live
objects, and a live patcher serializes back to a `.maxpat` that Max reopens.

**The runtime ships with py2max**, so `pip install py2max` is all you need:

```python
p = Patcher('builder.maxpat')
p.add_v8_bridge()   # adds [v8 js2max.v8.js]
p.save()            # writes builder.maxpat AND js2max.v8.js beside it
```

Max resolves a bare filename through the folder holding the patch, so the two
sitting together need no configuration. Nothing is written for a patch that
never asked for the bridge. `py2max.js2max_runtime.path()` and `install()` are
there if you would rather place it yourself.

Shipping them together is a correctness guarantee, not just a convenience:
`js2max/src/objects.ts` -- the port counts for 1098 object classes -- is
generated from py2max's own maxref data, so a runtime paired with a different
py2max version would declare wrong ports, and a box declaring a port it does not
have loses the cord attached to it when Max opens the file.

Full guide: [Building Patches Inside Max](docs/user_guide/js2max.md). Source and
what has been confirmed against Max: [`js2max/README.md`](js2max/README.md).
Building the runtime needs [Bun](https://bun.sh) (`make js2max`); using it does
not.

### Interactive Server (separate package)

Real-time browser-based patch editing with bidirectional sync lives in the
companion [`py2max-server`](https://github.com/shakfu/py2max-server) package, so
the core library stays small and offline:

```bash
pip install py2max-server
py2max-server serve my-patch.maxpat
# Opens browser at http://localhost:8000
```

**Features:**

- Drag objects, draw connections visually
- Three layout engines: **WebCola**, **ELK**, and **Dagre**
- Auto-save with debouncing
- Navigate into subpatchers
- REPL mode for Python interaction

### SVG Preview

Generate high-quality SVG previews without Max:

```bash
py2max preview my-patch.maxpat --open
```

```python
p = Patcher('synth.maxpat')
# ... add objects ...
p.to_svg('synth.svg', title="My Synth", show_ports=True)
```

### Layout Managers

Five built-in layout strategies:

| Layout | Description |
|--------|-------------|
| `grid` | Connection-aware clustering with configurable flow |
| `flow` | Signal flow-based hierarchical positioning |
| `columnar` | Controls -> Generators -> Processors -> Outputs |
| `matrix` | Signal chains in columns, categories in rows |
| `horizontal`/`vertical` | Simple grid layouts |

```python
p = Patcher('patch.maxpat', layout='flow', flow_direction='vertical')
# Add objects and connections...
p.optimize_layout()  # Arrange based on signal flow
p.save()
```

### MaxRef Integration

Access documentation for 1175 Max objects:

```python
p = Patcher('demo.maxpat')
cycle = p.add('cycle~ 440')

print(cycle.help())  # Full documentation
print(f"Inlets: {cycle.get_inlet_count()}")
print(f"Outlets: {cycle.get_outlet_count()}")
```

### Connection Validation

Optional validation catches wiring errors:

```python
p = Patcher('patch.maxpat', validate_connections=True)
osc = p.add('cycle~ 440')
gain = p.add('gain~')

p.link(osc, gain)              # Valid
p.link(osc, gain, outlet=5)    # Raises InvalidConnectionError
```

### Semantic IDs

Human-readable object IDs for easier debugging:

```python
p = Patcher('patch.maxpat', semantic_ids=True)

osc1 = p.add('cycle~ 440')   # ID: 'cycle_1'
osc2 = p.add('cycle~ 220')   # ID: 'cycle_2'
gain = p.add('gain~')        # ID: 'gain_1'

# Find by semantic ID
osc = p.find_by_id('cycle_1')
```

### SQLite Database

Query Max object metadata efficiently:

```python
from py2max.maxref import MaxRefDB

db = MaxRefDB()  # Auto-cached on first use
print(len(db))   # 1175 objects

if 'cycle~' in db:
    info = db['cycle~']
    print(info['digest'])

# Search and filter
results = db.search('filter')
msp_objects = db.by_category('MSP')
```

## Usage Examples

### Basic Patch Creation

```python
from py2max import Patcher

p = Patcher('my-patch.maxpat')
osc = p.add('cycle~ 440')
gain = p.add('gain~')
dac = p.add('ezdac~')

p.link(osc, gain)
p.link(gain, dac)
p.link(gain, dac, inlet=1)  # Stereo
p.save()
```

### Loading and Modifying Patches

```python
p = Patcher.from_file('existing.maxpat')

# Find and modify objects
for box in p.find_by_text('cycle~'):
    print(f"Found oscillator: {box.id}")

p.save_as('modified.maxpat')
```

### Subpatchers

```python
p = Patcher('main.maxpat')
sbox = p.add_subpatcher('p mysub')
sp = sbox.subpatcher

# Build the subpatcher
inlet = sp.add('inlet')
gain = sp.add('gain~')
outlet = sp.add('outlet')
sp.link(inlet, gain)
sp.link(gain, outlet)

# Connect in main patcher
osc = p.add('cycle~ 440')
dac = p.add('ezdac~')
p.link(osc, sbox)
p.link(sbox, dac)
p.save()
```

### Gen Codebox

`add_gen_codebox()` adds a standalone `gen.codebox~` object -- a complete gen
patch in a single box that sits directly in a regular Max patcher (unlike the
inner `codebox~` from `add_codebox()`, which belongs inside a `gen~`/`rnbo~`
subpatcher). Inlet/outlet counts are derived automatically from the highest
`inN`/`outN` references in the code:

```python
p = Patcher('fbdelay.maxpat')

# 1 inlet (in1), 1 outlet (out1)
osc = p.add('cycle~ 440')
cb = p.add_gen_codebox('''
Param feedback(0.5, min=0.0, max=0.95);
History fb(0.0);
out1 = in1 + fb * feedback;
fb = out1;
''')
dac = p.add('ezdac~')
p.link(osc, cb)
p.link(cb, dac)
p.save()

# Or via the add() string shortcut (single-line / `;`-terminated code)
cb = p.add('gen.codebox~ out1 = in1 * 0.5;')
```

### Object Search

```python
p = Patcher.from_file('complex-patch.maxpat')

# Find by ID
obj = p.find_by_id('obj-5')

# Find by text content
oscillators = p.find_by_text('cycle~')

# Find by object type
messages = p.find_by_type('message')
```

## Command Line Interface

### Patch Management

```bash
# Create new patch from template
py2max new demo.maxpat --template stereo

# Show patch info
py2max info demo.maxpat

# Generate SVG preview
py2max preview demo.maxpat --open

# Optimize layout
py2max optimize demo.maxpat --layout flow

# Validate connections
py2max validate demo.maxpat
```

### Interactive Server

Provided by the separate [`py2max-server`](https://github.com/shakfu/py2max-server)
package (`pip install py2max-server`):

```bash
# Start server with browser editing
py2max-server serve my-patch.maxpat

# With REPL in same terminal
py2max-server serve my-patch.maxpat --repl
```

### MaxRef Database

```bash
# Show cache status
py2max db cache location

# Create category-specific database
py2max db create msp.db --category msp

# Search objects
py2max db search maxref.db "oscillator" -v

# Query specific object
py2max db query maxref.db cycle~ --json
```

### Converters

```bash
# Convert .maxpat to Python code
py2max convert maxpat-to-python patch.maxpat output.py

# Lookup object documentation
py2max maxref cycle~ --json
```

## Use Cases

- **Scripted patch generation** - Automate repetitive patch creation
- **Batch processing** - Modify multiple `.maxpat` files programmatically
- **Parametric patches** - Generate variations from configuration files
- **Test generation** - Create `.maxhelp` files during external development
- **Container population** - Prepopulate `coll`, `dict`, `table` objects with data
- **Generative patching** - Algorithmic patch creation
- **CI/CD integration** - SVG previews for documentation and version control
- **Live patch building** - iterate on a patch while it stays open in Max, with [js2max](#building-patches-inside-max-js2max)

## Testing

```bash
make test          # Run all tests
make typecheck     # Type checking with mypy
make lint          # Linting with ruff
make docs          # Build documentation
make js2max-check  # Typecheck and test js2max, and verify its artifacts are current (needs bun)
```

## Design Notes

The `.maxpat` JSON format maps directly to three Python classes:

- **`Patcher`** - The patch container with boxes and patchlines
- **`Box`** - Individual Max objects
- **`Patchline`** - Connections between boxes

All classes are extendable via `**kwargs`, allowing any Max object configuration. The `add_textbox()` method handles most objects, with specialized methods (`add_subpatcher()`, `add_coll()`, etc.) for objects requiring extra configuration.

## Caveats

- Max doesn't refresh from file when open - close and reopen to see changes, or build straight into the open patch with [js2max](#building-patches-inside-max-js2max), or use `py2max-server serve` (from the separate `py2max-server` package) for live editing
- For tilde variants, use the `_tilde` suffix: `p.add_gen()` vs `p.add_gen_tilde()`
- API docs in progress - see `CLAUDE.md` for comprehensive usage

## Examples

The [`tests/examples/`](tests/examples/) directory contains working, tested
examples organized by topic (see its [README](tests/examples/README.md)):

- `quickstart/basic_patch.py` - Simple oscillator patch
- `tutorial/signal_processing_chain.py` - Complex audio processing chain
- `tutorial/generative_music.py` - Generative music system with patterns
- `layout/grid_layout_examples.py` - Grid layout with clustering
- `advanced/data_containers.py` - Tables, collections, and dictionaries
- `api/patcher_api_examples.py` - Patcher API reference examples

External usage:

- [faust2rnbo](https://github.com/grame-cncm/faust/blob/master-dev/architecture/max-msp/rnbo.py) - Generate Max patchers for RNBO

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
git clone https://github.com/shakfu/py2max.git
cd py2max
uv sync
source .venv/bin/activate
make test  # Verify setup
```

## License

MIT License. See [LICENSE](LICENSE) for details.

## Credits

- HOLA algorithm: Kieffer, Dwyer, Marriott, Wybrow (IEEE 2016)
- NetworkX: Hagberg, Schult, Swart (SciPy 2008)
- Graph drawing techniques: Gansner, Koutsofios, North, Vo (IEEE 1993)
