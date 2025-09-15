py2max.common Module
===================

.. automodule:: py2max.common
   :members:
   :undoc-members:
   :show-inheritance:

The common module contains shared utility classes and data structures used throughout py2max.

Common Classes
--------------

Rect Class
~~~~~~~~~~

.. autoclass:: py2max.common.Rect
   :members:
   :undoc-members:
   :show-inheritance:

The Rect class is a named tuple representing rectangular areas in Max patches. It contains four fields:

* **x** (float): X coordinate of the rectangle's top-left corner
* **y** (float): Y coordinate of the rectangle's top-left corner
* **w** (float): Width of the rectangle
* **h** (float): Height of the rectangle

Usage Examples
--------------

Creating Rectangles
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from py2max.common import Rect

   # Create a rectangle at position (100, 50) with size 200x100
   rect = Rect(100, 50, 200, 100)

   # Access individual components
   print(f"Position: ({rect.x}, {rect.y})")
   print(f"Size: {rect.w} x {rect.h}")

   # Use tuple unpacking
   x, y, w, h = rect
   print(f"Unpacked: x={x}, y={y}, w={w}, h={h}")

Rectangle Operations
~~~~~~~~~~~~~~~~~~~~

Since Rect is a named tuple, it supports standard tuple operations:

.. code-block:: python

   # Immutable - create new rectangles for modifications
   rect1 = Rect(0, 0, 100, 50)

   # Move rectangle (create new instance)
   rect2 = Rect(rect1.x + 50, rect1.y + 25, rect1.w, rect1.h)

   # Resize rectangle
   rect3 = Rect(rect1.x, rect1.y, rect1.w * 2, rect1.h * 2)

Integration with Layout System
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Rect class is heavily used in the layout system:

.. code-block:: python

   from py2max import Patcher
   from py2max.common import Rect

   p = Patcher('positioned-patch.maxpat')

   # Add object with specific position
   box = p.add_textbox('cycle~ 440', patching_rect=Rect(100, 100, 66, 22))

   # Layout managers work with Rect objects
   layout_mgr = p._layout_mgr
   new_pos = layout_mgr.get_absolute_pos(Rect(50, 50, 66, 22))