#!/usr/bin/env python3
"""
Demonstration of the MatrixLayoutManager for py2max.

This example shows how the MatrixLayoutManager organizes Max objects in a matrix
pattern where:
- Each column represents a connected signal chain
- Each row represents a functional category (Controls, Generators, Processors, Outputs)

Matrix Layout Pattern:
```
Row 0 (Controls):   [control0] [control1] [control2] ...
Row 1 (Generators): [gen0]     [gen1]     [gen2]     ...
Row 2 (Processors): [proc0]    [proc1]    [proc2]    ...
Row 3 (Outputs):    [output0]  [output1]  [output2]  ...
```

This creates a clear visual representation of parallel signal paths while
maintaining functional grouping by rows.
"""

from py2max import Patcher


def create_parallel_voices_matrix():
    """Create a multi-voice synthesizer using matrix layout."""

    # Create patcher with matrix layout
    p = Patcher("matrix_parallel_voices.maxpat", layout="matrix")

    print("Creating parallel voice matrix layout...")

    # Voice 1 - Column 0
    metro1 = p.add_textbox("metro 250", comment="Voice 1 Trigger", comment_pos="above")
    freq1 = p.add_floatbox(comment="Voice 1 Freq", comment_pos="above")
    osc1 = p.add_textbox("cycle~ 440", comment="Voice 1 Osc", comment_pos="above")
    env1 = p.add_textbox(
        "adsr~ 10 100 0.7 500", comment="Voice 1 Env", comment_pos="above"
    )
    gain1 = p.add_textbox("*~", comment="Voice 1 VCA", comment_pos="above")
    filter1 = p.add_textbox(
        "lores~ 1000", comment="Voice 1 Filter", comment_pos="above"
    )

    # Voice 2 - Column 1
    metro2 = p.add_textbox("metro 333", comment="Voice 2 Trigger", comment_pos="above")
    freq2 = p.add_floatbox(comment="Voice 2 Freq", comment_pos="above")
    osc2 = p.add_textbox("saw~ 330", comment="Voice 2 Osc", comment_pos="above")
    env2 = p.add_textbox(
        "adsr~ 5 50 0.5 300", comment="Voice 2 Env", comment_pos="above"
    )
    gain2 = p.add_textbox("*~", comment="Voice 2 VCA", comment_pos="above")
    filter2 = p.add_textbox(
        "lores~ 1500", comment="Voice 2 Filter", comment_pos="above"
    )

    # Voice 3 - Column 2
    metro3 = p.add_textbox("metro 500", comment="Voice 3 Trigger", comment_pos="above")
    freq3 = p.add_floatbox(comment="Voice 3 Freq", comment_pos="above")
    osc3 = p.add_textbox("tri~ 220", comment="Voice 3 Osc", comment_pos="above")
    env3 = p.add_textbox(
        "adsr~ 20 200 0.9 800", comment="Voice 3 Env", comment_pos="above"
    )
    gain3 = p.add_textbox("*~", comment="Voice 3 VCA", comment_pos="above")
    filter3 = p.add_textbox("lores~ 800", comment="Voice 3 Filter", comment_pos="above")

    # Master section - Column 3
    master_vol = p.add_floatbox(comment="Master Volume", comment_pos="above")
    mixer = p.add_textbox("gain~ 0.33", comment="Voice Mixer", comment_pos="above")
    reverb = p.add_textbox("freeverb~", comment="Master Reverb", comment_pos="above")
    master_gain = p.add_textbox("*~", comment="Master Gain", comment_pos="above")
    dac = p.add_textbox("ezdac~", comment="Audio Output", comment_pos="above")
    scope = p.add_textbox("scope~", comment="Waveform Monitor", comment_pos="above")

    # Connect Voice 1 signal chain
    p.add_line(metro1, env1)  # Trigger envelope
    p.add_line(metro1, osc1)  # Trigger oscillator
    p.add_line(freq1, osc1, inlet=1)  # Control frequency
    p.add_line(osc1, gain1, inlet=0)  # Oscillator to VCA
    p.add_line(env1, gain1, inlet=1)  # Envelope to VCA amplitude
    p.add_line(gain1, filter1)  # VCA to filter
    p.add_line(filter1, mixer, inlet=0)  # Filter to mixer

    # Connect Voice 2 signal chain
    p.add_line(metro2, env2)
    p.add_line(metro2, osc2)
    p.add_line(freq2, osc2, inlet=1)
    p.add_line(osc2, gain2, inlet=0)
    p.add_line(env2, gain2, inlet=1)
    p.add_line(gain2, filter2)
    p.add_line(filter2, mixer, inlet=0)  # Add to same mixer input (sum)

    # Connect Voice 3 signal chain
    p.add_line(metro3, env3)
    p.add_line(metro3, osc3)
    p.add_line(freq3, osc3, inlet=1)
    p.add_line(osc3, gain3, inlet=0)
    p.add_line(env3, gain3, inlet=1)
    p.add_line(gain3, filter3)
    p.add_line(filter3, mixer, inlet=0)  # Add to same mixer input (sum)

    # Connect master section
    p.add_line(mixer, reverb)  # Mixed signal to reverb
    p.add_line(reverb, master_gain, inlet=0)  # Reverb to master gain
    p.add_line(master_vol, master_gain, inlet=1)  # Master volume control
    p.add_line(master_gain, dac, inlet=0)  # Left channel
    p.add_line(master_gain, dac, inlet=1)  # Right channel (mono to stereo)
    p.add_line(master_gain, scope)  # Send to scope

    # Optimize the layout - this will organize objects into matrix pattern
    p.optimize_layout()

    # Get signal chain information
    chain_info = p._layout_mgr.get_signal_chain_info()

    # Save the patch
    p.save()

    print(f"Created matrix layout patch: {p._path}")
    print(f"Detected {chain_info['num_chains']} signal chains")
    print(
        f"Matrix size: {chain_info['matrix_size'][0]} rows × {chain_info['matrix_size'][1]} columns"
    )
    print("Objects organized in matrix pattern:")
    print("  Row 0: Control objects (metros, floatboxes)")
    print("  Row 1: Generator objects (oscillators)")
    print("  Row 2: Processor objects (envelopes, VCAs, filters, reverb)")
    print("  Row 3: Output objects (dac~, scope~)")


