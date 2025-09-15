Changelog
=========

All notable changes to py2max will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

[Unreleased]
------------

Added
~~~~~
* Comprehensive Sphinx API documentation with autodoc
* User guide with quickstart, tutorial, and advanced usage
* Layout manager documentation with examples
* Development guide with contributing guidelines
* Testing documentation with coverage information

[0.1.1] - 2025-01-15
---------------------

Fixed
~~~~~
* **Type Safety**: Resolved all mypy type checking errors
* **Abstract Interfaces**: Enhanced abstract base classes with proper method signatures
* **Connection Validation**: Fixed property override issues in AbstractPatchline
* **Test Coverage**: Updated abstract coverage tests for new interface requirements

Changed
~~~~~~~
* **Type Annotations**: Added complete type annotations to all functions
* **Layout Manager Types**: Improved type safety in layout manager interfaces
* **Iterator Support**: Added proper __iter__ methods to abstract base classes

[0.1.0] - 2025-01-10
---------------------

Added
~~~~~
* **MaxRef Integration System**: Dynamic Max object information using .maxref.xml files

  * 1157+ Max objects automatically discovered and parsed
  * Complete documentation including methods, attributes, inlets, outlets
  * Dynamic help system via Box.help() and Box.get_info() methods
  * Backwards compatibility with existing MAXCLASS_DEFAULTS
  * Intelligent caching for performance
  * Cross-platform support for Max installations

* **Connection Validation**: Comprehensive inlet/outlet validation system

  * validate_connection() function with detailed error messages
  * InvalidConnectionError exception for invalid connection attempts
  * Patcher validate_connections parameter (default: True)
  * Object introspection methods: get_inlet_count(), get_outlet_count(), get_inlet_types(), get_outlet_types()
  * Smart object name extraction from 'newobj' text fields
  * Basic signal/control type compatibility validation

* **Advanced Layout Managers**: Intelligent positioning algorithms

  * **GridLayoutManager**: Unified grid layout with configurable flow direction

    * Connection-aware clustering to group related objects
    * Horizontal and vertical flow directions
    * optimize_layout() method for post-connection positioning
    * Cluster detection using graph connectivity algorithms
    * Type-based subdivision for large clusters

  * **FlowLayoutManager**: Signal flow-based layout

    * Signal flow analysis using patchline connections
    * Hierarchical positioning organizing objects in flow levels
    * Dual layout modes (horizontal and vertical)
    * Topology-based arrangement based on functional relationships

* **Enhanced API**: Expanded object creation and manipulation

  * Specialized add_<type> methods for Max objects
  * Rich object introspection and help system
  * Comprehensive error handling and validation
  * Layout optimization methods

Fixed
~~~~~
* **MaxClass Assignment Bug**: Fixed incorrect maxclass assignment preventing patchline connections

  * Most objects (like cycle~) now correctly use maxclass="newobj"
  * UI/specialized objects (like ezdac~) use their own name as maxclass
  * Enhanced logic in add_textbox() to check defaults properly

* **Layout Algorithm Issues**: Fixed clustering implementation problems

  * Resolved early exit conditions in optimize_layout()
  * Fixed flow_direction handling in clustered layouts
  * Ensured clustered and unclustered layouts produce visibly different results
  * Implemented proper spatial separation for cluster types

Changed
~~~~~~~
* **Layout Manager API**: Unified consistent API across layout types

  * Grid and Flow layouts now use same parameter interface
  * Consistent flow_direction parameter ("horizontal"/"vertical")
  * Legacy layout managers maintained as aliases for compatibility

* **Backwards Compatibility**: Maintained full API compatibility

  * All existing code continues to work unchanged
  * Legacy MAXCLASS_DEFAULTS still supported
  * Original layout manager names still work

[0.0.1] - 2024-12-01
---------------------

Added
~~~~~
* **Core Functionality**: Initial implementation of py2max library

  * Patcher class for Max patch containers
  * Box class for Max objects
  * Patchline class for object connections
  * Round-trip conversion between Python objects and .maxpat JSON files

* **Basic Layout System**: Simple object positioning

  * HorizontalLayoutManager for left-to-right layout
  * VerticalLayoutManager for top-to-bottom layout
  * Basic positioning and spacing algorithms

* **Object Creation**: Methods for adding Max objects

  * add_textbox() for generic text-based objects
  * Specialized methods for common Max objects
  * Basic parameter and positioning support

* **File Operations**: Load and save Max patcher files

  * from_file() class method for loading existing patches
  * save() method for writing .maxpat files
  * JSON serialization and deserialization

* **Testing Framework**: Comprehensive test suite

  * ~99% code coverage
  * Tests for all major functionality
  * Property-based and parametrized testing

Development Changes
-------------------

[2025-01-15] - Documentation Release
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Added
^^^^^
* **Sphinx Documentation System**

  * Complete API reference with autodoc
  * User guide with tutorials and examples
  * Layout manager documentation
  * Development and contributing guides
  * Automated documentation building

* **Enhanced Developer Experience**

  * Type checking with mypy (zero errors)
  * Code quality with ruff (zero violations)
  * Comprehensive test coverage reporting
  * Development workflow documentation

Technical Improvements
^^^^^^^^^^^^^^^^^^^^^^
* **Type Safety**: Complete type annotation coverage
* **Code Quality**: Enhanced code organization and documentation
* **Testing**: Improved test organization and coverage reporting
* **Build System**: Streamlined development and documentation builds

Migration Guide
---------------

From 0.0.1 to 0.1.0
~~~~~~~~~~~~~~~~~~~~

No breaking changes - all existing code continues to work. New features are opt-in:

**To use MaxRef system**:

.. code-block:: python

   # Get object help (new feature)
   box = patcher.add_textbox('umenu')
   print(box.help())  # Rich documentation

**To use connection validation**:

.. code-block:: python

   # Enable validation (now default)
   patcher = Patcher('patch.maxpat', validate_connections=True)

**To use new layout managers**:

.. code-block:: python

   # New unified API (recommended)
   patcher = Patcher('patch.maxpat', layout="grid", flow_direction="horizontal")
   patcher = Patcher('patch.maxpat', layout="flow", flow_direction="vertical")

   # Legacy API still works
   patcher = Patcher('patch.maxpat', layout="horizontal")  # unchanged

**To use clustering**:

.. code-block:: python

   # Enable clustering (default for grid layout)
   patcher = Patcher('patch.maxpat', layout="grid", cluster_connected=True)

   # Add objects and connections
   # ...

   # Optimize layout to cluster connected objects
   patcher.optimize_layout()

From 0.1.0 to 0.1.1
~~~~~~~~~~~~~~~~~~~~

No breaking changes - all existing code continues to work. This release focused on:

* **Type Safety**: All mypy errors resolved
* **Developer Experience**: Better IDE support with complete type annotations
* **Test Reliability**: Enhanced test coverage for edge cases

No API changes required for existing code.

Future Plans
------------

Planned for 0.2.0
~~~~~~~~~~~~~~~~~~
* **Enhanced MaxRef Integration**: More sophisticated object discovery
* **Advanced Layout Algorithms**: Graph-based layout options
* **Subpatcher Support**: Better nested patcher handling
* **Performance Optimizations**: Faster layout algorithms for large patches

Planned for 0.3.0
~~~~~~~~~~~~~~~~~~
* **Real-time Integration**: Live patch modification capabilities
* **Visual Patch Editor**: Optional GUI for patch creation
* **Advanced Validation**: More sophisticated connection type checking
* **Template System**: Reusable patch templates and components