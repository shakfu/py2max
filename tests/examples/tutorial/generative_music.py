#!/usr/bin/env python3
"""
Tutorial 4: Generative Music System
====================================

Create a generative music system with multiple patterns and scales.

This example is used in:
- docs/source/user_guide/tutorial.rst
"""

from py2max import Patcher
from py2max.utils import pitch2freq


def create_generative_music():
    """Create a generative music system with multiple patterns."""
    p = Patcher("generative-music.maxpat", layout="flow", flow_direction="horizontal")

    # Master clock
    master_tempo = p.add_floatbox(120.0, name="tempo")
    metro = p.add_textbox("metro 500")

    p.add_line(master_tempo, metro)

    # Create 4 pattern generators
    patterns = []
    scales = [
        ["C4", "D4", "E4", "G4", "A4"],  # Pentatonic
        ["C4", "D4", "F4", "G4", "A4", "C5"],  # Minor pentatonic
        ["C4", "E4", "F4", "G4", "B4"],  # Mysterious
        ["C4", "Db4", "F4", "Gb4", "Ab4"],  # Diminished
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

        # Convert to frequencies
        freq_data = [pitch2freq(note) for note in scale]
        freq_table = p.add_table(f"freqs{i}", data=freq_data)
        table_lookup = p.add_textbox(f"table freqs{i}")

        p.add_line(note_selector, table_lookup)

        # Synthesizer voice
        osc = p.add_textbox("cycle~")
        env = p.add_textbox("adsr~ 10 100 0.3 500")
        voice_gain = p.add_textbox("*~")

        p.add_line(table_lookup, osc)
        p.add_line(pattern_metro, env)  # Trigger envelope
        p.add_line(osc, voice_gain)
        p.add_line(env, voice_gain, outlet=0, inlet=1)

        # Voice level control
        voice_level = p.add_floatbox(0.25, name=f"voice{i}_level")
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
    reverb = p.add_textbox("freeverb~ 0.8 0.5")
    master_gain = p.add_textbox("*~")
    master_level = p.add_floatbox(0.6, name="master_level")
    output = p.add_textbox("ezdac~")

    p.add_line(main_mixer, reverb)
    p.add_line(reverb, master_gain)
    p.add_line(master_level, master_gain, outlet=0, inlet=1)
    p.add_line(master_gain, output)

    # Add global controls
    start_stop = p.add_message("start", "stop")
    p.add_line(start_stop, metro)

    p.optimize_layout()
    p.save()

    return p


if __name__ == "__main__":
    patch = create_generative_music()
    print(f"Created generative music system with {len(patch._boxes)} objects")
    print("Patch saved as 'generative-music.maxpat'")
