# py2max

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A pure Python library for offline generation of Max/MSP patcher files (`.maxpat`, `.maxhelp`, `.rbnopat`).

If you are looking for Python 3 externals for Max/MSP, check out the [py-js](https://github.com/shakfu/py-js) project.

## Installation

```bash
pip install py2max

# With interactive server support
pip install py2max[server]
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
- **Universal Object Support** - Works with any Max/MSP/Jitter object
- **99% Test Coverage** - 418+ tests ensure reliability

### Interactive Server (New in 0.2.x)

Real-time browser-based patch editing with bidirectional sync:

```bash
py2max serve my-patch.maxpat
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

Access documentation for 1157 Max objects:

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
from py2max import MaxRefDB

db = MaxRefDB()  # Auto-cached on first use
print(len(db))   # 1157 objects

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

```bash
# Start server with browser editing
py2max serve my-patch.maxpat

# With REPL in same terminal
py2max serve my-patch.maxpat --repl
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

## Testing

```bash
make test        # Run all tests
make typecheck   # Type checking with mypy
make lint        # Linting with ruff
make docs        # Build documentation
```

## Design Notes

The `.maxpat` JSON format maps directly to three Python classes:

- **`Patcher`** - The patch container with boxes and patchlines
- **`Box`** - Individual Max objects
- **`Patchline`** - Connections between boxes

All classes are extendable via `**kwargs`, allowing any Max object configuration. The `add_textbox()` method handles most objects, with specialized methods (`add_subpatcher()`, `add_coll()`, etc.) for objects requiring extra configuration.

## Caveats

- Max doesn't refresh from file when open - close and reopen to see changes, or use `py2max serve` for live editing
- For tilde variants, use the `_tilde` suffix: `p.add_gen()` vs `p.add_gen_tilde()`
- API docs in progress - see `CLAUDE.md` for comprehensive usage

## Examples

See the `examples/` directory for demonstrations:

- `auto_layout_demo.py` - Complex synthesizer with layout optimization
- `nested_patcher_demo.py` - Subpatcher navigation
- `columnar_layout_demo.py` - Functional column organization
- `matrix_layout_demo.py` - Signal chain matrix layout

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
