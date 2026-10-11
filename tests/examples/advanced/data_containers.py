#!/usr/bin/env python3
"""
Advanced Usage: Data Containers
================================

Examples demonstrating buffers, tables, collections, and dictionaries.

This example is used in:
- docs/user_guide/advanced_usage.md
"""

import math
import struct
import wave
from pathlib import Path

from py2max import Patcher


def write_wavetable(path, samples, rate=44100):
    """Write ``samples`` (floats in -1..1) as a mono 16-bit WAV file."""
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(rate)
        f.writeframes(b"".join(struct.pack("<h", round(x * 32767)) for x in samples))


def create_wavetable_synth():
    """Create a wavetable synthesizer that plays a scale."""
    path = Path("wavetable-synth.maxpat")
    p = Patcher(path)

    # Wavetables: a buffer~ holds audio, so write each one as a WAV file
    # beside the patch; buffer~ loads it when the patch opens.
    size = 512
    sine = [math.sin(2 * math.pi * i / size) for i in range(size)]
    saw = [2 * (i / size) - 1 for i in range(size)]
    for name, samples in (("sine_wave", sine), ("saw_wave", saw)):
        write_wavetable(path.with_name(f"{name}.wav"), samples)
        p.add_textbox(f"buffer~ {name} {name}.wav")

    # A table holds ints: semitone offsets of a major scale, read by index
    scale = p.add_table("scale", array=[0, 2, 4, 5, 7, 9, 11, 12])

    # Step through the scale
    metro = p.add_textbox("metro 250")
    step = p.add_textbox("counter 0 7")
    root = p.add_textbox("+ 60")
    mtof = p.add_textbox("mtof")
    p.add_line(metro, step)
    p.add_line(step, scale)
    p.add_line(scale, root)
    p.add_line(root, mtof)

    # Wavetable oscillator: phasor~ ramps 0-1 through each wave~ table
    phasor = p.add_textbox("phasor~ 440")
    sine_lookup = p.add_textbox("wave~ sine_wave")
    saw_lookup = p.add_textbox("wave~ saw_wave")
    p.add_line(mtof, phasor)
    p.add_line(phasor, sine_lookup)
    p.add_line(phasor, saw_lookup)

    # selector~ 2: an int picks input 1 or 2 (0 is off)
    wave_select = p.add_intparam("wave_select", initial=1)
    selector = p.add_textbox("selector~ 2 1")
    p.add_line(wave_select, selector)
    p.add_line(sine_lookup, selector, outlet=0, inlet=1)
    p.add_line(saw_lookup, selector, outlet=0, inlet=2)

    # Output
    level = p.add_textbox("*~ 0.2")
    dac = p.add_textbox("ezdac~")
    p.add_line(selector, level)
    p.add_line(level, dac)
    p.add_line(level, dac, inlet=1)

    p.save()
    return p


def create_sequencer():
    """Create a sequencer using collections."""
    p = Patcher("sequencer.maxpat")

    # Create sequence data: index -> value
    melody_sequence = {
        0: [60, 100, 250],  # note, velocity, duration
        1: [64, 90, 250],
        2: [67, 110, 500],
        3: [60, 80, 250],
        4: [69, 100, 750],
    }

    rhythm_sequence = {0: "kick", 1: "snare", 2: "kick", 3: "hihat", 4: "kick"}

    # Create collections; an int in the left inlet outputs that index's value
    melody_lookup = p.add_coll("melody", dictionary=melody_sequence)
    rhythm_lookup = p.add_coll("rhythm", dictionary=rhythm_sequence)

    # Sequence player
    metro = p.add_textbox("metro 500")
    counter = p.add_textbox("counter 0 4")

    # Melody player
    note_unpack = p.add_textbox("unpack i i i")
    mtof = p.add_textbox("mtof")
    osc = p.add_textbox("cycle~")
    level = p.add_textbox("*~ 0.2")
    dac = p.add_textbox("ezdac~")

    # Rhythm player
    drums = p.add_textbox("select kick snare hihat")

    # Connect sequencer
    p.add_line(metro, counter)
    p.add_line(counter, melody_lookup)
    p.add_line(counter, rhythm_lookup)

    # Melody chain
    p.add_line(melody_lookup, note_unpack)
    p.add_line(note_unpack, mtof, outlet=0, inlet=0)
    p.add_line(mtof, osc)
    p.add_line(osc, level)
    p.add_line(level, dac)
    p.add_line(level, dac, inlet=1)

    # Rhythm chain: one outlet per drum name
    p.add_line(rhythm_lookup, drums)

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
