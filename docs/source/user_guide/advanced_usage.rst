Advanced Usage
==============

This guide covers advanced py2max features for power users and complex use cases.

Working with Subpatchers
-------------------------

Subpatchers allow you to create hierarchical patches with encapsulated functionality.

Creating Subpatchers
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from py2max import Patcher

   # Create main patch
   main = Patcher('main.maxpat')

   # Create subpatcher
   sub = main.add_subpatcher('voice')

   # Add objects to subpatcher
   inlet = sub.add_textbox('inlet~')
   filter_obj = sub.add_textbox('biquad~ 1000 0.707')
   env = sub.add_textbox('adsr~ 10 100 0.3 500')
   vca = sub.add_textbox('*~')
   outlet = sub.add_textbox('outlet~')

   # Connect subpatcher internals
   sub.add_line(inlet, filter_obj)
   sub.add_line(filter_obj, vca)
   sub.add_line(env, vca, outlet=0, inlet=1)
   sub.add_line(vca, outlet)

   # Use subpatcher in main patch
   osc = main.add_textbox('cycle~ 440')
   voice_instance = main.add_textbox('p voice')
   output = main.add_textbox('dac~')

   main.add_line(osc, voice_instance)
   main.add_line(voice_instance, output)

   main.save()

Nested Subpatchers
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Create deeply nested structure
   main = Patcher('complex.maxpat')

   # Level 1 subpatcher
   synth = main.add_subpatcher('synthesizer')

   # Level 2 subpatcher inside synth
   oscillator_bank = synth.add_subpatcher('oscillator-bank')

   # Add objects to nested subpatcher
   for i in range(4):
       osc = oscillator_bank.add_textbox(f'cycle~ {220 * (i + 1)}')
       out = oscillator_bank.add_textbox(f'outlet~ {i}')
       oscillator_bank.add_line(osc, out)

   # Use nested subpatchers
   bank_instance = synth.add_textbox('p oscillator-bank')
   mixer = synth.add_textbox('+~')
   synth_out = synth.add_textbox('outlet~')

   # Connect multiple outlets
   for i in range(4):
       synth.add_line(bank_instance, mixer, outlet=i, inlet=0)

   synth.add_line(mixer, synth_out)

Data Containers and Persistence
--------------------------------

Working with Tables
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import math

   p = Patcher('wavetable-synth.maxpat')

   # Create wavetable data
   wavetable_size = 512
   sine_data = [math.sin(2 * math.pi * i / wavetable_size) for i in range(wavetable_size)]
   saw_data = [2 * (i / wavetable_size) - 1 for i in range(wavetable_size)]

   # Create tables
   sine_table = p.add_table('sine_wave', data=sine_data)
   saw_table = p.add_table('saw_wave', data=saw_data)

   # Wavetable oscillator
   phasor = p.add_textbox('phasor~ 440')
   wave_select = p.add_floatbox(0.0, name='wave_morph')
   crossfade = p.add_textbox('crossfade~')

   # Table lookups
   sine_lookup = p.add_textbox('wave~ sine_wave')
   saw_lookup = p.add_textbox('wave~ saw_wave')

   # Connect wavetable synthesis
   p.add_line(phasor, sine_lookup)
   p.add_line(phasor, saw_lookup)
   p.add_line(sine_lookup, crossfade, outlet=0, inlet=0)
   p.add_line(saw_lookup, crossfade, outlet=0, inlet=1)
   p.add_line(wave_select, crossfade, outlet=0, inlet=2)

   p.save()

Collections for Sequences
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   p = Patcher('sequencer.maxpat')

   # Create sequence data
   melody_sequence = [
       "0, 60 100 250",   # note, velocity, duration
       "1, 64 90 250",
       "2, 67 110 500",
       "3, 60 80 250",
       "4, 69 100 750"
   ]

   rhythm_sequence = [
       "0, kick",
       "1, snare",
       "2, kick",
       "3, hihat",
       "4, kick"
   ]

   # Create collections
   melody_coll = p.add_coll('melody', data=melody_sequence)
   rhythm_coll = p.add_coll('rhythm', data=rhythm_sequence)

   # Sequence player
   metro = p.add_textbox('metro 500')
   counter = p.add_textbox('counter 0 4')

   # Melody player
   melody_lookup = p.add_textbox('coll melody')
   note_unpack = p.add_textbox('unpack i i i')
   mtof = p.add_textbox('mtof')
   osc = p.add_textbox('cycle~')

   # Rhythm player
   rhythm_lookup = p.add_textbox('coll rhythm')
   drum_select = p.add_textbox('select kick snare hihat')

   # Connect sequencer
   p.add_line(metro, counter)
   p.add_line(counter, melody_lookup)
   p.add_line(counter, rhythm_lookup)

   # Melody chain
   p.add_line(melody_lookup, note_unpack)
   p.add_line(note_unpack, mtof, outlet=0, inlet=0)
   p.add_line(mtof, osc)

   p.save()

