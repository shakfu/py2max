Tutorial
========

This tutorial will walk you through creating increasingly complex Max/MSP patches with py2max.

Tutorial 1: Simple Synthesis
-----------------------------

Let's create a basic synthesizer with multiple oscillators:

.. code-block:: python

   from py2max import Patcher
   from py2max.utils import pitch2freq

   # Create patcher with grid layout
   p = Patcher('synthesizer.maxpat', layout="grid", flow_direction="horizontal")

   # Create oscillators for a C major chord
   freqs = [pitch2freq("C4"), pitch2freq("E4"), pitch2freq("G4")]
   oscillators = []

   for i, freq in enumerate(freqs):
       osc = p.add_textbox(f'cycle~ {freq:.2f}')
       oscillators.append(osc)

   # Add gain controls
   gains = []
   for i in range(3):
       gain = p.add_floatbox(0.3, name=f'gain{i}')
       gains.append(gain)
       gain_mult = p.add_textbox('*~')

       # Connect oscillator to gain
       p.add_line(oscillators[i], gain_mult)
       p.add_line(gain, gain_mult, outlet=0, inlet=1)

   # Mix the signals
   mixer = p.add_textbox('+~')
   for gain_mult in gains:
       # Get the *~ objects (every other object after gains)
       mult_obj = p._boxes[p._boxes.index(gain_mult) + 1]
       p.add_line(mult_obj, mixer)

   # Add master volume and output
   master_vol = p.add_floatbox(0.5, name='master')
   master_mult = p.add_textbox('*~')
   output = p.add_textbox('ezdac~')

   p.add_line(mixer, master_mult)
   p.add_line(master_vol, master_mult, outlet=0, inlet=1)
   p.add_line(master_mult, output)

   # Optimize layout
   p.optimize_layout()
   p.save()

Tutorial 2: Signal Processing Chain
------------------------------------

Create a complex audio processing chain:

.. code-block:: python

   from py2max import Patcher

   # Use flow layout for signal processing
   p = Patcher('fx-chain.maxpat', layout="flow", flow_direction="vertical")

   # Input section
   input_obj = p.add_textbox('adc~ 1 2')
   input_gain = p.add_textbox('*~ 1.0')
   p.add_line(input_obj, input_gain)

   # Add input level control
   input_level = p.add_floatbox(1.0, name='input_level')
   p.add_line(input_level, input_gain, outlet=0, inlet=1)

   # EQ section
   highpass = p.add_textbox('biquad~ 100. 0.707 highpass')
   lowpass = p.add_textbox('biquad~ 8000. 0.707 lowpass')

   p.add_line(input_gain, highpass)
   p.add_line(highpass, lowpass)

   # Distortion section
   drive = p.add_floatbox(1.0, name='drive')
   drive_mult = p.add_textbox('*~')
   overdrive = p.add_textbox('overdrive~')

   p.add_line(lowpass, drive_mult)
   p.add_line(drive, drive_mult, outlet=0, inlet=1)
   p.add_line(drive_mult, overdrive)

   # Delay section
   delay_time = p.add_floatbox(250.0, name='delay_time')
   delay = p.add_textbox('delay~')
   delay_feedback = p.add_floatbox(0.3, name='feedback')
   feedback_mult = p.add_textbox('*~')
   delay_mix = p.add_floatbox(0.3, name='delay_mix')
   wet_dry = p.add_textbox('crossfade~')

   # Delay connections
   p.add_line(delay_time, delay)
   p.add_line(overdrive, delay)
   p.add_line(delay, feedback_mult)
   p.add_line(delay_feedback, feedback_mult, outlet=0, inlet=1)
   p.add_line(feedback_mult, delay, outlet=0, inlet=1)  # feedback loop

   # Wet/dry mix
   p.add_line(overdrive, wet_dry, outlet=0, inlet=0)  # dry signal
   p.add_line(delay, wet_dry, outlet=0, inlet=1)      # wet signal
   p.add_line(delay_mix, wet_dry, outlet=0, inlet=2)  # mix control

   # Output section
   output_gain = p.add_textbox('*~')
   output_level = p.add_floatbox(0.7, name='output_level')
   output = p.add_textbox('dac~ 1 2')

   p.add_line(wet_dry, output_gain)
   p.add_line(output_level, output_gain, outlet=0, inlet=1)
   p.add_line(output_gain, output)

   # Optimize layout for signal flow
   p.optimize_layout()
   p.save()