def create_effects_chain_matrix():
    """Create an effects processing chain using matrix layout."""

    p = Patcher("matrix_effects_chains.maxpat", layout="matrix")

    print("\nCreating effects chain matrix layout...")

    # Input controls - Row 0
    input_gain = p.add_floatbox(comment="Input Level", comment_pos="above")
    delay_time = p.add_floatbox(comment="Delay Time", comment_pos="above")
    reverb_size = p.add_floatbox(comment="Reverb Size", comment_pos="above")
    master_mix = p.add_floatbox(comment="Master Mix", comment_pos="above")

    # Input sources - Row 1
    adc = p.add_textbox("adc~ 1", comment="Audio Input", comment_pos="above")
    test_osc = p.add_textbox("cycle~ 440", comment="Test Tone", comment_pos="above")
    noise_gen = p.add_textbox("noise~", comment="Noise Source", comment_pos="above")
    input_sel = p.add_textbox(
        "selector~ 3", comment="Input Selector", comment_pos="above"
    )

    # Effects processing - Row 2
    input_amplifier = p.add_textbox("*~", comment="Input Amp", comment_pos="above")
    delay_fx = p.add_textbox("delay~ 1000", comment="Delay Effect", comment_pos="above")
    reverb_fx = p.add_textbox("freeverb~", comment="Reverb Effect", comment_pos="above")
    final_mix = p.add_textbox("*~", comment="Final Mix", comment_pos="above")

    # Outputs - Row 3
    dac = p.add_textbox("ezdac~", comment="Main Output", comment_pos="above")
    record = p.add_textbox("sfrecord~", comment="Recording", comment_pos="above")
    meter = p.add_textbox("meter~", comment="Level Meter", comment_pos="above")
    analyzer = p.add_textbox("spectroscope~", comment="Spectrum", comment_pos="above")

    # Connect Chain 1: ADC -> Input Amp -> Delay -> Final Mix -> Outputs
    p.add_line(adc, input_sel, inlet=0)
    p.add_line(input_sel, input_amplifier, outlet=0)
    p.add_line(input_gain, input_amplifier, inlet=1)
    p.add_line(input_amplifier, delay_fx)
    p.add_line(delay_time, delay_fx, inlet=1)
    p.add_line(delay_fx, final_mix, inlet=0)
    p.add_line(master_mix, final_mix, inlet=1)

    # Connect Chain 2: Test Osc -> Input Selector -> Reverb -> Final Mix
    p.add_line(test_osc, input_sel, inlet=1)
    p.add_line(input_sel, reverb_fx, outlet=0)
    p.add_line(reverb_size, reverb_fx, inlet=1)
    p.add_line(reverb_fx, final_mix, inlet=0)

    # Connect Chain 3: Noise -> Input Selector
    p.add_line(noise_gen, input_sel, inlet=2)

    # Connect outputs
    p.add_line(final_mix, dac, inlet=0)
    p.add_line(final_mix, dac, inlet=1)
    p.add_line(final_mix, record, inlet=0)
    p.add_line(final_mix, meter)
    p.add_line(final_mix, analyzer)

    # Optimize layout
    p.optimize_layout()

    # Get chain info
    chain_info = p._layout_mgr.get_signal_chain_info()

    # Save
    p.save()

    print(f"Created effects chain patch: {p._path}")
    print(f"Detected {chain_info['num_chains']} signal chains")
    print(f"Matrix demonstrates parallel input sources feeding into shared effects")


