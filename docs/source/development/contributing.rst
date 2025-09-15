Contributing
============

We welcome contributions to py2max! This guide explains how to contribute effectively.

Getting Started
---------------

Development Setup
~~~~~~~~~~~~~~~~~

1. **Fork and clone the repository**:

   .. code-block:: bash

      git clone https://github.com/your-username/py2max.git
      cd py2max

2. **Set up development environment** (recommended with uv):

   .. code-block:: bash

      uv sync
      source .venv/bin/activate

   Or with pip:

   .. code-block:: bash

      pip install -e ".[dev,docs]"

3. **Verify the setup**:

   .. code-block:: bash

      uv run pytest
      uv run mypy py2max
      uv run ruff check py2max

Project Structure
~~~~~~~~~~~~~~~~~

.. code-block::

   py2max/
   ├── py2max/              # Main package
   │   ├── __init__.py      # Package exports
   │   ├── core.py          # Core classes (Patcher, Box, Patchline)
   │   ├── layout.py        # Layout managers
   │   ├── maxref.py        # MaxRef integration system
   │   ├── abstract.py      # Abstract base classes
   │   ├── common.py        # Common utilities (Rect)
   │   └── utils.py         # Utility functions
   ├── tests/               # Comprehensive test suite
   ├── docs/                # Sphinx documentation
   ├── scripts/             # Development scripts
   └── pyproject.toml       # Project configuration

Development Workflow
--------------------

Making Changes
~~~~~~~~~~~~~~

1. **Create a feature branch**:

   .. code-block:: bash

      git checkout -b feature/your-feature-name

2. **Make your changes** following the coding standards below

3. **Add tests** for new functionality:

   .. code-block:: bash

      # Add tests in tests/test_your_feature.py
      uv run pytest tests/test_your_feature.py -v

4. **Run the full test suite**:

   .. code-block:: bash

      uv run pytest

5. **Check code quality**:

   .. code-block:: bash

      uv run ruff check py2max
      uv run mypy py2max

6. **Build and test documentation**:

   .. code-block:: bash

      cd docs
      uv run sphinx-build -b html source build

Testing
~~~~~~~

py2max has extensive test coverage (~97%). When contributing:

* **Write tests** for all new functionality
* **Update existing tests** if changing behavior
* **Test with different Python versions** if possible
* **Include edge cases** and error conditions

Test categories:

* **Unit tests**: Individual class/function testing
* **Integration tests**: Full patch creation workflows
* **Layout tests**: Layout manager algorithms
* **MaxRef tests**: Object discovery and validation
* **Abstract tests**: Abstract base class coverage

Running specific test categories:

.. code-block:: bash

   # Run layout tests
   uv run pytest tests/test_layout* -v

   # Run MaxRef tests
   uv run pytest tests/test_maxref.py -v

   # Run with coverage
   uv run pytest --cov=py2max --cov-report=html

Coding Standards
----------------

Code Style
~~~~~~~~~~

We use **ruff** for code formatting and linting:

.. code-block:: bash

   # Check code style
   uv run ruff check py2max

   # Auto-fix issues
   uv run ruff check py2max --fix

Key style guidelines:

* **PEP 8 compliance** with 88-character line limit
* **No trailing whitespace**
* **Consistent import ordering**
* **Clear variable names**
* **Minimal comments** - prefer self-documenting code

Type Hints
~~~~~~~~~~

All code must include **complete type hints**:

.. code-block:: python

   def add_textbox(
       self,
       text: str,
       patching_rect: Optional[Rect] = None,
       comment: Optional[str] = None
   ) -> Box:
       """Add a text-based Max object."""
       # Implementation

Run type checking:

.. code-block:: bash

   uv run mypy py2max

Docstrings
~~~~~~~~~~

Use **clear, concise docstrings** for all public APIs:

