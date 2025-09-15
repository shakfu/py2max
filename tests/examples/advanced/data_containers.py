#!/usr/bin/env python3
"""
Advanced Usage: Data Containers
================================

Examples demonstrating tables, collections, and dictionaries.

This example is used in:
- docs/source/user_guide/advanced_usage.rst
"""

import math
from py2max import Patcher


def create_wavetable_synth():
    """Create a wavetable synthesizer with tables."""
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
    return p


def create_sequencer():
    """Create a sequencer using collections."""
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
    return p


def create_state_management():
    """Create patch state management using dictionaries."""
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

    p.save()
    return p


if __name__ == '__main__':
    # Create wavetable synth
    wavetable_patch = create_wavetable_synth()
    print(f"Created wavetable synth with {len(wavetable_patch._boxes)} objects")

    # Create sequencer
    sequencer_patch = create_sequencer()
    print(f"Created sequencer with {len(sequencer_patch._boxes)} objects")

    # Create state management
    state_patch = create_state_management()
    print(f"Created state management with {len(state_patch._boxes)} objects")