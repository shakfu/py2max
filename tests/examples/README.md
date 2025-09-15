# py2max Examples

This directory contains working examples used throughout the py2max documentation. All examples are tested to ensure they work correctly.

## Directory Structure

- **quickstart/**: Examples from the quickstart guide
  - `basic_patch.py` - Simple oscillator patch
  - `layout_examples.py` - Grid and flow layout demonstrations
- **tutorial/**: Complete tutorial examples
  - `simple_synthesis.py` - Basic synthesizer with C major chord
  - `signal_processing_chain.py` - Complex audio processing chain
  - `interactive_controller.py` - MIDI controller interface
  - `generative_music.py` - Generative music system with patterns
- **layout/**: Layout manager examples
  - `grid_layout_examples.py` - Grid layout with clustering
  - `flow_layout_examples.py` - Flow layout with signal analysis
- **advanced/**: Advanced usage patterns
  - `subpatchers.py` - Subpatcher creation and nesting
  - `data_containers.py` - Tables, collections, and dictionaries
  - `connection_patterns.py` - Fan-out, feedback, and matrix routing
  - `error_handling.py` - Robust patch creation and validation
  - `performance_optimization.py` - Large patch optimization
  - `custom_extensions.py` - Custom patcher classes and methods
- **api/**: API reference examples
  - `patcher_api_examples.py` - Patcher class methods and features
  - `box_api_examples.py` - Box class introspection and help system

## Running Examples

All examples can be run independently:

```bash
# Run a specific example
python tests/examples/quickstart/basic_patch.py
python tests/examples/tutorial/simple_synthesis.py
python tests/examples/advanced/subpatchers.py

# Run all examples (via test suite)
uv run pytest tests/test_examples.py
```

## Example Categories

### Quickstart Examples
Basic examples for getting started with py2max, including simple patches and layout demonstrations.

### Tutorial Examples
Four comprehensive tutorials building from simple synthesis to complex generative music systems:
1. **Simple Synthesis** - Multi-oscillator chord synthesizer
2. **Signal Processing Chain** - Complete audio effects chain
3. **Interactive Controller** - MIDI controller with preset management
4. **Generative Music** - Multi-pattern algorithmic composition

### Layout Examples
Demonstrations of py2max's powerful layout managers:
- **Grid Layout** - Automatic grid positioning with clustering
- **Flow Layout** - Signal flow-based hierarchical arrangement

### Advanced Examples
Complex usage patterns including:
- **Subpatchers** - Hierarchical patch organization
- **Data Containers** - Tables, collections, and state management
- **Connection Patterns** - Advanced routing and feedback systems
- **Error Handling** - Robust patch creation with validation
- **Performance** - Optimization techniques for large patches
- **Extensions** - Custom patcher classes and methods

### API Examples
Complete demonstrations of the py2max API:
- **Patcher API** - All patcher creation and management methods
- **Box API** - Object introspection, help system, and validation

## Testing

Examples are automatically tested as part of the test suite to ensure they remain functional as the library evolves.

```bash
# Test all examples
uv run pytest tests/test_examples.py -v

# Test specific example category
uv run pytest tests/test_examples.py::test_quickstart_examples -v
uv run pytest tests/test_examples.py::test_tutorial_examples -v
uv run pytest tests/test_examples.py::test_layout_examples -v
uv run pytest tests/test_examples.py::test_advanced_examples -v
uv run pytest tests/test_examples.py::test_api_examples -v
```

## Integration with Documentation

These examples are designed to be included in the Sphinx documentation to ensure that all code examples in the docs are tested and functional. The documentation references these files directly instead of containing hardcoded examples.