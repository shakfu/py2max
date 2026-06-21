Testing
=======

py2max has comprehensive test coverage (~97%) ensuring reliability and correctness. This guide covers the testing framework and practices.

Test Overview
-------------

Test Framework
~~~~~~~~~~~~~~

py2max uses **pytest** as the primary testing framework with additional tools:

* **pytest**: Test runner and framework
* **pytest-cov**: Coverage measurement
* **mypy**: Static type checking
* **ruff**: Code quality and linting

Test Statistics
~~~~~~~~~~~~~~~

Current test metrics:

* **167 tests passing**, 13 skipped
* **97% code coverage**
* **60 test files** covering all modules
* **Zero mypy errors**
* **Zero ruff violations**

Running Tests
-------------

Basic Test Execution
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Run all tests
   uv run pytest

   # Run with verbose output
   uv run pytest -v

   # Run specific test file
   uv run pytest tests/test_core.py

   # Run specific test function
   uv run pytest tests/test_core.py::test_patcher_creation

   # Run tests matching pattern
   uv run pytest -k "layout"

Coverage Reports
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Generate coverage report
   uv run pytest --cov=py2max --cov-report=html

   # View coverage in terminal
   uv run pytest --cov=py2max --cov-report=term

   # Generate detailed coverage
   make coverage  # Equivalent to above with HTML output

The HTML coverage report is generated in `outputs/_covhtml/index.html`.

Test Categories
---------------

Core Functionality Tests
~~~~~~~~~~~~~~~~~~~~~~~~~

**Location**: `tests/test_core*.py`, `tests/test_basic.py`

Tests core classes and functionality:

.. code-block:: bash

   # Run core tests
   uv run pytest tests/test_core_coverage.py -v
   uv run pytest tests/test_basic.py -v

Coverage includes:

* **Patcher creation and manipulation**
* **Box object creation and properties**
* **Patchline connections and validation**
* **File I/O operations**
* **Error handling**

Layout Manager Tests
~~~~~~~~~~~~~~~~~~~~

**Location**: `tests/test_layout*.py`

Tests all layout algorithms and positioning:

.. code-block:: bash

   # Run layout tests
   uv run pytest tests/test_layout* -v

   # Run specific layout tests
   uv run pytest tests/test_layout_builtins.py -v
   uv run pytest tests/test_layout_flow.py -v

Coverage includes:

* **Grid layout with clustering**
* **Flow layout with signal analysis**
* **Legacy horizontal/vertical layouts**
* **Layout optimization algorithms**
* **Positioning calculations**

MaxRef Integration Tests
~~~~~~~~~~~~~~~~~~~~~~~~

**Location**: `tests/test_maxref.py`

Tests Max object discovery and documentation:

.. code-block:: bash

   # Run MaxRef tests
   uv run pytest tests/test_maxref.py -v

Coverage includes:

* **Object discovery from .maxref.xml files**
* **Help text generation**
* **Connection validation**
* **Inlet/outlet counting**
* **Legacy compatibility**

Connection Validation Tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Location**: `tests/test_connection_validation.py`

Tests connection validation system:

.. code-block:: bash

   # Run validation tests
   uv run pytest tests/test_connection_validation.py -v

Coverage includes:

* **Valid connection acceptance**
* **Invalid connection rejection**
* **Error message generation**
* **Object introspection methods**
* **Validation configuration**

Abstract Base Class Tests
~~~~~~~~~~~~~~~~~~~~~~~~~

**Location**: `tests/test_abstract_coverage.py`

Tests abstract interfaces and type safety:

.. code-block:: bash

   # Run abstract tests
   uv run pytest tests/test_abstract_coverage.py -v

Coverage includes:

* **Abstract method enforcement**
* **Interface compliance**
* **Type checking integration**
* **Circular dependency prevention**

Object-Specific Tests
~~~~~~~~~~~~~~~~~~~~~

