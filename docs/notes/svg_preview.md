# SVG Preview Feature

py2max now includes SVG export functionality that enables offline visual validation of Max patches without requiring Max to be installed.

## Overview

The SVG preview feature converts Max/MSP patch layouts to high-quality, scalable SVG graphics that can be:

- Viewed in any web browser
- Shared with collaborators
- Embedded in documentation
- Version controlled alongside code
- Rendered without binary dependencies

## Usage

### Command Line Interface

The `py2max preview` command generates SVG previews from `.maxpat` files:

```bash
# Basic usage - saves to /tmp
py2max preview my-patch.maxpat

# Specify output path
py2max preview my-patch.maxpat -o output.svg

# Custom title
py2max preview my-patch.maxpat --title "My Synthesizer"

# Hide inlet/outlet ports
py2max preview my-patch.maxpat --no-ports

# Open in browser automatically
py2max preview my-patch.maxpat --open

# Combine options
py2max preview my-patch.maxpat -o synth.svg --title "Synth" --open
```

### Programmatic API

Use the `export_svg` function in your Python code:

```python
from py2max import Patcher, export_svg

# Create a patch
p = Patcher('synth.maxpat', layout='grid')
metro = p.add_textbox('metro 500')
osc = p.add_textbox('cycle~ 440')
gain = p.add_textbox('gain~ 0.5')
dac = p.add_textbox('ezdac~')

p.add_line(metro, osc)
p.add_line(osc, gain)
p.add_line(gain, dac)
p.optimize_layout()
p.save()

# Export to SVG
export_svg(p, 'synth.svg', title="Simple Synth", show_ports=True)
```

### Export to String

For dynamic generation or embedding:

```python
from py2max import Patcher, export_svg_string

p = Patcher('patch.maxpat')
osc = p.add_textbox('cycle~ 440')

# Get SVG as string
svg_content = export_svg_string(p, show_ports=True, title="Patch")
print(svg_content)
```

## Features

### Visual Rendering

- **Boxes**: Rendered with correct positioning, sizing, and type-specific colors
  - Regular objects: Light gray fill
  - Comments: Yellow fill
  - Messages: Medium gray fill

- **Patchlines**: Connection lines between objects with proper inlet/outlet positioning

- **Ports**: Optional inlet (blue) and outlet (orange) visualization
  - Automatically detected from Max object metadata
  - Positioned based on actual inlet/outlet counts

- **Text**: Object labels with proper escaping for special characters

### Customization Options

- `show_ports` (bool): Display inlet/outlet ports (default: True)
- `title` (str|None): Add a title at the top of the SVG
- `output_path` (str|Path): Output file location

### Layout Support

SVG export works with all py2max layout managers:

- Horizontal grid
- Vertical grid
- Unified grid with clustering
- Flow-based layouts
- Columnar layouts
- Matrix layouts

## Examples

See `tests/examples/preview/svg_preview_demo.py` for comprehensive examples including:

- Basic synth patches
- Complex multi-voice systems
- Layout comparisons
- Custom styling options
- Programmatic workflows
- Temporary file usage

## Technical Details

### SVG Generation

- Pure Python implementation with no binary dependencies
- Supports both Rect objects and list/tuple coordinates
- Handles text overflow gracefully (no truncation)
- Proper XML escaping for special characters
- Scalable vector graphics (resolution independent)

### Port Detection

Inlet/outlet information is automatically obtained from:

1. Box `get_inlet_count()` and `get_outlet_count()` methods (when available)
2. MaxRef metadata (for known Max objects)
3. Fallback to private attributes

### File Locations

- Default output: `/tmp/<patchname>_preview.svg`
- Custom output: Specified via `-o` flag
- Temporary files: Cleaned up by OS

## Integration

### CI/CD Workflows

```bash
# Generate previews for all patches in tests
for patch in tests/**/*.maxpat; do
    py2max preview "$patch" -o "${patch%.maxpat}.svg"
done
```

### Documentation

```python
# Generate SVG for embedding in docs
from py2max import Patcher, export_svg

p = Patcher.from_file('example.maxpat')
export_svg(p, 'docs/images/example.svg', title="Example Patch")
```

### Version Control

SVG files are text-based and work well with git:

- Easy to diff
- Reviewable in PR interfaces
- Viewable directly on GitHub/GitLab

## Limitations

- Text rendering uses monospace font approximation
- Complex subpatchers are rendered flat
- No support for:
  - Presentation mode layouts
  - UI object states (slider positions, etc.)
  - Real-time visual updates

## Future Enhancements

Potential improvements:

- Interactive SVG with hover states
- Subpatcher expansion/collapse
- Export to other formats (PNG, PDF)
- Custom color schemes
- Animated connection flows

## See Also

- [CLI Documentation](../README.md#command-line-interface)
- [API Reference](../docs/api.md)
- [Layout Managers](../CLAUDE.md#layout-management)
