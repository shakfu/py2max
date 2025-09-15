Quick Start Guide
=================

This guide will get you up and running with py2max in just a few minutes.

Your First Patch
-----------------

Let's create a simple oscillator patch:

.. code-block:: python

   from py2max import Patcher

   # Create a new patcher
   p = Patcher('my-first-patch.maxpat')

   # Add a sine wave oscillator
   osc = p.add_textbox('cycle~ 440')

   # Add a gain control
   gain = p.add_textbox('gain~ 0.5')

   # Add audio output
   dac = p.add_textbox('ezdac~')

   # Connect the objects
   p.add_line(osc, gain)    # oscillator -> gain
   p.add_line(gain, dac)    # gain -> output

   # Save the patch
   p.save()

This creates a .maxpat file that you can open in Max/MSP!

Understanding the Basics
-------------------------

Patcher
~~~~~~~

The :class:`~py2max.Patcher` is the main container for your Max patch. It handles:

* Adding Max objects
* Managing connections between objects
* Layout and positioning
* Saving and loading patches

.. code-block:: python

   # Create with automatic layout
   p = Patcher('patch.maxpat', layout="grid")

   # Create with flow-based layout
   p = Patcher('patch.maxpat', layout="flow")

Adding Objects
~~~~~~~~~~~~~~

py2max provides several methods for adding Max objects:

.. code-block:: python

   # Generic text-based objects
   osc = p.add_textbox('cycle~ 440')
   filter = p.add_textbox('biquad~')

   # Specialized UI objects
   button = p.add_message('bang')
   comment = p.add_comment('This is a comment')
   number = p.add_floatbox(440.0)

   # Container objects
   table = p.add_table('wavetable')
   coll = p.add_coll('sequence-data')

Making Connections
~~~~~~~~~~~~~~~~~~

Connect objects using the :meth:`~py2max.Patcher.add_line` method:

.. code-block:: python

   # Simple connection (outlet 0 to inlet 0)
   p.add_line(osc, gain)

   # Specify outlet and inlet indices
   p.add_line(osc, filter, outlet=0, inlet=1)

   # Multiple connections from one object
   p.add_line(osc, gain)
   p.add_line(osc, filter)  # Send same signal to both

Working with Layout
-------------------

py2max provides intelligent layout managers:

Grid Layout
~~~~~~~~~~~

.. code-block:: python

   # Horizontal grid with automatic clustering
   p = Patcher('patch.maxpat', layout="grid", flow_direction="horizontal")

   # Add several objects
   objects = []
   for i in range(5):
       obj = p.add_textbox(f'cycle~ {440 + i * 110}')
       objects.append(obj)

   # Connect them in sequence
   for i in range(len(objects) - 1):
       p.add_line(objects[i], objects[i + 1])

   # Optimize layout to cluster connected objects
   p.optimize_layout()

Flow Layout
~~~~~~~~~~~

.. code-block:: python

   # Signal flow-based layout
   p = Patcher('patch.maxpat', layout="flow", flow_direction="vertical")

   # Create a signal processing chain
   input_obj = p.add_textbox('adc~')
   eq = p.add_textbox('filtergraph~')
   delay = p.add_textbox('delay~ 500')
   reverb = p.add_textbox('freeverb~')
   output = p.add_textbox('dac~')

   # Connect in signal flow order
   p.add_line(input_obj, eq)
   p.add_line(eq, delay)
   p.add_line(delay, reverb)
   p.add_line(reverb, output)

   # Layout will arrange objects hierarchically
   p.optimize_layout()

Getting Object Help
--------------------

py2max provides rich documentation for Max objects:

.. code-block:: python

   # Add an object
   umenu = p.add_textbox('umenu')

   # Get formatted help
   print(umenu.help())

   # Get detailed object information
   info = umenu.get_info()
   print(f"Methods: {len(info['methods'])}")
   print(f"Attributes: {len(info['attributes'])}")
   print(f"Inlets: {umenu.get_inlet_count()}")
   print(f"Outlets: {umenu.get_outlet_count()}")

Connection Validation
---------------------

py2max can validate connections to prevent errors:

.. code-block:: python

   from py2max import InvalidConnectionError

   # Enable validation (default)
   p = Patcher('patch.maxpat', validate_connections=True)

   osc = p.add_textbox('cycle~ 440')
   gain = p.add_textbox('gain~')

   # Valid connection
   p.add_line(osc, gain)

   # This would raise an error (cycle~ only has 1 outlet)
   try:
       p.add_line(osc, gain, outlet=5)
   except InvalidConnectionError as e:
       print(f"Invalid connection: {e}")

Loading Existing Patches
-------------------------

You can load and modify existing .maxpat files:

.. code-block:: python

   # Load an existing patch
   p = Patcher.from_file('existing-patch.maxpat')

   # Add new objects
   new_obj = p.add_textbox('delay~ 1000')

   # Save with a new name
   p._path = 'modified-patch.maxpat'
   p.save()

Next Steps
----------

* Read the :doc:`tutorial` for more detailed examples
* Explore :doc:`layout_managers` for advanced positioning
* Check the :doc:`../api/py2max` for complete API reference
* See :doc:`advanced_usage` for complex scenarios