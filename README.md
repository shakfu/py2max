# py2max

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A pure Python library for offline generation of Max/MSP patcher files (`.maxpat`, `.maxhelp`, `.rbnopat`).

If you are looking for python3 externals for Max/MSP check out the [py-js](https://github.com/shakfu/py-js) project.

## Features

### Core Capabilities

- **Offline Patch Generation**: Scripted generation of Max patcher files using Python objects, corresponding one-to-one with Max/MSP objects in the `.maxpat` JSON format.

- **Round-trip Conversion**: Bidirectional conversion between `.maxpat` files (with arbitrary nesting) and `Patcher`, `Box`, and `Patchline` Python objects.

- **Universal Object Support**: Handle any Max object or maxclass with specialized methods for common objects.

- **Extensive Test Coverage**: ~99% test coverage with 400+ tests.

### MaxRef Integration

- **Dynamic Help System**: Access documentation for 1157 Max objects via `.maxref.xml` files from your Max installation.

- **Object Introspection**: Query inlet/outlet counts, types, methods, and attributes for any Max object.

- **Box Documentation**: Use `Box.help()` and `Box.get_info()` for rich object documentation directly in Python.

```python
p = Patcher('demo.maxpat')
cycle = p.add_textbox('cycle~ 440')
print(cycle.help())  # Complete documentation
print(f"Inlets: {cycle.get_inlet_count()}, Outlets: {cycle.get_outlet_count()}")
```

### Connection Validation

- **Automatic Validation**: Optional inlet/outlet validation when creating connections.

- **Detailed Errors**: `InvalidConnectionError` with clear messages for invalid connections.

```python
p = Patcher('patch.maxpat', validate_connections=True)
osc = p.add_textbox('cycle~ 440')
gain = p.add_textbox('gain~')
p.add_line(osc, gain)  # Valid
p.add_line(osc, gain, outlet=5)  # Raises InvalidConnectionError
```

### Layout Managers

- **Grid Layout**: Connection-aware clustering with configurable flow direction.
- **Flow Layout**: Signal flow-based hierarchical positioning.
- **Columnar Layout**: Functional column organization (Controls -> Generators -> Processors -> Outputs).
- **Matrix Layout**: Signal chains in columns, functional categories in rows.

```python
p = Patcher('patch.maxpat', layout='flow', flow_direction='vertical')
# or: layout='grid', 'columnar', 'matrix'
p.optimize_layout()  # Arrange objects after adding connections
```

### Visualization & Export

- **SVG Preview**: Offline visual validation without Max installation.
- **Interactive Server**: WebSocket server with browser-based editing and real-time sync.
- **REPL Mode**: Interactive Python REPL with live patch updates.

### Database Support

- **SQLite Storage**: Store and query Max object metadata in SQLite databases.
- **Automatic Caching**: Platform-specific cache with all 1157 objects populated on first use.
- **Category Filtering**: Query by category (Max, MSP, Jitter, M4L).

## Possible Use Cases

- Scripted patcher file creation.

- Batch modification of existing `.maxpat` files.

- Use the rich python standard library and ecosystem to help create parametrizable objects with configuration from offline sources. For example, one-of-a-kind wavetable oscillators configured from random wavetable files.

- Generation of test cases and `.maxhelp` files during external development

- Takes the pain out of creating objects with lots of parameters

- Prepopulate containers objects such as `coll`, `dict` and `table` objects with data

- Help to save time creating many objects with slightly different arguments

- Use [graph drawing / layout algorithms](docs/auto-layouts.md) on generated patches.

- Generative patch generation `(-;`

- etc..

## Quick Start

### Installation

```bash
pip install py2max
```

Or for development:

```bash
git clone https://github.com/shakfu/py2max.git
cd py2max
uv sync
source .venv/bin/activate
```

## Usage Examples

```python
p = Patcher('my-patch.maxpat')
osc1 = p.add_textbox('cycle~ 440')
gain = p.add_textbox('gain~')
dac = p.add_textbox('ezdac~')
osc1_gain = p.add_line(osc1, gain) # osc1 outlet 0 -> gain inlet 0
gain_dac0 = p.add_line(gain, dac, outlet=0, inlet=0)
gain_dac1 = p.add_line(gain, dac, outlet=0, inlet=1)
p.save()
```

By default, objects are returned (including patchlines), and patchline outlets and inlets are set to 0. While returned objects are useful for linking, the returned patchlines are not. Therefore, the above can be written more concisely as:

```python
p = Patcher('my-patch.maxpat')
osc1 = p.add_textbox('cycle~ 440')
gain = p.add_textbox('gain~')
dac = p.add_textbox('ezdac~')
p.add_line(osc1, gain)
p.add_line(gain, dac)
p.add_line(gain, dac, inlet=1)
p.save()
```

With builtin aliases (`.add` for `.add_*`  type methods and `.link` for `.add_line`), the above example can be written in an even more abbreviated form (and with a vertical layout) as:

```python
p = Patcher('out_vertical.maxpat', layout='vertical')
osc = p.add('cycle~ 440')
gain = p.add('gain~')
dac = p.add('ezdac~')
p.link(osc, gain)
p.link(gain, dac)
p.link(gain, dac, 1)
p.save()
```

### Object Search

Find and manipulate objects in complex patches:

```python
p = Patcher('my-patch.maxpat')

# Find by ID
osc = p.find_by_id('obj-5')

# Find all oscillators
oscillators = p.find_by_text('~')  # Case-insensitive by default

# Find specific object types
messages = p.find_by_type('message')

# Combine searches
cycle_objects = [b for b in p.find_by_text('cycle', case_sensitive=False)
                 if 'cycle~' in b.text]
```

### Semantic Object IDs

By default, py2max generates numeric IDs like `obj-1`, `obj-2`. Enable semantic IDs for more readable, object-type-based IDs:

```python
# Enable semantic IDs
p = Patcher('my-patch.maxpat', semantic_ids=True)

osc1 = p.add_textbox('cycle~ 440')    # ID: 'cycle_1'
osc2 = p.add_textbox('cycle~ 220')    # ID: 'cycle_2'
gain = p.add_textbox('gain~')         # ID: 'gain_1'
metro = p.add_textbox('metro 500')    # ID: 'metro_1'
msg = p.add_message('start')          # ID: 'message_1'

# Find objects by semantic ID
osc1 = p.find_by_id('cycle_1')
gain = p.find_by_id('gain_1')
```

Benefits of semantic IDs:
- **Easier debugging**: Immediately know object type from ID
- **Better readability**: IDs like `cycle_1` more intuitive than `obj-5`
- **Type-based counters**: Each object type gets its own counter

### Live Server

py2max provides an interactive WebSocket server for real-time visualization and editing:

```bash
# Install server dependencies (websockets + ptpython for REPL)
pip install py2max[server]

# Start interactive server
py2max serve my-patch.maxpat
```

The server provides:
- **Bidirectional sync**: Changes in Python or browser update both
- **Visual editing**: Drag objects, draw connections in browser
- **Auto-save**: Changes automatically saved to file
- **Live preview**: See patch updates in real-time

### Parsing Existing Patches

Parse existing `.maxpat` files, modify them, and save changes:

```python
p = Patcher.from_file('example1.maxpat')
# ... make some change
p.save_as('example1_mod.maxpat')
```

Another example with subpatchers:

```python
p = Patcher('out.maxpat')
sbox = p.add_subpatcher('p mysub')
sp = sbox.subpatcher
in1 = sp.add('inlet')
gain = sp.add('gain~')
out1 = sp.add('outlet')
osc = p.add('cycle~ 440')
dac = p.add('ezdac~')
sp.link(in1, gain)
sp.link(gain, out1)
p.link(osc, sbox)
p.link(sbox, dac)
p.save()
```

Note that Python classes are basically just simple wrappers around the JSON structures in a .maxpat file, and almost all Max/MSP and Jitter objects can be added to the patcher file with the `.add_textbox` or the generic `.add` methods. There are also specialized methods in the form `.add_<type>` for numbers, numeric parameters, subpatchers, and container-type objects (see the design notes below for more details).

## Installation

Simplest way is to use [uv](https://github.com/astral-sh/uv):

```sh
git clone https://github.com/shakfu/py2max.git
cd py2max
uv sync
source .venv/bin/activate
```

Note that py2max does not need to be installed to be used, so you can skip the `pip install` part if you prefer and just `cd` into the cloned directory and start using it interactively:

```sh
cd py2max
uv run python
```

For example

```python
>>> from py2max import Patcher
>>> p = Patcher.from_file("tests/data/simple.maxpat")
>>> p.boxes
[Box(id='obj-2', text=None, maxclass='ezdac~', numinlets=2, numoutlets=0, outlettype=[''], patching_rect=Rect(x=284.0, y=272.0, w=45.0, h=45.0), patcher=None), Box(id='obj-1', text='cycle~ 440', maxclass='newobj', numinlets=2, numoutlets=1, outlettype=['signal'], patching_rect=Rect(x=279.0, y=149.0, w=66.0, h=22.0), patcher=None, varname='osc1')]
```

## Quickstart

py2max has a minimal `Makefile` frontend to provide easy access to common commands:

```Makefile
.PHONY: all build test coverage clean reset

all: build

build:
    @uv build

test:
    @uv run pytest

coverage:
    @mkdir -p outputs
    @uv run pytest --cov-report html:outputs/_covhtml --cov=py2max tests

clean:
    @rm -rf outputs .*_cache

reset: clean
    @rm -rf .venv
```

## Testing

`py2max` has an extensive test suite with tests in the `tests/` folder.

One can run all tests as follows:

```sh
uv run pytest
```

This will output the results of all tests into `outputs` folder.

Note that some tests may be skipped if a required package for the test cannot be imported.

You can check which test is skipped by the following:

```sh
uv run pytest -v
```

To check test coverage:

```sh
make test
```

which essentially does the following

```sh
mkdir -p outputs
uv run pytest --cov-report html:outputs/_covhtml --cov=py2max tests
```

To run an individual test:

```sh
uv run pytest tests.test_basic
```

Note that because `py2max` primarily deals with `json` generation and manipulation, most tests have no dependencies since `json` is already built into the stdlib.

However, a bunch of tests explore the application of orthogonal graph layout algorithms and for this, a whole bunch of packages have been used, which range from the well-known to the esoteric.

As mentioned above, pytest will skip a test if required packages are not installed, so these are entirely optional tests.

If you insist on diving into the rabbit hole, and want to run all tests you will need the following packages (and their dependencies):

- [networkx](https://networkx.org): `pip install networkx`

- [matplotlib](<https://matplotlib.org>): `pip install matplotlib`

- [pygraphviz](https://github.com/pygraphviz/pygraphviz): Pygraphviz requires installing the development library of graphviz: <https://www.graphviz.org/> 
    - On macOS this can be done via:
    ```sh
    brew install graphviz
    pip install pygraphviz
    ```
    - If there are errors, try:
    ```sh
    CFLAGS="-I$(brew --prefix)/include" LDFLAGS="-L$(brew --prefix)/lib" pip install pygraphviz
    ```

- [adaptagrams](https://github.com/mjwybrow/adaptagrams): First build the adaptagrams c++ libs and then build the swig-based python wrapper.

- [hola-graph](https://github.com/shakfu/hola-graph): a pybind11 wrapper of adaptagrams HOLA algorithm. Install with `pip install hola-graph`.

- [graph-layout](https://github.com/shakfu/graph-layout): constraint-based graph layout including COLA algorithm. Install with `pip install graph-layout`.

- [tsmpy](https://github.com/uknfire/tsmpy): install from git repo

- [OrthogonalDrawing](https://github.com/hasii2011/OrthogonalDrawing): install from git repo

## Caveats

- API Docs are still not available (see CLAUDE.md for comprehensive usage documentation)

- While py2max now includes multiple layout managers (grid, flow, columnar, matrix), you can also explore [external graph layout algorithms](docs/auto-layouts.md) for specialized needs.

- Max does not refresh-from-file when open, so you will need to close and reopen patches to see changes. Use `py2max serve` for live editing with browser sync.

- For objects with tilde variants, use the `_tilde` suffix:

    ```python
    gen = p.add_gen()
    gen_tilde = p.add_gen_tilde()
    ```

## Design Notes

The `.maxpat` JSON format is actually pretty minimal and hierarchical. It has a parent `Patcher` and child `Box` entries and also `Patchlines`. Certain boxes contain other `patcher` instances to represent nested subpatchers and `gen~` patches, etc..

The above structure directly maps onto the Python implementation which consists of 3 classes: `Patcher`, `Box`, and `Patchline`. These classes are extendable via their respective `**kwds` and internal`__dict__` structures. In fact, this is the how the `.from_file` patcher classmethod is implemented.

This turns out to be the most maintainable and flexible way to handle all the differences between the hundreds of Max, MSP, and Jitter objects.

A growing list of patcher methods have been implemented to specialize and facilitate the creation of certain classes of objects which require additional configuration:

- `.add_attr`
- `.add_beap`
- `.add_bpatcher`
- `.add_codebox`
- `.add_coll`
- `.add_comment`
- `.add_dict`
- `.add_floatbox`
- `.add_floatparam`
- `.add_gen`
- `.add_intbox`
- `.add_intparam`
- `.add_itable`
- `.add_message`
- `.add_rnbo`
- `.add_subpatcher`
- `.add_table`
- `.add_textbox`
- `.add_umenu`

This is a short list, but the `add_textbox` method alone can handle almost all case. The others are really just there for convenience and to save typing.

Generally, it is recommended to start using `py2max`'s via these `add_<type>` methods, since they have most of the required parameters built into the methods and you can get IDE completion support.  Once you are comfortable with the parameters, then use the generic abbreviated form: `add`, which is less typing but tbe tradeoff is you lose the IDE parameter completion support.

## Scripts

The project has a few of scripts which may be useful:

- `convert.py`: convert `maxpat` to `yaml` for ease of reading during dev
- `compare.py`: compare using [deepdiff](https://zepworks.com/deepdiff/current/diff.html)
- `coverage.sh`: run pytest coverage and generate html coverage report

Note that if you want to build py2max as a wheel:

```bash
uv build
```

The wheel then should be in the `dist` directory.

## Command Line Usage

py2max includes a comprehensive CLI for bootstrapping, inspecting, and managing patches and databases:

### Patcher Management

```bash
# Create a starter stereo patch (use --force to overwrite)
py2max new outputs/demo.maxpat --template stereo

# Summarise basic stats for an existing patcher
py2max info outputs/demo.maxpat

# Generate SVG preview for visual validation (NEW!)
py2max preview outputs/demo.maxpat
py2max preview outputs/demo.maxpat -o docs/demo.svg --title "My Synth" --open

# Optimise layout (writes in place unless you pass -o)
py2max optimize outputs/demo.maxpat --layout matrix

# Validate connections against maxref metadata
py2max validate outputs/demo.maxpat

# Apply a transformer pipeline via CLI
py2max transform outputs/demo.maxpat --apply set-font-size=18 --apply add-comment=Auto
```

### MaxRef Metadata

```bash
# Inspect maxref metadata (list all objects)
py2max maxref --list

# Dump a specific object's metadata as JSON
py2max maxref cycle~ --json

# Scaffold a pytest skeleton for an object
py2max maxref ezdac~ --test --output tests/test_ezdac_maxref.py
```

### MaxRefDB Database Management

py2max now includes a powerful database system for managing Max object metadata with **automatic caching**:

#### Default Cache Location

MaxRefDB automatically creates and populates a cache database on first use:
- **macOS**: `~/Library/Caches/py2max/maxref.db`
- **Linux**: `~/.cache/py2max/maxref.db`
- **Windows**: `~/AppData/Local/py2max/Cache/maxref.db`

The cache is populated once and reused, providing instant access to all 1157 Max objects!

#### Cache Management

```bash
# Show cache location and status
py2max db cache location

# Manually initialize/reinitialize cache
py2max db cache init
py2max db cache init --force

# Clear cache
py2max db cache clear
py2max db cache clear --force
```

#### Working with Databases

```bash
# Create custom database with all MSP objects
py2max db create msp.db --category msp

# Create database with all objects (max, msp, jit, m4l)
py2max db create maxref.db

# Create empty database
py2max db create empty.db --empty

# Populate existing database with specific objects
py2max db populate maxref.db --objects cycle~ gain~ dac~

# Populate with a category
py2max db populate maxref.db --category jit

# Show database info
py2max db info maxref.db --summary

# List all objects
py2max db info maxref.db --list

# Search for objects
py2max db search maxref.db "oscillator"
py2max db search maxref.db --category MSP -v

# Get detailed object information
py2max db query maxref.db cycle~ --json

# Export database to JSON
py2max db export maxref.db backup.json

# Import JSON data into database
py2max db import maxref.db data.json
```

### Converters

```bash
# Convert a .maxpat file to a Python builder
py2max convert maxpat-to-python tests/data/simple.maxpat outputs/simple_builder.py

# Cache maxref metadata (uses MaxRefDB internally)
py2max convert maxref-to-sqlite --output cache/maxref.db --overwrite
```

### SVG Preview

Generate high-quality SVG previews of Max patches without requiring Max:

```bash
# Basic preview (saves to /tmp)
py2max preview my-patch.maxpat

# Custom output and title
py2max preview synth.maxpat -o docs/synth.svg --title "My Synthesizer"

# Hide inlet/outlet ports
py2max preview patch.maxpat --no-ports

# Open in browser automatically
py2max preview patch.maxpat --open

# Combine options
py2max preview synth.maxpat -o synth.svg --title "Synth" --open
```

**Python API:**

```python
from py2max import Patcher

# Create patch and export to SVG
p = Patcher('synth.maxpat', layout='grid')
osc = p.add_textbox('cycle~ 440')
gain = p.add_textbox('gain~ 0.5')
dac = p.add_textbox('ezdac~')
p.add_line(osc, gain)
p.add_line(gain, dac)
p.optimize_layout()
p.save()

# Export to SVG file (method on Patcher)
p.to_svg('synth.svg', title="Simple Synth", show_ports=True)

# Or get SVG as string
svg_content = p.to_svg_string(show_ports=False)

# Alternative: use export module directly
from py2max.export import export_svg, export_svg_string
export_svg(p, 'synth.svg', title="Simple Synth")
```

**Features:**
- High-quality, scalable vector graphics
- Automatic inlet/outlet port detection from MaxRef
- Works with all layout managers (grid, flow, matrix, etc.)
- Perfect for CI/CD, documentation, and version control
- Pure Python with no binary dependencies

### Python API Examples

```python
# Use MaxRefDB with automatic caching
from py2max.db import MaxRefDB

# Use default cache (auto-populated on first use)
db = MaxRefDB()  # Uses platform-specific cache location

# Or create custom database
db = MaxRefDB('my_custom.db', auto_populate=False)
db.populate(category='msp')  # or db.populate(['cycle~', 'gain~'])

# Pythonic access
print(f"Total objects: {len(db)}")  # or db.count
print(f"Categories: {db.categories}")

if 'cycle~' in db:
    cycle = db['cycle~']
    print(cycle['digest'])

# Search and filter
results = db.search('filter')
msp_objects = db.by_category('MSP')

# Export/import
db.export('backup.json')
db.load('data.json')

# Get summary statistics
summary = db.summary()
print(f"Database: {summary}")

# Get cache location (using static methods)
print(f"Cache: {MaxRefDB.get_default_db_path()}")
print(f"Cache dir: {MaxRefDB.get_cache_dir()}")

# Apply transformer pipeline
from py2max import Patcher
from py2max.transformers import run_pipeline, set_font_size, optimize_layout

patcher = Patcher('outputs/transform_example.maxpat')
patcher.add_textbox('cycle~ 440')
patcher.add_textbox('ezdac~')

run_pipeline(patcher, [set_font_size(18.0), optimize_layout('grid')])
patcher.save()
```

## Examples of Use

- [Generate Max patchers for faust2rnbo](https://github.com/grame-cncm/faust/blob/master-dev/architecture/max-msp/rnbo.py)

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Quick Contribution Checklist

- [ ] Fork the repository
- [ ] Create a feature branch
- [ ] Run `make quality` (linting + type checking)
- [ ] Run `make test` (ensure all tests pass)
- [ ] Update documentation if needed
- [ ] Submit a pull request

### Development Setup

```bash
git clone https://github.com/shakfu/py2max.git
cd py2max
uv sync
source .venv/bin/activate
make test  # Verify everything works
```

## Credits and Licensing

All rights reserved to the original respective authors:

- Steve Kieffer, Tim Dwyer, Kim Marriott, and Michael Wybrow. HOLA: Human-like Orthogonal Network Layout. In Visualization and Computer Graphics, IEEE Transactions on, Volume 22, Issue 1, pages 349 - 358. IEEE, 2016. DOI

- Aric A. Hagberg, Daniel A. Schult and Pieter J. Swart, “Exploring network structure, dynamics, and function using NetworkX”, in Proceedings of the 7th Python in Science Conference (SciPy2008), Gäel Varoquaux, Travis Vaught, and Jarrod Millman (Eds), (Pasadena, CA USA), pp. 11–15, Aug 2008

- A Technique for Drawing Directed Graphs Emden R. Gansner, Eleftherios Koutsofios, Stephen C. North, Kiem-phong Vo • IEEE TRANSACTIONS ON SOFTWARE ENGINEERING • Published 1993

- Gansner, E.R., Koren, Y., North, S. (2005). Graph Drawing by Stress Majorization. In: Pach, J. (eds) Graph Drawing. GD 2004. Lecture Notes in Computer Science, vol 3383. Springer, Berlin, Heidelberg. <https://doi.org/10.1007/978-3-540-31843-9_25>

- An open graph visualization system and its applications to software engineering Emden R. Gansner, Stephen C. North • SOFTWARE - PRACTICE AND EXPERIENCE • Published 2000