Tutorial 3: Interactive Controller
-----------------------------------

Create an interactive MIDI controller interface:

.. code-block:: python

   from py2max import Patcher

   # Create controller with automatic layout
   p = Patcher('midi-controller.maxpat', layout="grid", cluster_connected=True)

   # MIDI input
   midi_in = p.add_textbox('ctlin')

   # Create 8 controller channels
   controllers = []
   for cc_num in range(1, 9):  # CC 1-8
       # CC number selection
       cc_select = p.add_intbox(cc_num, name=f'CC{cc_num}')

       # Route specific CC
       route = p.add_textbox(f'route {cc_num}')

       # Scale 0-127 to 0.0-1.0
       scale = p.add_textbox('/ 127.')

       # Value display
       value_display = p.add_floatbox(0.0, name=f'value{cc_num}')

       # Connect chain
       p.add_line(midi_in, route)
       p.add_line(route, scale)
       p.add_line(scale, value_display)

       controllers.append({
           'cc': cc_select,
           'route': route,
           'scale': scale,
           'value': value_display
       })

   # Add preset management
   preset_slot = p.add_intbox(1, name='preset_slot')
   preset_store = p.add_message('store $1')
   preset_recall = p.add_message('recall $1')
   preset_obj = p.add_textbox('preset')

   p.add_line(preset_slot, preset_store)
   p.add_line(preset_slot, preset_recall)
   p.add_line(preset_store, preset_obj)
   p.add_line(preset_recall, preset_obj)

   # Connect all value displays to preset system
   for i, ctrl in enumerate(controllers):
       p.add_line(preset_obj, ctrl['value'], outlet=i, inlet=0)
       p.add_line(ctrl['value'], preset_obj, outlet=0, inlet=i)

   # Add comments for clarity
   p.add_comment('MIDI Controller Interface', position='above')
   p.add_comment('Controllers 1-8', position='above')
   p.add_comment('Preset Management', position='above')

   p.optimize_layout()
   p.save()

Tutorial 4: Generative Music System
------------------------------------

Create a generative music system with multiple patterns:

