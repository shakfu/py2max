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
* :class:`py2max.MaxRefDB` - SQLite database for Max object reference data

Exceptions
----------

The package provides a hierarchy of exceptions for error handling:

* :class:`py2max.Py2MaxError` - Base exception for all py2max errors
* :class:`py2max.InvalidConnectionError` - Exception for invalid patchline connections
* :class:`py2max.InvalidObjectError` - Exception for invalid object configuration
* :class:`py2max.InvalidPatchError` - Exception for invalid patcher state
* :class:`py2max.PatcherIOError` - Exception for file I/O errors
* :class:`py2max.MaxRefError` - Exception for MaxRef XML parsing errors
* :class:`py2max.LayoutError` - Exception for layout manager errors
* :class:`py2max.DatabaseError` - Exception for database errors

Example Usage
-------------

.. code-block:: python

   from py2max import Patcher

   # Create a new patcher
   patch = Patcher('example.maxpat')

   # Add some objects
   osc = patch.add_textbox('cycle~ 440')
   gain = patch.add_textbox('gain~ 0.5')
   output = patch.add_textbox('ezdac~')

   # Connect them
   patch.add_line(osc, gain)
   patch.add_line(gain, output)

   # Export to SVG for preview
   patch.to_svg('example.svg')

   # Save the patch
   patch.save()

Using MaxRefDB
--------------

.. code-block:: python

   from py2max import MaxRefDB

   # Use default cache (auto-populated on first use)
   db = MaxRefDB()

   # Query objects
   if 'cycle~' in db:
       cycle_info = db['cycle~']
       print(cycle_info['digest'])

   # Search for objects
   results = db.search('filter')

   # Get objects by category
   msp_objects = db.by_category('MSP')

For more detailed examples, see the :doc:`../user_guide/tutorial`.