py2max.layout Module
===================

.. automodule:: py2max.layout
   :members:
   :undoc-members:
   :show-inheritance:

The layout module provides sophisticated algorithms for positioning Max objects in patches.

Layout Managers
---------------

Base Layout Manager
~~~~~~~~~~~~~~~~~~~

.. autoclass:: py2max.layout.LayoutManager
   :members:
   :undoc-members:
   :show-inheritance:

The base layout manager provides fundamental positioning capabilities with horizontal flow layout.

Grid Layout Manager
~~~~~~~~~~~~~~~~~~~

.. autoclass:: py2max.layout.GridLayoutManager
   :members:
   :undoc-members:
   :show-inheritance:

The GridLayoutManager provides:

* **Unified grid layout** handling both horizontal and vertical arrangements
* **Configurable flow direction** (horizontal or vertical)
* **Connection-aware clustering** to group related objects
* **Smart positioning** with automatic wrapping
* **Layout optimization** to minimize connection distances

Flow Layout Manager
~~~~~~~~~~~~~~~~~~~

.. autoclass:: py2max.layout.FlowLayoutManager
   :members:
   :undoc-members:
   :show-inheritance:

The FlowLayoutManager offers intelligent signal flow-based positioning:

* **Signal flow analysis** using patchline connections
* **Hierarchical positioning** organizing objects in flow levels
* **Dual layout modes** supporting horizontal and vertical flow
* **Topology-based arrangement** based on functional relationships

Legacy Layout Managers
~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: py2max.layout.HorizontalLayoutManager
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: py2max.layout.VerticalLayoutManager
   :members:
   :undoc-members:
   :show-inheritance:

Legacy layout managers maintained for backward compatibility. These are now aliases for GridLayoutManager with appropriate flow directions.

Usage Examples
--------------

Grid Layout with Clustering
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Create patcher with grid layout and clustering
   p = Patcher('patch.maxpat', layout="grid", flow_direction="horizontal")

   # Add connected objects
   osc = p.add_textbox('cycle~ 440')
   gain = p.add_textbox('gain~')
   dac = p.add_textbox('ezdac~')

   # Connect objects
   p.add_line(osc, gain)
   p.add_line(gain, dac)

   # Optimize layout to cluster connected objects
   p.optimize_layout()

Flow Layout
~~~~~~~~~~~

.. code-block:: python

   # Create patcher with intelligent flow layout
   p = Patcher('patch.maxpat', layout="flow", flow_direction="vertical")

   # Add signal chain
   input_obj = p.add_textbox('adc~')
   filter_obj = p.add_textbox('biquad~')
   delay_obj = p.add_textbox('delay~')
   output_obj = p.add_textbox('dac~')

   # Connect in signal flow order
   p.add_line(input_obj, filter_obj)
   p.add_line(filter_obj, delay_obj)
   p.add_line(delay_obj, output_obj)

   # Optimize for signal flow hierarchy
   p.optimize_layout()