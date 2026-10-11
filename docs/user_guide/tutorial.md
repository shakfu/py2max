# Tutorial

This tutorial will walk you through creating increasingly complex Max/MSP patches with py2max.

## Tutorial 1: Simple Synthesis

Let's create a basic synthesizer with multiple oscillators:

``` python
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
    gain = p.add_floatparam(f'gain{i}', initial=0.3)
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
master_vol = p.add_floatparam('master', initial=0.5)
master_mult = p.add_textbox('*~')
output = p.add_textbox('ezdac~')

p.add_line(mixer, master_mult)
p.add_line(master_vol, master_mult, outlet=0, inlet=1)
p.add_line(master_mult, output)

# Optimize layout
p.optimize_layout()
p.save()
```

## Tutorial 2: Signal Processing Chain

Create a complex audio processing chain:

``` python
from py2max import Patcher

# Use flow layout for signal processing
p = Patcher('fx-chain.maxpat', layout="flow", flow_direction="vertical")

# Input section
input_obj = p.add_textbox('adc~ 1 2')
input_gain = p.add_textbox('*~ 1.0')
p.add_line(input_obj, input_gain)

# Add input level control
input_level = p.add_floatparam('input_level', initial=1.0)
p.add_line(input_level, input_gain, outlet=0, inlet=1)

# EQ section: svf~ outlets are low-pass, high-pass, band-pass, notch
highpass = p.add_textbox('svf~ 100 0.5')
lowpass = p.add_textbox('svf~ 8000 0.5')

p.add_line(input_gain, highpass)
p.add_line(highpass, lowpass, outlet=1)  # high-pass output

# Distortion section
drive = p.add_floatparam('drive', initial=1.0)
drive_mult = p.add_textbox('*~')
overdrive = p.add_textbox('overdrive~')

p.add_line(lowpass, drive_mult)  # low-pass output
p.add_line(drive, drive_mult, outlet=0, inlet=1)
p.add_line(drive_mult, overdrive)

# Delay section: tapin~/tapout~, since a signal loop through delay~ is
# not allowed
delay_time = p.add_floatparam('delay_time', initial=250.0)
tapin = p.add_textbox('tapin~ 1000')
tapout = p.add_textbox('tapout~ 250')
delay_feedback = p.add_floatparam('feedback', initial=0.3)
feedback_mult = p.add_textbox('*~')

p.add_line(overdrive, tapin)
p.add_line(tapin, tapout)
p.add_line(delay_time, tapout)  # delay time in ms
p.add_line(tapout, feedback_mult)
p.add_line(delay_feedback, feedback_mult, outlet=0, inlet=1)
p.add_line(feedback_mult, tapin)  # feedback loop

# Wet/dry mix: wet * mix + dry * (1 - mix)
delay_mix = p.add_floatparam('delay_mix', initial=0.3)
dry_level = p.add_textbox('!- 1.')
wet_gain = p.add_textbox('*~')
dry_gain = p.add_textbox('*~')
wet_dry = p.add_textbox('+~')

p.add_line(tapout, wet_gain)
p.add_line(delay_mix, wet_gain, outlet=0, inlet=1)
p.add_line(delay_mix, dry_level)
p.add_line(overdrive, dry_gain)
p.add_line(dry_level, dry_gain, outlet=0, inlet=1)
p.add_line(wet_gain, wet_dry)
p.add_line(dry_gain, wet_dry, outlet=0, inlet=1)

# Output section
output_gain = p.add_textbox('*~')
output_level = p.add_floatparam('output_level', initial=0.7)
output = p.add_textbox('dac~ 1 2')

p.add_line(wet_dry, output_gain)
p.add_line(output_level, output_gain, outlet=0, inlet=1)
p.add_line(output_gain, output)
p.add_line(output_gain, output, outlet=0, inlet=1)

# Optimize layout for signal flow
p.optimize_layout()
p.save()
```

## Tutorial 3: Interactive Controller

Create an interactive MIDI controller interface:

