py2max.maxref Module
===================

.. automodule:: py2max.maxref
   :members:
   :undoc-members:
   :show-inheritance:

The maxref module provides dynamic Max object information using .maxref.xml files from Max installations.

MaxRef System Overview
----------------------

The MaxRef integration system automatically discovers and parses Max object documentation, providing:

* **1157+ Max objects** automatically discovered and parsed
* **Complete documentation** including methods, attributes, inlets, outlets, examples
* **Dynamic help system** via Box.help() and Box.get_info() methods
* **Backwards compatibility** with existing MAXCLASS_DEFAULTS
* **Intelligent caching** for performance
* **Cross-platform support** for Max installations

Main Classes
------------

MaxRef Cache
~~~~~~~~~~~~

.. autoclass:: py2max.maxref.MaxRefCache
   :members:
   :undoc-members:
   :show-inheritance:

The MaxRefCache class manages the loading, parsing, and caching of Max object documentation.

Key Functions
-------------

Object Information
~~~~~~~~~~~~~~~~~~

.. autofunction:: py2max.maxref.get_object_help

.. autofunction:: py2max.maxref.get_object_info

.. autofunction:: py2max.maxref.get_available_objects

Connection Validation
~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: py2max.maxref.validate_connection

.. autofunction:: py2max.maxref.get_inlet_count

.. autofunction:: py2max.maxref.get_outlet_count

.. autofunction:: py2max.maxref.get_inlet_types

.. autofunction:: py2max.maxref.get_outlet_types

Legacy Compatibility
~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: py2max.maxref.get_legacy_defaults

Utility Functions
~~~~~~~~~~~~~~~~~

.. autofunction:: py2max.maxref.replace_tags

Usage Examples
--------------

Getting Object Help
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from py2max.maxref import get_object_help, get_available_objects

   # See all available objects
   objects = get_available_objects()  # Returns 1157+ objects
   print(f"Available objects: {len(objects)}")

   # Get help for any object
   help_text = get_object_help('umenu')
   print(help_text)

Using Box Help Methods
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from py2max import Patcher

   p = Patcher('help-demo.maxpat')
   cycle = p.add_textbox('cycle~ 440')

   # Get formatted help
   print(cycle.help())

   # Get structured object information
   info = cycle.get_info()
   print(f"Methods: {len(info['methods'])}")
   print(f"Attributes: {len(info['attributes'])}")

Connection Validation
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from py2max import Patcher, InvalidConnectionError

   # Validation enabled by default
   p = Patcher('patch.maxpat', validate_connections=True)
   osc = p.add_textbox('cycle~ 440')
   gain = p.add_textbox('gain~')

   # Valid connections work normally
   p.add_line(osc, gain)

   # Invalid connections raise detailed exceptions
   try:
       p.add_line(osc, gain, outlet=5)  # cycle~ only has 1 outlet
   except InvalidConnectionError as e:
       print(f"Connection error: {e}")

   # Object introspection
   print(f"cycle~ has {osc.get_inlet_count()} inlets")
   print(f"cycle~ has {osc.get_outlet_count()} outlets")