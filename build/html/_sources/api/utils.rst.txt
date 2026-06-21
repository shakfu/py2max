py2max.utils Module
===================

.. automodule:: py2max.utils
   :members:
   :undoc-members:
   :show-inheritance:

The utils module contains utility functions for common operations in music and audio programming.

The main utility is the **pitch2freq** function which converts musical pitch notation to frequency values, useful for generating oscillator frequencies and musical calculations.

Usage Examples
--------------

Pitch to Frequency Conversion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from py2max.utils import pitch2freq

   # Convert various pitches to frequencies
   c3_freq = pitch2freq("C3")  # 130.81 Hz
   a4_freq = pitch2freq("A4")  # 440.0 Hz (concert pitch)
   c5_freq = pitch2freq("C5")  # 523.25 Hz

   print(f"C3: {c3_freq:.2f} Hz")
   print(f"A4: {a4_freq:.2f} Hz")
   print(f"C5: {c5_freq:.2f} Hz")

   # Use with different tuning
   a4_442 = pitch2freq("A4", A4=442)  # 442 Hz tuning
   print(f"A4 at 442 Hz tuning: {a4_442:.2f} Hz")

Integration with Patcher Creation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from py2max import Patcher
   from py2max.utils import pitch2freq

   # Create a patch with musically tuned oscillators
   p = Patcher('musical-patch.maxpat')

   # Create oscillators for a C major chord
   c_freq = pitch2freq("C4")
   e_freq = pitch2freq("E4")
   g_freq = pitch2freq("G4")

   osc_c = p.add_textbox(f'cycle~ {c_freq:.2f}')
   osc_e = p.add_textbox(f'cycle~ {e_freq:.2f}')
   osc_g = p.add_textbox(f'cycle~ {g_freq:.2f}')

   # Mix and output
   mixer = p.add_textbox('*~ 0.3')
   output = p.add_textbox('ezdac~')

   # Connect all oscillators to mixer
   p.add_line(osc_c, mixer)
   p.add_line(osc_e, mixer)
   p.add_line(osc_g, mixer)
   p.add_line(mixer, output)

   p.save()

Supported Pitch Notation
~~~~~~~~~~~~~~~~~~~~~~~~~

The pitch2freq function supports standard pitch notation:

* **Note names**: A, Bb, B, C, Db, D, Eb, E, F, Gb, G, Ab

* **Octave numbers**: Any integer (typically 0-9)

* **Examples**: "C3", "Bb4", "F#5" (use "Gb5" instead of "F#5")

.. code-block:: python

   # Various pitch examples
   pitches = ["C0", "A1", "Bb2", "C3", "Db4", "E4", "Gb5", "A6", "C7"]

   for pitch in pitches:
       freq = pitch2freq(pitch)
       print(f"{pitch}: {freq:.2f} Hz")