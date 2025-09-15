py2max.abstract Module
======================

.. automodule:: py2max.abstract
   :members:
   :undoc-members:
   :show-inheritance:

The abstract module defines abstract base classes to break circular dependencies between core.py and layout.py modules.

Purpose and Design
------------------

These abstract base classes serve to:

* **Break circular imports** between core and layout modules
* **Define clear interfaces** for extensibility
* **Enable type checking** with proper inheritance
* **Maintain separation of concerns** in the architecture

The abstract classes include:

* **AbstractLayoutManager** - Interface for layout managers with position calculation methods, rectangle manipulation, and Max object class handling
* **AbstractBox** - Interface for Max object boxes with required attributes (id, maxclass, patching_rect, _kwds), rendering capabilities, dictionary serialization, and iterator support
* **AbstractPatchline** - Interface for patchline connections with source and destination properties and dictionary serialization
* **AbstractPatcher** - Interface for patcher containers with size properties (width, height) and required attributes for object and connection management

The abstract classes are not intended for direct use but provide the foundation for the concrete implementations in the core module.