``` python
from py2max import Patcher

# Create controller with automatic layout
p = Patcher('midi-controller.maxpat', layout="grid", cluster_connected=True)

# MIDI input
midi_in = p.add_textbox('ctlin')

# Create 8 controller channels
controllers = []
for cc_num in range(1, 9):  # CC 1-8
    # CC number selection
    cc_select = p.add_intparam(f'CC{cc_num}', initial=cc_num)

    # Route specific CC
    route = p.add_textbox(f'route {cc_num}')

    # Scale 0-127 to 0.0-1.0
    scale = p.add_textbox('/ 127.')

    # Value display
    value_display = p.add_floatparam(f'value{cc_num}', initial=0.0)

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
preset_slot = p.add_intparam('preset_slot', initial=1)
preset_store = p.add_message('store $1')
preset_recall = p.add_message('recall $1')
preset_obj = p.add_textbox('preset')

p.add_line(preset_slot, preset_store)
p.add_line(preset_slot, preset_recall)
p.add_line(preset_store, preset_obj)
p.add_line(preset_recall, preset_obj)

# preset's left outlet names the objects whose values it stores

for ctrl in controllers:

    p.add_line(preset_obj, ctrl['value'])

# Add comments for clarity
p.add_comment('MIDI Controller Interface', position='above')
p.add_comment('Controllers 1-8', position='above')
p.add_comment('Preset Management', position='above')

p.optimize_layout()
p.save()
```

## Tutorial 4: Generative Music System

Create a generative music system with multiple patterns:

``` python
from py2max import Patcher

p = Patcher('generative-music.maxpat', layout="flow", flow_direction="horizontal")

# Master clock
master_tempo = p.add_floatparam('tempo', initial=120.0)
metro = p.add_textbox('metro 500')

p.add_line(master_tempo, metro)

# Create 4 pattern generators
patterns = []
# MIDI note numbers (C4 = 60); a table holds ints
scales = [
    [60, 62, 64, 67, 69],      # Pentatonic: C D E G A
    [60, 62, 65, 67, 69, 72],  # Minor pentatonic: C D F G A C
    [60, 64, 65, 67, 71],      # Mysterious: C E F G B
    [60, 61, 65, 66, 68],      # Diminished: C Db F Gb Ab
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

    # Look up the note, then convert it to a frequency
    table_lookup = p.add_table(f'notes{i}', array=scale)
    to_freq = p.add_textbox('mtof')

    p.add_line(note_selector, table_lookup)
    p.add_line(table_lookup, to_freq)

    # Synthesizer voice
    osc = p.add_textbox('cycle~')
    env = p.add_textbox('adsr~ 10 100 0.3 500')
    voice_gain = p.add_textbox('*~')

    p.add_line(to_freq, osc)
    p.add_line(pattern_metro, env)  # Trigger envelope
    p.add_line(osc, voice_gain)
    p.add_line(env, voice_gain, outlet=0, inlet=1)

    # Voice level control
    voice_level = p.add_floatparam(f'voice{i}_level', initial=0.25)
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
reverb = p.add_textbox('comb~ 100 37 1. 0. 0.7')  # feedback comb, a reverb stand-in
master_gain = p.add_textbox('*~')
master_level = p.add_floatparam('master_level', initial=0.6)
output = p.add_textbox('ezdac~')

p.add_line(main_mixer, reverb)
p.add_line(reverb, master_gain)
p.add_line(master_level, master_gain, outlet=0, inlet=1)
p.add_line(master_gain, output)

# Add global controls: non-zero starts the metro, 0 stops it
start = p.add_message('1')
stop = p.add_message('0')
p.add_line(start, metro)
p.add_line(stop, metro)

p.optimize_layout()
p.save()
```

## Advanced Techniques

### Working with Subpatchers

``` python
# Create main patch
main = Patcher('main-patch.maxpat')

# Create subpatcher; Max needs the "p" prefix
voice = main.add_subpatcher('p voice-processor')
sub = voice.subpatcher

# Add objects to subpatcher; inlet/outlet carry signals too
sub_in = sub.add_textbox('inlet')
sub_filter = sub.add_textbox('lores~ 1000 0.5')
sub_out = sub.add_textbox('outlet')

sub.add_line(sub_in, sub_filter)
sub.add_line(sub_filter, sub_out)

# Use the subpatcher box in the main patch
osc = main.add_textbox('cycle~ 440')
output = main.add_textbox('dac~')

main.add_line(osc, voice)
main.add_line(voice, output)
```

### Working with Data

``` python
# Create patch with data containers
p = Patcher('data-patch.maxpat')

# Table of ints: MIDI notes of a C major arpeggio
# (audio wavetables belong in a buffer~; see the Advanced Usage guide)
table = p.add_table('arpeggio', array=[60, 64, 67, 72])

# Collection for sequences: index -> note, velocity, duration
sequence_data = {
    0: [60, 127, 500],
    1: [64, 100, 300],
    2: [67, 110, 400],
}
coll = p.add_coll('sequence', dictionary=sequence_data)

# Dictionary for complex data
dict_obj = p.add_dict('patch-data')
```

### Error Handling and Validation

``` python
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
```

This completes our tutorial series. You now have the knowledge to create complex, interactive Max/MSP patches using py2max!