Dictionaries for Complex Data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   p = Patcher('patch-state.maxpat')

   # Create state management system
   patch_dict = p.add_dict('patch_state')

   # State controls
   save_state = p.add_message('store current_state')
   load_state = p.add_message('recall current_state')

   # Connect to dictionary
   p.add_line(save_state, patch_dict)
   p.add_line(load_state, patch_dict)

   # Parameters to save
   params = ['frequency', 'amplitude', 'filter_freq', 'resonance']
   param_controls = {}

   for param in params:
       control = p.add_floatbox(0.5, name=param)
       param_controls[param] = control

       # Connect to state system
       p.add_line(patch_dict, control)
       p.add_line(control, patch_dict)

Advanced Connection Patterns
-----------------------------

Fan-out Connections
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   p = Patcher('fan-out.maxpat', layout="flow")

   source = p.add_textbox('cycle~ 440')

   # Connect one source to multiple destinations
   destinations = []
   for i in range(6):
       dest = p.add_textbox(f'biquad~ {200 + i * 300} 0.707')
       destinations.append(dest)

       # Fan out from source
       p.add_line(source, dest)

   # Collect all processed signals
   collector = p.add_textbox('+~')
   for dest in destinations:
       p.add_line(dest, collector)

   p.optimize_layout()
   p.save()

Feedback Loops
~~~~~~~~~~~~~~

.. code-block:: python

   p = Patcher('feedback-delay.maxpat')

   # Input
   input_obj = p.add_textbox('adc~')

   # Delay line with feedback
   delay = p.add_textbox('delay~ 500')
   feedback_gain = p.add_floatbox(0.3, name='feedback')
   feedback_mult = p.add_textbox('*~')
   input_mix = p.add_textbox('+~')

   # Create feedback loop
   p.add_line(input_obj, input_mix)
   p.add_line(input_mix, delay)
   p.add_line(delay, feedback_mult)
   p.add_line(feedback_gain, feedback_mult, outlet=0, inlet=1)
   p.add_line(feedback_mult, input_mix, outlet=0, inlet=1)  # Feedback

   # Output
   output = p.add_textbox('dac~')
   p.add_line(delay, output)

   p.save()

Matrix Routing
~~~~~~~~~~~~~~

.. code-block:: python

   p = Patcher('matrix-mixer.maxpat', layout="grid")

   # Create 4x4 matrix mixer
   sources = []
   destinations = []

   # Create sources
   for i in range(4):
       source = p.add_textbox(f'cycle~ {220 * (i + 1)}')
       sources.append(source)

   # Create destinations
   for i in range(4):
       dest = p.add_textbox(f'dac~ {i + 1}')
       destinations.append(dest)

   # Create matrix of gain controls
   matrix = {}
   for src_idx in range(4):
       for dst_idx in range(4):
           # Gain control
           gain = p.add_floatbox(0.0, name=f'gain_{src_idx}_{dst_idx}')
           mult = p.add_textbox('*~')

           # Store for routing
           matrix[(src_idx, dst_idx)] = {'gain': gain, 'mult': mult}

           # Connect source to multiplier
           p.add_line(sources[src_idx], mult)
           p.add_line(gain, mult, outlet=0, inlet=1)

   # Create summing for each destination
   for dst_idx in range(4):
       summer = p.add_textbox('+~')

       # Sum all sources for this destination
       for src_idx in range(4):
           p.add_line(matrix[(src_idx, dst_idx)]['mult'], summer)

       # Connect to destination
       p.add_line(summer, destinations[dst_idx])

   p.optimize_layout()
   p.save()

Error Handling and Robustness
------------------------------

Comprehensive Error Handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from py2max import Patcher, InvalidConnectionError
   import logging

   # Set up logging
   logging.basicConfig(level=logging.INFO)
   logger = logging.getLogger(__name__)

   def create_robust_patch(filename):
       try:
           p = Patcher(filename, validate_connections=True)

           # Track objects for cleanup on error
           created_objects = []

           try:
               # Create objects with error checking
               osc = p.add_textbox('cycle~ 440')
               created_objects.append(osc)

               gain = p.add_textbox('gain~')
               created_objects.append(gain)

               output = p.add_textbox('ezdac~')
               created_objects.append(output)

               # Attempt connections with validation
               p.add_line(osc, gain)
               logger.info("Connected oscillator to gain")

               p.add_line(gain, output)
               logger.info("Connected gain to output")

               # Validate object capabilities
               logger.info(f"Oscillator outlets: {osc.get_outlet_count()}")
               logger.info(f"Gain inlets: {gain.get_inlet_count()}")

               p.save()
               logger.info(f"Successfully created patch: {filename}")
               return p

           except InvalidConnectionError as e:
               logger.error(f"Connection error: {e}")
               # Could implement recovery logic here
               raise

           except Exception as e:
               logger.error(f"Unexpected error creating objects: {e}")
               # Cleanup logic could go here
               raise

       except Exception as e:
           logger.error(f"Failed to create patch {filename}: {e}")
           return None

   # Use robust patch creation
   patch = create_robust_patch('robust-patch.maxpat')

