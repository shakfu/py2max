py2max Documentation
====================

**py2max** is a pure Python library for offline generation of Max/MSP patcher files (.maxpat, .maxhelp, .rbnopat). It provides a Python object model that mirrors Max's patch organization with round-trip conversion capabilities.

Features
--------

* **Scripted offline generation** of Max patcher files using Python objects
* **Round-trip conversion** between JSON .maxpat files and corresponding Python objects
* **Dynamic Max object help system** using .maxref.xml files with 1157+ Max objects
* **Connection validation** to prevent invalid patchline connections
* **Intelligent layout algorithms** including grid, flow, columnar, and matrix layouts
* **SQLite database** for Max object metadata with automatic caching
* **SVG preview generation** for offline visual validation
* **Interactive server** with WebSocket-based live editing
* **Comprehensive API** with specialized methods for Max objects
* **High test coverage** (~99%) with 400+ tests

Quick Start
-----------

.. code-block:: python

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

Installation
------------

.. code-block:: bash

   pip install py2max

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   user_guide/installation
   user_guide/quickstart
   user_guide/tutorial
   user_guide/layout_managers
   user_guide/advanced_usage

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/py2max
   api/core
   api/layout
   api/maxref
   api/abstract
   api/common
   api/utils

.. toctree::
   :maxdepth: 1
   :caption: Development

   development/contributing
   development/testing
   development/changelog

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`