py2max Package
==============

.. automodule:: py2max
   :members:
   :undoc-members:
   :show-inheritance:

The main py2max package provides the core classes for creating Max/MSP patcher files.

Main Classes
------------

The package exports the following main classes:

* :class:`py2max.Patcher` - Main class for creating and manipulating Max patches
* :class:`py2max.Box` - Represents individual Max objects in a patch
* :class:`py2max.Patchline` - Represents connections between Max objects
* :class:`py2max.InvalidConnectionError` - Exception for invalid object connections

Example Usage
-------------

.. code-block:: python

   from py2max import Patcher, Box, Patchline

   # Create a new patcher
   patch = Patcher('example.maxpat')

   # Add some objects
   osc = patch.add_textbox('cycle~ 440')
   gain = patch.add_textbox('gain~ 0.5')
   output = patch.add_textbox('ezdac~')

   # Connect them
   patch.add_line(osc, gain)
   patch.add_line(gain, output)

   # Save the patch
   patch.save()

For more detailed examples, see the :doc:`../user_guide/tutorial`.