Validation and Testing
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def validate_patch_structure(patcher):
       """Validate patch structure and connections."""
       errors = []
       warnings = []

       # Check for disconnected objects
       connected_objects = set()
       for line in patcher._lines:
           connected_objects.add(line.src)
           connected_objects.add(line.dst)

       all_objects = set(obj.id for obj in patcher._boxes if obj.id)
       disconnected = all_objects - connected_objects

       if disconnected:
           warnings.append(f"Disconnected objects: {disconnected}")

       # Check for impossible connections
       for line in patcher._lines:
           try:
               src_obj = patcher._objects[line.src]
               dst_obj = patcher._objects[line.dst]

               src_outlets = src_obj.get_outlet_count()
               dst_inlets = dst_obj.get_inlet_count()

               if hasattr(line, 'outlet') and line.outlet >= src_outlets:
                   errors.append(f"Invalid outlet {line.outlet} on {src_obj.maxclass}")

               if hasattr(line, 'inlet') and line.inlet >= dst_inlets:
                   errors.append(f"Invalid inlet {line.inlet} on {dst_obj.maxclass}")

           except Exception as e:
               errors.append(f"Error validating connection: {e}")

       return errors, warnings

   # Use validation
   errors, warnings = validate_patch_structure(p)
   if errors:
       print(f"Patch errors: {errors}")
   if warnings:
       print(f"Patch warnings: {warnings}")

Performance Optimization
-------------------------

Large Patch Optimization
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def create_large_patch_efficiently():
       """Create large patches with performance optimizations."""

       # Disable clustering for large patches if speed is critical
       p = Patcher('large-patch.maxpat',
                  layout="grid",
                  cluster_connected=False,  # Faster for 100+ objects
                  validate_connections=False)  # Skip validation for speed

       # Batch object creation
       objects = []
       for i in range(200):
           obj = p.add_textbox(f'cycle~ {220 + i}')
           objects.append(obj)

       # Batch connection creation
       for i in range(0, len(objects) - 1, 2):
           p.add_line(objects[i], objects[i + 1])

       # Single layout optimization at the end
       p.optimize_layout()

       return p

Memory Management
~~~~~~~~~~~~~~~~~

.. code-block:: python

   def process_many_patches(patch_configs):
       """Process multiple patches with memory management."""

       for config in patch_configs:
           # Create patch
           p = Patcher(config['filename'])

           # Add objects based on config
           for obj_config in config['objects']:
               p.add_textbox(obj_config['text'])

           # Process and save
           p.optimize_layout()
           p.save()

           # Explicit cleanup for large numbers of patches
           del p

Custom Extensions
-----------------

Custom Object Creation
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class CustomPatcher(Patcher):
       """Extended patcher with custom object creation methods."""

       def add_lowpass_filter(self, frequency=1000, resonance=0.707):
           """Add a lowpass filter with controls."""
           freq_ctrl = self.add_floatbox(frequency, name=f'freq_{len(self._boxes)}')
           res_ctrl = self.add_floatbox(resonance, name=f'res_{len(self._boxes)}')
           filter_obj = self.add_textbox('biquad~ lowpass')

           # Connect controls
           self.add_line(freq_ctrl, filter_obj, outlet=0, inlet=1)
           self.add_line(res_ctrl, filter_obj, outlet=0, inlet=2)

           return filter_obj, freq_ctrl, res_ctrl

       def add_envelope_generator(self, attack=10, decay=100, sustain=0.3, release=500):
           """Add an ADSR envelope with controls."""
           a_ctrl = self.add_floatbox(attack, name=f'attack_{len(self._boxes)}')
           d_ctrl = self.add_floatbox(decay, name=f'decay_{len(self._boxes)}')
           s_ctrl = self.add_floatbox(sustain, name=f'sustain_{len(self._boxes)}')
           r_ctrl = self.add_floatbox(release, name=f'release_{len(self._boxes)}')

           env = self.add_textbox('adsr~')

           # Connect controls
           self.add_line(a_ctrl, env, outlet=0, inlet=1)
           self.add_line(d_ctrl, env, outlet=0, inlet=2)
           self.add_line(s_ctrl, env, outlet=0, inlet=3)
           self.add_line(r_ctrl, env, outlet=0, inlet=4)

           return env, (a_ctrl, d_ctrl, s_ctrl, r_ctrl)

   # Use custom patcher
   p = CustomPatcher('custom-synth.maxpat')

   osc = p.add_textbox('cycle~ 440')
   filter_obj, freq_ctrl, res_ctrl = p.add_lowpass_filter(2000, 0.5)
   env, env_ctrls = p.add_envelope_generator(5, 50, 0.7, 200)

   p.add_line(osc, filter_obj)
   p.add_line(env, filter_obj, outlet=0, inlet=3)  # Envelope to filter

   p.save()

This covers the advanced features of py2max for sophisticated patch creation and management.