.. code-block:: python

   def add_line(self, source: Box, destination: Box,
                outlet: int = 0, inlet: int = 0) -> Patchline:
       """Connect two Max objects with a patchline.

       Args:
           source: Source Max object
           destination: Destination Max object
           outlet: Source outlet index (default: 0)
           inlet: Destination inlet index (default: 0)

       Returns:
           The created patchline object

       Raises:
           InvalidConnectionError: If connection is invalid
       """

Documentation Standards
-----------------------

All public APIs must be documented:

* **Module docstrings** explaining purpose
* **Class docstrings** with usage examples
* **Method docstrings** with parameters and return values
* **Type hints** for all parameters and returns
* **Examples** in user guide documentation

API Documentation
~~~~~~~~~~~~~~~~~

API docs are auto-generated from docstrings using Sphinx autodoc:

.. code-block:: bash

   cd docs
   uv run sphinx-build -b html source build

User Guide Documentation
~~~~~~~~~~~~~~~~~~~~~~~~

Add examples to user guide for significant new features:

* **docs/source/user_guide/tutorial.rst** - Tutorial examples
* **docs/source/user_guide/advanced_usage.rst** - Advanced features
* **docs/source/user_guide/layout_managers.rst** - Layout documentation

Contribution Types
------------------

Bug Fixes
~~~~~~~~~~

1. **Create an issue** describing the bug
2. **Include minimal reproduction case**
3. **Add regression test** to prevent recurrence
4. **Fix the bug** with minimal changes
5. **Verify fix** with existing and new tests

New Features
~~~~~~~~~~~~

1. **Discuss the feature** in an issue first
2. **Design the API** with backwards compatibility in mind
3. **Implement with tests** and documentation
4. **Add user guide examples** for significant features
5. **Update CHANGELOG.md**

Performance Improvements
~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Benchmark current performance** with realistic data
2. **Implement optimization** maintaining correctness
3. **Verify performance improvement** with benchmarks
4. **Ensure no regression** in functionality

Documentation Improvements
~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Fix typos and unclear explanations**
2. **Add missing examples**
3. **Improve API documentation**
4. **Update user guides** for new workflows

Code Review Process
-------------------

Pull Request Guidelines
~~~~~~~~~~~~~~~~~~~~~~~

* **One feature per PR** - keep changes focused
* **Descriptive title and description**
* **Reference related issues**
* **Include tests and documentation**
* **Ensure CI passes** (tests, linting, type checking)

Review Criteria
~~~~~~~~~~~~~~~

Reviews will check for:

* **Functionality** - Does it work as intended?
* **Tests** - Are there adequate tests?
* **Documentation** - Is the API documented?
* **Style** - Does it follow coding standards?
* **Performance** - Are there any regressions?
* **Backwards compatibility** - Does it break existing APIs?

Getting Help
------------

If you need help with contributing:

* **Create an issue** for questions about features
* **Join discussions** on existing issues
* **Check the documentation** for API usage
* **Look at existing tests** for examples

Issue Guidelines
----------------

Bug Reports
~~~~~~~~~~~

Include:

* **py2max version**
* **Python version**
* **Operating system**
* **Minimal reproduction case**
* **Expected vs actual behavior**
* **Error messages and stack traces**

Feature Requests
~~~~~~~~~~~~~~~~

Include:

* **Use case description**
* **Proposed API design**
* **Alternative approaches considered**
* **Backwards compatibility impact**

Security Issues
~~~~~~~~~~~~~~~

For security-related issues:

* **Do not create public issues**
* **Email maintainers privately**
* **Include detailed description**
* **Wait for response before disclosure**

Release Process
---------------

Releases follow semantic versioning:

* **Major (1.0.0)**: Breaking API changes
* **Minor (0.1.0)**: New features, backwards compatible
* **Patch (0.0.1)**: Bug fixes, backwards compatible

Maintainers handle releases, but contributors should:

* **Update CHANGELOG.md** for significant changes
* **Maintain backwards compatibility** when possible
* **Add deprecation warnings** before removing features

Thank you for contributing to py2max!