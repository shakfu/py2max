# py2max Documentation

**py2max** is a pure Python library for offline generation of Max/MSP patcher files (.maxpat, .maxhelp, .rbnopat). It provides a Python object model that mirrors Max's patch organization with round-trip conversion capabilities.

## Features

- **Scripted offline generation** of Max patcher files using Python objects
- **Round-trip conversion** between JSON .maxpat files and corresponding Python objects
- **Max for Live (.amxd)** binary read/write with presentation-mode helpers
- **Encapsulation** -- wrap a selection of objects into a subpatcher with auto-generated inlets/outlets
- **Parameters and presets** -- `pattrstorage` / `autopattr` scaffolding and parameter helpers
- **Multichannel (mc.) and poly~** convenience helpers
- **Standalone `gen.codebox~`** with inlet/outlet counts derived from the gen code
- **Color and theme helpers** with a named Max color palette
- **Dynamic Max object help system** using .maxref.xml files with 1175+ Max objects
- **Connection validation** and **keyword-attribute validation** to catch wiring and typo errors
- **Intelligent layout algorithms** including grid, flow, columnar, and matrix layouts
- **SVG preview generation** with a Max-faithful look (signal vs message ports/cables, subpatcher tinting)
- **SQLite database** for Max object metadata with automatic caching
- **Fully typed** (passes `mypy --strict`) with no runtime dependencies
- **High test coverage** with 420+ tests

!!! note
    The interactive browser-based live editor and remote REPL now live in the
    separate [py2max-server](https://github.com/shakfu/py2max-server) package
    (`pip install py2max-server`), so the core library stays small and offline.

## Quick Start

``` python
from py2max import Patcher

# Create a simple patch
p = Patcher('my-patch.maxpat')
osc = p.add_textbox('cycle~ 440')
gain = p.add_textbox('gain~')
dac = p.add_textbox('ezdac~')

# Connect objects
p.add_line(osc, gain)
p.add_line(gain, dac)

# Save the patch
p.save()
```

## Installation

``` bash
pip install py2max
```

## Next steps

- [Quickstart](user_guide/quickstart.md) -- build your first patch
- [Tutorial](user_guide/tutorial.md) -- a guided walkthrough
- [Layout Managers](user_guide/layout_managers.md) -- automatic positioning
- [Advanced Usage](user_guide/advanced_usage.md) -- subpatchers, presets, mc./poly~, theming
- [API Reference](api/py2max.md) -- the full API
