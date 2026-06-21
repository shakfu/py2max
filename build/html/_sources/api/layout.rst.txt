py2max.layout Module
====================

.. automodule:: py2max.layout
   :members:
   :undoc-members:
   :show-inheritance:

The layout module provides sophisticated algorithms for positioning Max objects in patches.

Layout Manager Classes
----------------------

The layout system includes several layout manager classes:

* **LayoutManager** - Base layout manager providing fundamental positioning capabilities

* **GridLayoutManager** - Unified grid layout with configurable flow direction and connection-aware clustering

* **FlowLayoutManager** - Signal flow-based hierarchical positioning with topology analysis

* **ColumnarLayoutManager** - Functional column organization optimized for typical Max patch patterns:

  - Column 1: Controls (flonum, metro, button, slider, MIDI inputs)
  - Column 2: Generators (cycle~, saw~, noise~, play~, adsr~)
  - Column 3: Processors (gain~, lores~, delay~, reverb~, math objects)
  - Column 4: Outputs (dac~, ezdac~, print, record~, meters)

* **MatrixLayoutManager** - Matrix organization where columns represent signal chains and rows represent functional categories, ideal for multi-voice patches

* **HorizontalLayoutManager** and **VerticalLayoutManager** - Legacy aliases for GridLayoutManager

Usage Examples
--------------

Grid Layout
~~~~~~~~~~~

.. code-block:: python

   p = Patcher('patch.maxpat', layout="grid", flow_direction="horizontal")
   osc = p.add_textbox('cycle~ 440')
   gain = p.add_textbox('gain~')
   dac = p.add_textbox('ezdac~')
   p.add_line(osc, gain)
   p.add_line(gain, dac)
   p.optimize_layout()

Flow Layout
~~~~~~~~~~~

.. code-block:: python

   p = Patcher('patch.maxpat', layout="flow", flow_direction="vertical")
   input_obj = p.add_textbox('adc~')
   filter_obj = p.add_textbox('biquad~')
   output_obj = p.add_textbox('dac~')
   p.add_line(input_obj, filter_obj)
   p.add_line(filter_obj, output_obj)
   p.optimize_layout()

Columnar Layout
~~~~~~~~~~~~~~~

.. code-block:: python

   p = Patcher('patch.maxpat', layout="columnar")
   metro = p.add_textbox('metro 500')      # Column 1: Controls
   osc = p.add_textbox('cycle~ 440')       # Column 2: Generators
   filter = p.add_textbox('lores~ 1000')   # Column 3: Processors
   dac = p.add_textbox('ezdac~')           # Column 4: Outputs
   p.add_line(metro, osc)
   p.add_line(osc, filter)
   p.add_line(filter, dac)
   p.optimize_layout()

Matrix Layout
~~~~~~~~~~~~~

.. code-block:: python

   p = Patcher('patch.maxpat', layout="matrix")
   # Chain 1
   metro1 = p.add_textbox('metro 250')
   osc1 = p.add_textbox('cycle~ 440')
   filter1 = p.add_textbox('lores~ 1000')
   # Chain 2
   metro2 = p.add_textbox('metro 333')
   osc2 = p.add_textbox('saw~ 220')
   # Shared output
   dac = p.add_textbox('ezdac~')

   p.add_line(metro1, osc1)
   p.add_line(osc1, filter1)
   p.add_line(metro2, osc2)
   p.add_line(filter1, dac)
   p.add_line(osc2, dac)
   p.optimize_layout()

   # Get signal chain analysis
   chain_info = p._layout_mgr.get_signal_chain_info()
   print(f"Detected {chain_info['num_chains']} signal chains")