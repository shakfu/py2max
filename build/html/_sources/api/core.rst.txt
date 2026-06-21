py2max.core Module
==================

.. automodule:: py2max.core
   :members:
   :undoc-members:
   :show-inheritance:

The core module contains the main classes that form the foundation of py2max:

* **Patcher** - Main interface for creating Max/MSP patches with methods for adding various types of Max objects, connecting objects with patchlines, managing layout and positioning, saving and loading patch files, and validating connections

* **Box** - Represents individual Max objects within a patch with unique identifier, position and size information, Max object type (maxclass), parameters and attributes, and help and documentation methods (``help()``, ``get_info()``, ``get_inlet_count()``, ``get_outlet_count()``)

* **Patchline** - Represents connections between Max objects, managing source and destination objects, inlet and outlet indices, and visual representation in patches

See :doc:`py2max` for the full list of exceptions available for error handling.