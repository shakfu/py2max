#!/usr/bin/env python3
"""
Advanced Usage: Data Containers
================================

Examples demonstrating tables, collections, and dictionaries.

This example is used in:
- docs/user_guide/advanced_usage.md
"""

import math
from py2max import Patcher


def create_wavetable_synth():
    """Create a wavetable synthesizer with tables."""
    p = Patcher("wavetable-synth.maxpat")

    # Create wavetable data
    wavetable_size = 512
    sine_data = [
        math.sin(2 * math.pi * i / wavetable_size) for i in range(wavetable_size)
    ]
    saw_data = [2 * (i / wavetable_size) - 1 for i in range(wavetable_size)]

    # Create tables
    p.add_table("sine_wave", data=sine_data)
    p.add_table("saw_wave", data=saw_data)

    # Wavetable oscillator
    phasor = p.add_textbox("phasor~ 440")
    wave_select = p.add_floatparam("wave_morph", initial=0.0)
    crossfade = p.add_textbox("crossfade~")

    # Table lookups
    sine_lookup = p.add_textbox("wave~ sine_wave")
    saw_lookup = p.add_textbox("wave~ saw_wave")

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
    p = Patcher("sequencer.maxpat")

    # Create sequence data
    melody_sequence = [
        "0, 60 100 250",  # note, velocity, duration
        "1, 64 90 250",
        "2, 67 110 500",
        "3, 60 80 250",
        "4, 69 100 750",
    ]

    rhythm_sequence = ["0, kick", "1, snare", "2, kick", "3, hihat", "4, kick"]

    # Create collections
    p.add_coll("melody", data=melody_sequence)
    p.add_coll("rhythm", data=rhythm_sequence)

    # Sequence player
    metro = p.add_textbox("metro 500")
    counter = p.add_textbox("counter 0 4")

    # Melody player
    melody_lookup = p.add_textbox("coll melody")
    note_unpack = p.add_textbox("unpack i i i")
    mtof = p.add_textbox("mtof")
    osc = p.add_textbox("cycle~")

    # Rhythm player
    rhythm_lookup = p.add_textbox("coll rhythm")
    p.add_textbox("select kick snare hihat")

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
    p = Patcher("patch-state.maxpat")

    params = ["frequency", "amplitude", "filter_freq", "resonance"]
    patch_dict = p.add_dict("patch_state")

    # Save and load the dictionary as JSON
    p.add_line(p.add_message("export patch_state.json"), patch_dict)
    p.add_line(p.add_message("import patch_state.json"), patch_dict)

    # Recall: `get key` answers "key value" from outlet 1; route splits by key
    recall = p.add_message(", ".join(f"get {param}" for param in params))
    p.add_line(recall, patch_dict)
    router = p.add_textbox("route " + " ".join(params))
    p.add_line(patch_dict, router, outlet=1)

    for i, param in enumerate(params):
        control = p.add_floatparam(param, initial=0.5)
        # Store: "set key value" writes the control's value into the dict
        store = p.add_textbox(f"prepend set {param}")
        p.add_line(control, store)
        p.add_line(store, patch_dict)
        # "set" updates the control without sending the value back
        update = p.add_textbox("prepend set")
        p.add_line(router, update, outlet=i)
        p.add_line(update, control)

    p.save()
    return p


if __name__ == "__main__":
    # Create wavetable synth
    wavetable_patch = create_wavetable_synth()
    print(f"Created wavetable synth with {len(wavetable_patch._boxes)} objects")

    # Create sequencer
    sequencer_patch = create_sequencer()
    print(f"Created sequencer with {len(sequencer_patch._boxes)} objects")

    # Create state management
    state_patch = create_state_management()
    print(f"Created state management with {len(state_patch._boxes)} objects")
