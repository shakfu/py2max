#!/usr/bin/env python3
"""
Tutorial 4: Generative Music System
====================================

Create a generative music system with multiple patterns and scales.

This example is used in:
- docs/source/user_guide/tutorial.rst
"""

from py2max import Patcher


def create_generative_music():
    """Create a generative music system with multiple patterns."""
    p = Patcher("generative-music.maxpat", layout="flow", flow_direction="horizontal")

    # Master clock
    master_tempo = p.add_floatparam("tempo", initial=120.0)
    metro = p.add_textbox("metro 500")

    p.add_line(master_tempo, metro)

    # Create 4 pattern generators
    patterns = []
    # MIDI note numbers (C4 = 60); a table holds ints
    scales = [
        [60, 62, 64, 67, 69],  # Pentatonic: C D E G A
        [60, 62, 65, 67, 69, 72],  # Minor pentatonic: C D F G A C
        [60, 64, 65, 67, 71],  # Mysterious: C E F G B
        [60, 61, 65, 66, 68],  # Diminished: C Db F Gb Ab
    ]

    for i, scale in enumerate(scales):
        # Pattern trigger
        pattern_div = p.add_textbox(f"/ {2 ** (i + 1)}")  # Different divisions
        pattern_metro = p.add_textbox("metro")

        p.add_line(metro, pattern_div)
        p.add_line(pattern_div, pattern_metro)

        # Note selection
        note_selector = p.add_textbox(f"random {len(scale)}")
        p.add_line(pattern_metro, note_selector)

        # Look up the note, then convert it to a frequency
        table_lookup = p.add_table(f"notes{i}", array=scale)
        to_freq = p.add_textbox("mtof")

        p.add_line(note_selector, table_lookup)
        p.add_line(table_lookup, to_freq)

        # Synthesizer voice
        osc = p.add_textbox("cycle~")
        env = p.add_textbox("adsr~ 10 100 0.3 500")
        voice_gain = p.add_textbox("*~")

        p.add_line(to_freq, osc)
        p.add_line(pattern_metro, env)  # Trigger envelope
        p.add_line(osc, voice_gain)
        p.add_line(env, voice_gain, outlet=0, inlet=1)

        # Voice level control
        voice_level = p.add_floatparam(f"voice{i}_level", initial=0.25)
        voice_mult = p.add_textbox("*~")

        p.add_line(voice_gain, voice_mult)
        p.add_line(voice_level, voice_mult, outlet=0, inlet=1)

        patterns.append(
            {"voice": voice_mult, "level": voice_level, "tempo_div": pattern_div}
        )

    # Mix all voices
    main_mixer = p.add_textbox("+~")
    for pattern in patterns:
        p.add_line(pattern["voice"], main_mixer)

    # Global effects
    reverb = p.add_textbox("comb~ 100 37 1. 0. 0.7")  # feedback comb, a reverb stand-in
    master_gain = p.add_textbox("*~")
    master_level = p.add_floatparam("master_level", initial=0.6)
    output = p.add_textbox("ezdac~")

    p.add_line(main_mixer, reverb)
    p.add_line(reverb, master_gain)
    p.add_line(master_level, master_gain, outlet=0, inlet=1)
    p.add_line(master_gain, output)

    # Add global controls: non-zero starts the metro, 0 stops it
    start = p.add_message("1")
    stop = p.add_message("0")
    p.add_line(start, metro)
    p.add_line(stop, metro)

    p.optimize_layout()
    p.save()

    return p


if __name__ == "__main__":
    patch = create_generative_music()
    print(f"Created generative music system with {len(patch._boxes)} objects")
    print("Patch saved as 'generative-music.maxpat'")
