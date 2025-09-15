py2max.core Module
==================

.. automodule:: py2max.core
   :members:
   :undoc-members:
   :show-inheritance:

The core module contains the main classes that form the foundation of py2max:

Core Classes
------------

Patcher Class
~~~~~~~~~~~~~

.. autoclass:: py2max.core.Patcher
   :members:
   :undoc-members:
   :show-inheritance:

The Patcher class is the main interface for creating Max/MSP patches. It provides methods for:

* Adding various types of Max objects (oscillators, effects, UI elements, etc.)
* Connecting objects with patchlines
* Managing layout and positioning
* Saving and loading patch files
* Validating connections

Box Class
~~~~~~~~~

.. autoclass:: py2max.core.Box
   :members:
   :undoc-members:
   :show-inheritance:

The Box class represents individual Max objects within a patch. Each box has:

* A unique identifier
* Position and size information
* Max object type (maxclass)
* Parameters and attributes
* Help and documentation methods

Patchline Class
~~~~~~~~~~~~~~~

.. autoclass:: py2max.core.Patchline
   :members:
   :undoc-members:
   :show-inheritance:

The Patchline class represents connections between Max objects. It manages:

* Source and destination objects
* Inlet and outlet indices
* Connection validation
* Visual representation in patches

Exceptions
----------

.. autoclass:: py2max.core.InvalidConnectionError
   :members:
   :undoc-members:
   :show-inheritance:

Raised when attempting to create invalid connections between Max objects, typically when:

* Connecting to non-existent inlets or outlets
* Type mismatches between signal and control connections
* Invalid object references