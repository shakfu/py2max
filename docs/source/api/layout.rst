py2max.layout Module
====================

.. automodule:: py2max.layout
   :members:
   :undoc-members:
   :show-inheritance:

The layout module provides sophisticated algorithms for positioning Max objects in patches.

The layout system includes several layout manager classes:

* **LayoutManager** - Base layout manager providing fundamental positioning capabilities with horizontal flow layout
* **GridLayoutManager** - Unified grid layout handling both horizontal and vertical arrangements with configurable flow direction, connection-aware clustering to group related objects, smart positioning with automatic wrapping, and layout optimization to minimize connection distances
* **FlowLayoutManager** - Intelligent signal flow-based positioning with signal flow analysis using patchline connections, hierarchical positioning organizing objects in flow levels, dual layout modes supporting horizontal and vertical flow, and topology-based arrangement based on functional relationships
* **HorizontalLayoutManager** and **VerticalLayoutManager** - Legacy layout managers maintained for backward compatibility (now aliases for GridLayoutManager with appropriate flow directions)

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