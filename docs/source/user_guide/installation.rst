Installation
============

Requirements
------------

py2max requires:

* Python 3.9 or later
* No runtime dependencies (pure Python)

The library is designed to work without any external dependencies, making it easy to integrate into existing projects.

Install from PyPI
-----------------

Once published to PyPI, py2max can be installed using pip:

.. code-block:: bash

   pip install py2max

Install from Source
-------------------

To install from source, clone the repository and install using pip:

.. code-block:: bash

   git clone https://github.com/shakfu/py2max.git
   cd py2max
   pip install .

Development Installation
------------------------

For development, use uv (recommended):

.. code-block:: bash

   git clone https://github.com/shakfu/py2max.git
   cd py2max
   uv sync
   source .venv/bin/activate

Verify Installation
-------------------

To verify the installation works correctly:

.. code-block:: python

   import py2max
   print(py2max.__version__)

   # Create a simple test patch
   p = py2max.Patcher('test.maxpat')
   osc = p.add_textbox('cycle~ 440')
   print(f"Created patch with oscillator: {osc}")

Optional Dependencies
---------------------

For the interactive server and REPL features:

.. code-block:: bash

   pip install py2max[server]

This installs ``websockets`` and ``ptpython`` for the live editing server and interactive REPL.

For enhanced layout algorithms, you can optionally install:

.. code-block:: bash

   pip install networkx matplotlib
   pip install hola-graph      # HOLA orthogonal layout
   pip install graph-layout    # COLA constraint-based layout

These are only required for advanced graph-based layout algorithms and are not needed for basic usage.

Max/MSP Integration
-------------------

py2max works with Max/MSP installations to provide enhanced object documentation and validation:

* **macOS**: Automatically detects Max.app installations in /Applications
* **Windows/Linux**: Basic functionality available without Max installation

The MaxRef system will automatically discover your Max installation and provide rich documentation for 1157+ Max objects. If Max is not found, the library falls back to basic functionality.