**Location**: `tests/test_*.py` (individual object types)

Tests specific Max object types:

.. code-block:: bash

   # Run object-specific tests
   uv run pytest tests/test_coll.py -v
   uv run pytest tests/test_table.py -v
   uv run pytest tests/test_message.py -v

Coverage includes:

* **Specialized object creation methods**
* **Object-specific parameters**
* **Data container functionality**
* **UI element behavior**

Test Data and Fixtures
----------------------

Test Fixtures
~~~~~~~~~~~~~

Common fixtures used across tests:

.. code-block:: python

   import pytest
   from py2max import Patcher

   @pytest.fixture
   def basic_patcher():
       """Create a basic patcher for testing."""
       return Patcher('test.maxpat')

   @pytest.fixture
   def connected_objects():
       """Create patcher with connected objects."""
       p = Patcher('connected.maxpat')
       osc = p.add_textbox('cycle~ 440')
       gain = p.add_textbox('gain~')
       p.add_line(osc, gain)
       return p, osc, gain

Test Data Generation
~~~~~~~~~~~~~~~~~~~~

Tests use various data generation strategies:

.. code-block:: python

   # Parametrized tests for multiple scenarios
   @pytest.mark.parametrize("layout_type", ["grid", "flow", "horizontal"])
   def test_layout_managers(layout_type):
       p = Patcher('test.maxpat', layout=layout_type)
       # Test implementation

   # Property-based testing for edge cases
   def test_rect_operations():
       for x, y, w, h in [(0, 0, 10, 10), (100, 200, 50, 75)]:
           rect = Rect(x, y, w, h)
           assert rect.x == x

Output Validation
~~~~~~~~~~~~~~~~~

Tests validate generated .maxpat files:

.. code-block:: python

   def test_patch_json_structure():
       p = Patcher('test.maxpat')
       osc = p.add_textbox('cycle~ 440')

       # Generate JSON and validate structure
       patch_dict = p.to_dict()
       assert 'boxes' in patch_dict
       assert len(patch_dict['boxes']) == 1

       # Validate Max-compatible format
       box_data = patch_dict['boxes'][0]['box']
       assert box_data['maxclass'] == 'newobj'
       assert 'cycle~ 440' in box_data['text']

Performance Testing
-------------------

Layout Performance Tests
~~~~~~~~~~~~~~~~~~~~~~~~

Some tests measure layout algorithm performance:

.. code-block:: bash

   # Run performance-sensitive tests
   uv run pytest tests/test_layout_coverage.py -v

These tests verify that:

* **Layout algorithms scale** with object count
* **Clustering performance** is acceptable for large patches
* **Memory usage** remains reasonable

Optional Dependency Tests
~~~~~~~~~~~~~~~~~~~~~~~~~

Tests that require optional dependencies are skipped if not available:

.. code-block:: bash

   # These will be skipped if networkx not installed
   uv run pytest tests/test_layout_networkx* -v

   # Install optional deps to run all tests
   pip install networkx pygraphviz

Writing Tests
-------------

Test Structure
~~~~~~~~~~~~~~

Follow this structure for new tests:

.. code-block:: python

   """Tests for new feature functionality."""

   import pytest
   from py2max import Patcher, Box, Patchline
   from py2max.common import Rect


   class TestNewFeature:
       """Test new feature functionality."""

       def test_basic_functionality(self):
           """Test basic feature operation."""
           p = Patcher('test.maxpat')
           # Test implementation
           assert expected_result

       def test_error_conditions(self):
           """Test error handling."""
           p = Patcher('test.maxpat')

           with pytest.raises(ExpectedError):
               # Code that should raise error
               pass

       @pytest.mark.parametrize("input_value,expected", [
           (1, "result1"),
           (2, "result2"),
       ])
       def test_parametrized_behavior(self, input_value, expected):
           """Test with multiple parameter sets."""
           result = function_under_test(input_value)
           assert result == expected

