#!/usr/bin/env python3
"""
Demonstration of the ColumnarLayoutManager for py2max.

This example shows how the ColumnarLayoutManager automatically organizes
Max objects into functional columns following typical Max patch patterns:
- Column 1: Controls (parameters, inputs, UI elements)
- Column 2: Generators (oscillators, samplers, noise sources)
- Column 3: Processors (filters, effects, modulation)
- Column 4: Outputs (mixers, DACs, print objects)
"""

from py2max import Patcher


def create_typical_synth_patch():
    """Create a typical Max synthesizer patch using columnar layout."""

    # Create patcher with columnar layout
    p = Patcher('columnar_synth_demo.maxpat', layout="columnar")

    # Add control objects (Column 1: Controls)
    metro = p.add_textbox('metro 500', comment="Tempo", comment_pos="above")
    freq_control = p.add_floatbox(comment="Frequency", comment_pos="above")
    filter_freq = p.add_floatbox(comment="Filter Cutoff", comment_pos="above")
    volume = p.add_floatbox(comment="Volume", comment_pos="above")

    # Add generator objects (Column 2: Generators)
    osc1 = p.add_textbox('cycle~ 440', comment="Oscillator 1", comment_pos="above")
    osc2 = p.add_textbox('saw~ 220', comment="Oscillator 2", comment_pos="above")
    noise = p.add_textbox('noise~', comment="Noise Source", comment_pos="above")

    # Add processor objects (Column 3: Processors)
    mixer = p.add_textbox('gain~ 0.5', comment="Mixer", comment_pos="above")
    lowpass = p.add_textbox('lores~ 1000', comment="Low Pass Filter", comment_pos="above")
    delay_fx = p.add_textbox('delay~ 500', comment="Delay Effect", comment_pos="above")
    master_gain = p.add_textbox('gain~ 0.7', comment="Master Volume", comment_pos="above")

    # Add output objects (Column 4: Outputs)
    dac = p.add_textbox('ezdac~', comment="Audio Output", comment_pos="above")
    scope = p.add_textbox('scope~', comment="Waveform Display", comment_pos="above")

    # Create typical Max signal chain connections

    # Control connections
    p.add_line(metro, osc1)
    p.add_line(freq_control, osc1, inlet=1)  # Control frequency
    p.add_line(freq_control, osc2, inlet=1)  # Control frequency
    p.add_line(filter_freq, lowpass, inlet=1)  # Control filter cutoff
    p.add_line(volume, master_gain, inlet=1)  # Control master volume

    # Audio signal chain
    p.add_line(osc1, mixer, inlet=0, outlet=0)  # Oscillator 1 to mixer
    p.add_line(osc2, mixer, inlet=0, outlet=0)  # Oscillator 2 to mixer (summed)
    p.add_line(noise, mixer, inlet=0, outlet=0)  # Noise to mixer (summed)

    p.add_line(mixer, lowpass)  # Mixed signal to filter
    p.add_line(lowpass, delay_fx)  # Filtered signal to delay
    p.add_line(delay_fx, master_gain)  # Delayed signal to master volume

    # Output connections
    p.add_line(master_gain, dac, inlet=0)  # Left channel
    p.add_line(master_gain, dac, inlet=1)  # Right channel (mono to stereo)
    p.add_line(master_gain, scope)  # Send to scope for visualization

    # Optimize the layout - this will organize objects into functional columns
    p.optimize_layout()

    # Save the patch
    p.save()

    print(f"Created columnar synth patch: {p._path}")
    print(f"Objects organized into {p._layout_mgr.num_columns} functional columns:")
    print(f"  Column 1 (Controls): metro, floatboxes")
    print(f"  Column 2 (Generators): cycle~, saw~, noise~")
    print(f"  Column 3 (Processors): gain~, lores~, delay~")
    print(f"  Column 4 (Outputs): ezdac~, scope~")


def create_multi_voice_patch():
    """Create a more complex multi-voice patch demonstrating horizontal replication."""

    p = Patcher('columnar_multivoice_demo.maxpat', layout="columnar")

    # Controls for multiple voices
    metro1 = p.add_textbox('metro 250')
    metro2 = p.add_textbox('metro 333')
    metro3 = p.add_textbox('metro 500')
    freq1 = p.add_floatbox()
    freq2 = p.add_floatbox()
    freq3 = p.add_floatbox()

    # Multiple voice generators
    voice1_osc = p.add_textbox('cycle~ 220')
    voice2_osc = p.add_textbox('saw~ 330')
    voice3_osc = p.add_textbox('tri~ 440')
    voice1_env = p.add_textbox('adsr~ 10 100 0.7 500')
    voice2_env = p.add_textbox('adsr~ 5 50 0.5 300')
    voice3_env = p.add_textbox('adsr~ 20 200 0.9 800')

    # Processing for each voice
    voice1_gain = p.add_textbox('gain~ 0.33')
    voice2_gain = p.add_textbox('gain~ 0.33')
    voice3_gain = p.add_textbox('gain~ 0.33')
    voice1_filter = p.add_textbox('lores~ 1000')
    voice2_filter = p.add_textbox('lores~ 1500')
    voice3_filter = p.add_textbox('lores~ 800')
    final_mix = p.add_textbox('gain~ 0.8')

    # Outputs
    dac = p.add_textbox('ezdac~')
    meter = p.add_textbox('meter~')

    # Connect the three-voice patch
    # Voice 1 chain
    p.add_line(metro1, voice1_osc)
    p.add_line(metro1, voice1_env)
    p.add_line(freq1, voice1_osc, inlet=1)
    p.add_line(voice1_osc, voice1_gain)
    p.add_line(voice1_env, voice1_gain, inlet=1)
    p.add_line(voice1_gain, voice1_filter)
    p.add_line(voice1_filter, final_mix)

    # Voice 2 chain
    p.add_line(metro2, voice2_osc)
    p.add_line(metro2, voice2_env)
    p.add_line(freq2, voice2_osc, inlet=1)
    p.add_line(voice2_osc, voice2_gain)
    p.add_line(voice2_env, voice2_gain, inlet=1)
    p.add_line(voice2_gain, voice2_filter)
    p.add_line(voice2_filter, final_mix)

    # Voice 3 chain
    p.add_line(metro3, voice3_osc)
    p.add_line(metro3, voice3_env)
    p.add_line(freq3, voice3_osc, inlet=1)
    p.add_line(voice3_osc, voice3_gain)
    p.add_line(voice3_env, voice3_gain, inlet=1)
    p.add_line(voice3_gain, voice3_filter)
    p.add_line(voice3_filter, final_mix)

    # Final output
    p.add_line(final_mix, dac)
    p.add_line(final_mix, meter)

    # Organize into columns with horizontal replication where needed
    p.optimize_layout()
    p.save()

    print(f"Created multi-voice patch: {p._path}")
    print(f"Demonstrates horizontal replication within functional columns")


if __name__ == "__main__":
    print("ColumnarLayoutManager Demo")
    print("=" * 50)

    # Create demonstration patches
    create_typical_synth_patch()
    print()
    create_multi_voice_patch()

    print()
    print("Demo complete! Open the generated .maxpat files in Max/MSP to see the")
    print("automatically organized columnar layout.")