.. code-block:: python

   from py2max import Patcher
   from py2max.utils import pitch2freq
   import random

   p = Patcher('generative-music.maxpat', layout="flow", flow_direction="horizontal")

   # Master clock
   master_tempo = p.add_floatbox(120.0, name='tempo')
   metro = p.add_textbox('metro 500')

   p.add_line(master_tempo, metro)

   # Create 4 pattern generators
   patterns = []
   scales = [
       ["C4", "D4", "E4", "G4", "A4"],      # Pentatonic
       ["C4", "D4", "F4", "G4", "A4", "C5"], # Minor pentatonic
       ["C4", "E4", "F4", "G4", "B4"],       # Mysterious
       ["C4", "Db4", "F4", "Gb4", "Ab4"]     # Diminished
   ]

   for i, scale in enumerate(scales):
       # Pattern trigger
       pattern_div = p.add_textbox(f'/ {2**(i+1)}')  # Different divisions
       pattern_metro = p.add_textbox('metro')

       p.add_line(metro, pattern_div)
       p.add_line(pattern_div, pattern_metro)

       # Note selection
       note_selector = p.add_textbox(f'random {len(scale)}')
       p.add_line(pattern_metro, note_selector)

       # Convert to frequencies
       freq_table = p.add_table(f'freqs{i}', data=[pitch2freq(note) for note in scale])
       table_lookup = p.add_textbox(f'table freqs{i}')

       p.add_line(note_selector, table_lookup)

       # Synthesizer voice
       osc = p.add_textbox('cycle~')
       env = p.add_textbox('adsr~ 10 100 0.3 500')
       voice_gain = p.add_textbox('*~')

       p.add_line(table_lookup, osc)
       p.add_line(pattern_metro, env)  # Trigger envelope
       p.add_line(osc, voice_gain)
       p.add_line(env, voice_gain, outlet=0, inlet=1)

       # Voice level control
       voice_level = p.add_floatbox(0.25, name=f'voice{i}_level')
       voice_mult = p.add_textbox('*~')

       p.add_line(voice_gain, voice_mult)
       p.add_line(voice_level, voice_mult, outlet=0, inlet=1)

       patterns.append({
           'voice': voice_mult,
           'level': voice_level,
           'tempo_div': pattern_div
       })

   # Mix all voices
   main_mixer = p.add_textbox('+~')
   for pattern in patterns:
       p.add_line(pattern['voice'], main_mixer)

   # Global effects
   reverb = p.add_textbox('freeverb~ 0.8 0.5')
   master_gain = p.add_textbox('*~')
   master_level = p.add_floatbox(0.6, name='master_level')
   output = p.add_textbox('ezdac~')

   p.add_line(main_mixer, reverb)
   p.add_line(reverb, master_gain)
   p.add_line(master_level, master_gain, outlet=0, inlet=1)
   p.add_line(master_gain, output)

   # Add global controls
   start_stop = p.add_message('start', 'stop')
   p.add_line(start_stop, metro)

   p.optimize_layout()
   p.save()

Advanced Techniques
-------------------

Working with Subpatchers
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Create main patch
   main = Patcher('main-patch.maxpat')

   # Create subpatcher
   sub = main.add_subpatcher('voice-processor')

   # Add objects to subpatcher
   sub_in = sub.add_textbox('inlet~')
   sub_filter = sub.add_textbox('biquad~')
   sub_out = sub.add_textbox('outlet~')

   sub.add_line(sub_in, sub_filter)
   sub.add_line(sub_filter, sub_out)

   # Use subpatcher in main patch
   osc = main.add_textbox('cycle~ 440')
   sub_instance = main.add_textbox('p voice-processor')
   output = main.add_textbox('dac~')

   main.add_line(osc, sub_instance)
   main.add_line(sub_instance, output)

Working with Data
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Create patch with data containers
   p = Patcher('data-patch.maxpat')

   # Table for wavetable synthesis
   wavetable_data = [math.sin(2 * math.pi * i / 512) for i in range(512)]
   wavetable = p.add_table('wavetable', data=wavetable_data)

   # Collection for sequences
   sequence_data = [
       "0, 60 127 500",
       "1, 64 100 300",
       "2, 67 110 400"
   ]
   coll = p.add_coll('sequence', data=sequence_data)

   # Dictionary for complex data
   dict_obj = p.add_dict('patch-data')

Error Handling and Validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from py2max import Patcher, InvalidConnectionError

   p = Patcher('safe-patch.maxpat', validate_connections=True)

   try:
       osc = p.add_textbox('cycle~ 440')
       gain = p.add_textbox('gain~')

       # This connection is valid
       p.add_line(osc, gain)

       # This would raise an error
       p.add_line(osc, gain, outlet=10)  # cycle~ doesn't have outlet 10

   except InvalidConnectionError as e:
       print(f"Connection error: {e}")
       # Handle error gracefully

   # Check object capabilities
   print(f"Oscillator outlets: {osc.get_outlet_count()}")
   print(f"Gain inlets: {gain.get_inlet_count()}")

This completes our tutorial series. You now have the knowledge to create complex, interactive Max/MSP patches using py2max!