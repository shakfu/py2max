py2max.abstract Module
=====================

.. automodule:: py2max.abstract
   :members:
   :undoc-members:
   :show-inheritance:

The abstract module defines abstract base classes to break circular dependencies between core.py and layout.py modules.

Abstract Base Classes
---------------------

AbstractLayoutManager
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: py2max.abstract.AbstractLayoutManager
   :members:
   :undoc-members:
   :show-inheritance:

Defines the interface that layout managers must implement, including:

* Position calculation methods
* Rectangle manipulation
* Max object class handling

AbstractBox
~~~~~~~~~~~

.. autoclass:: py2max.abstract.AbstractBox
   :members:
   :undoc-members:
   :show-inheritance:

Defines the interface for Max object boxes, including:

* Required attributes (id, maxclass, patching_rect, _kwds)
* Rendering capabilities
* Dictionary serialization
* Iterator support

AbstractPatchline
~~~~~~~~~~~~~~~~~

.. autoclass:: py2max.abstract.AbstractPatchline
   :members:
   :undoc-members:
   :show-inheritance:

Defines the interface for patchline connections, including:

* Source and destination properties
* Dictionary serialization

AbstractPatcher
~~~~~~~~~~~~~~~

.. autoclass:: py2max.abstract.AbstractPatcher
   :members:
   :undoc-members:
   :show-inheritance:

Defines the interface for patcher containers, including:

* Size properties (width, height)
* Required attributes for object and connection management

Purpose and Design
------------------

These abstract base classes serve to:

* **Break circular imports** between core and layout modules
* **Define clear interfaces** for extensibility
* **Enable type checking** with proper inheritance
* **Maintain separation of concerns** in the architecture

The abstract classes are not intended for direct use but provide the foundation for the concrete implementations in the core module.