Testing Guidelines
~~~~~~~~~~~~~~~~~~

When writing tests:

1. **Test public APIs** - Focus on user-facing functionality
2. **Include edge cases** - Test boundary conditions
3. **Test error conditions** - Verify proper error handling
4. **Use descriptive names** - Test names should explain what they test
5. **Keep tests independent** - Each test should work in isolation
6. **Mock external dependencies** - Don't rely on Max installation
7. **Validate outputs** - Check generated .maxpat files are correct

Example Test Implementation
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def test_connection_validation():
       """Test that connection validation works correctly."""
       p = Patcher('test.maxpat', validate_connections=True)

       # Create objects
       osc = p.add_textbox('cycle~ 440')
       gain = p.add_textbox('gain~')

       # Valid connection should work
       line = p.add_line(osc, gain)
       assert line.src == osc.id
       assert line.dst == gain.id

       # Invalid connection should raise error
       with pytest.raises(InvalidConnectionError) as exc_info:
           p.add_line(osc, gain, outlet=10)  # cycle~ has only 1 outlet

       assert "outlet 10" in str(exc_info.value)
       assert "cycle~" in str(exc_info.value)

   def test_layout_clustering():
       """Test that grid layout clustering works."""
       p = Patcher('test.maxpat', layout="grid", cluster_connected=True)

       # Create connected objects
       objects = []
       for i in range(6):
           obj = p.add_textbox(f'object{i}')
           objects.append(obj)

       # Connect in two separate chains
       p.add_line(objects[0], objects[1])
       p.add_line(objects[1], objects[2])

       p.add_line(objects[3], objects[4])
       p.add_line(objects[4], objects[5])

       # Get initial positions
       initial_positions = [obj.patching_rect for obj in objects]

       # Optimize layout
       p.optimize_layout()

       # Get final positions
       final_positions = [obj.patching_rect for obj in objects]

       # Verify clustering worked (positions changed)
       position_changes = sum(1 for i, f in zip(initial_positions, final_positions) if i != f)
       assert position_changes >= len(objects) // 2  # At least half moved

Continuous Integration
----------------------

Automated Testing
~~~~~~~~~~~~~~~~~

The project uses CI to run tests automatically:

* **On every push** to main branch
* **On every pull request**
* **Multiple Python versions** (when configured)
* **Multiple operating systems** (when configured)

CI Pipeline includes:

1. **Install dependencies**
2. **Run full test suite**
3. **Check code coverage**
4. **Run type checking (mypy)**
5. **Run linting (ruff)**
6. **Build documentation**

Local CI Simulation
~~~~~~~~~~~~~~~~~~~~

Simulate CI locally before pushing:

.. code-block:: bash

   # Run complete test suite like CI
   uv run pytest --cov=py2max
   uv run mypy py2max
   uv run ruff check py2max

   # Build docs like CI
   cd docs
   uv run sphinx-build -b html source build

Test Maintenance
----------------

Keeping Tests Current
~~~~~~~~~~~~~~~~~~~~~

* **Update tests** when changing functionality
* **Add tests** for bug fixes to prevent regression
* **Remove obsolete tests** when features are removed
* **Refactor tests** to maintain clarity

Test Performance
~~~~~~~~~~~~~~~~

* **Keep test suite fast** - aim for <5 seconds total runtime
* **Skip expensive tests** in development (mark with `@pytest.mark.slow`)
* **Use mocking** for external dependencies
* **Parallelize tests** when possible

Coverage Goals
~~~~~~~~~~~~~~

Maintain high coverage while focusing on:

* **Critical paths** - Core functionality must be 100% covered
* **Error conditions** - All error paths should be tested
* **Public APIs** - All user-facing code must have tests
* **Edge cases** - Boundary conditions and unusual inputs

The test suite is a critical part of py2max's reliability and should be maintained with the same care as the production code.