def demonstrate_signal_chain_analysis():
    """Demonstrate the signal chain analysis capabilities."""

    p = Patcher("matrix_analysis_demo.maxpat", layout="matrix")

    print("\nDemonstrating signal chain analysis...")

    # Create a patch with complex routing
    # Source controls
    metro1 = p.add_textbox("metro 250")
    metro2 = p.add_textbox("metro 333")
    volume = p.add_floatbox()

    # Generators
    osc1 = p.add_textbox("cycle~ 440")
    osc2 = p.add_textbox("saw~ 220")
    noise = p.add_textbox("noise~")

    # Processing
    mixer = p.add_textbox("gain~ 0.33")
    filter = p.add_textbox("lores~ 1000")
    delay = p.add_textbox("delay~ 500")
    gain = p.add_textbox("*~")

    # Outputs
    dac = p.add_textbox("ezdac~")
    scope = p.add_textbox("scope~")

    # Create connections with branching and merging
    p.add_line(metro1, osc1)  # Chain 1 start
    p.add_line(metro2, osc2)  # Chain 2 start
    p.add_line(osc1, mixer)  # Chain 1 to mixer
    p.add_line(osc2, mixer)  # Chain 2 to mixer (merge)
    p.add_line(noise, mixer)  # Chain 3 to mixer
    p.add_line(mixer, filter)  # Continue merged chain
    p.add_line(filter, delay)
    p.add_line(delay, gain)
    p.add_line(volume, gain, inlet=1)  # Volume control
    p.add_line(gain, dac)  # Branch to DAC
    p.add_line(gain, scope)  # Branch to scope

    # Optimize layout
    p.optimize_layout()

    # Analyze the signal chains
    chain_info = p._layout_mgr.get_signal_chain_info()

    p.save()

    print(f"Created analysis demo patch: {p._path}")
    print(f"Signal chain analysis results:")
    print(f"  - Number of chains detected: {chain_info['num_chains']}")
    print(f"  - Matrix dimensions: {chain_info['matrix_size']}")

    # Print detailed chain information
    for i, chain in enumerate(chain_info["chains"]):
        print(f"  - Chain {i}: {len(chain)} objects")
        chain_objects = []
        for obj_id in chain:
            if obj_id in p._objects:
                obj = p._objects[obj_id]
                text = getattr(obj, "text", obj.maxclass)
                if hasattr(obj, "_kwds") and "text" in obj._kwds:
                    text = obj._kwds["text"]
                chain_objects.append(text or obj.maxclass)
        print(f"    Objects: {' -> '.join(chain_objects)}")


if __name__ == "__main__":
    print("MatrixLayoutManager Demo")
    print("=" * 50)

    # Create demonstration patches
    create_parallel_voices_matrix()
    create_effects_chain_matrix()
    demonstrate_signal_chain_analysis()

    print()
    print("Demo complete! Open the generated .maxpat files in Max/MSP to see the")
    print("automatically organized matrix layout where:")
    print("- Each column represents a connected signal chain")
    print("- Each row represents a functional category")
    print("- Objects maintain their signal flow relationships while being")
    print("  visually organized for easy understanding of parallel processing")
