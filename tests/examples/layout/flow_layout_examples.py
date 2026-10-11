#!/usr/bin/env python3
"""
Layout Examples: Flow Layout Manager
=====================================

Examples demonstrating flow layout with signal flow analysis.

This example is used in:
- docs/source/user_guide/layout_managers.rst
"""

from py2max import Patcher


def create_horizontal_flow():
    """Horizontal signal flow layout."""
    # Horizontal signal flow (left-to-right)
    p = Patcher("flow-horizontal.maxpat", layout="flow", flow_direction="horizontal")

    # Create a signal processing chain
    input_obj = p.add_textbox("adc~")
    eq = p.add_textbox("svf~ 1000 0.5")  # low-pass from outlet 0
    compressor = p.add_textbox("omx.comp~")
    delay = p.add_textbox("delay~ 44100 11025")  # samples
    reverb = p.add_textbox("comb~ 100 37 1. 0. 0.7")  # feedback comb
    output = p.add_textbox("dac~")

    # Connect in signal flow order
    p.add_line(input_obj, eq)
    p.add_line(eq, compressor)
    p.add_line(compressor, delay)
    p.add_line(delay, reverb)
    p.add_line(reverb, output)

    # Layout will arrange objects in hierarchical levels
    p.optimize_layout()
    p.save()
    return p


def create_vertical_flow():
    """Vertical signal flow layout."""
    # Vertical signal flow (top-to-bottom)
    p = Patcher("flow-vertical.maxpat", layout="flow", flow_direction="vertical")

    # Create control flow
    metro = p.add_textbox("metro 500")
    counter = p.add_textbox("counter 0 7")
    select = p.add_textbox("select 0 1 2 3 4 5 6 7")

    # Create multiple outputs
    outputs = []
    for i in range(8):
        outlet = p.add_textbox(f"outlet {i}")
        outputs.append(outlet)

    # Connect control flow
    p.add_line(metro, counter)
    p.add_line(counter, select)

    # Connect to all outputs
    for i, outlet in enumerate(outputs):
        p.add_line(select, outlet, outlet=i, inlet=0)

    # Vertical layout will create clear top-to-bottom hierarchy
    p.optimize_layout()
    p.save()
    return p


def create_complex_flow():
    """Complex flow pattern with multiple signal paths."""
    p = Patcher("complex-flow.maxpat", layout="flow")

    # Multiple sources
    source1 = p.add_textbox("cycle~ 220")
    source2 = p.add_textbox("cycle~ 330")
    source3 = p.add_textbox("noise~")

    # Processing layers
    mixer1 = p.add_textbox("+~")
    mixer2 = p.add_textbox("+~")
    main_filter = p.add_textbox("svf~")

    # Multiple effects: chorus is a short delay swept by a slow LFO
    chorus_in = p.add_textbox("tapin~ 50")
    chorus_out = p.add_textbox("tapout~ 20")
    lfo = p.add_textbox("cycle~ 0.5")
    depth = p.add_textbox("*~ 5")
    center = p.add_textbox("+~ 20")
    delay = p.add_textbox("delay~ 44100 16538")  # samples
    reverb = p.add_textbox("comb~ 100 37 1. 0. 0.7")  # feedback comb

    # Final mixing: equal parts dry and wet
    dry = p.add_textbox("*~ 0.5")
    wet = p.add_textbox("*~ 0.5")
    wet_dry = p.add_textbox("+~")
    output = p.add_textbox("ezdac~")

    # Complex connection pattern
    p.add_line(source1, mixer1)
    p.add_line(source2, mixer1)
    p.add_line(source3, mixer2)

    p.add_line(mixer1, main_filter)
    p.add_line(mixer2, main_filter)

    p.add_line(main_filter, chorus_in)
    p.add_line(chorus_in, chorus_out)
    p.add_line(lfo, depth)
    p.add_line(depth, center)
    p.add_line(center, chorus_out)  # delay time in ms
    p.add_line(chorus_out, delay)
    p.add_line(delay, reverb)

    # Wet/dry mixing
    p.add_line(main_filter, dry)
    p.add_line(reverb, wet)
    p.add_line(dry, wet_dry)
    p.add_line(wet, wet_dry, outlet=0, inlet=1)
    p.add_line(wet_dry, output)
    p.add_line(wet_dry, output, outlet=0, inlet=1)

    p.optimize_layout()
    p.save()
    return p


def create_parallel_processing():
    """Parallel processing with flow layout."""
    p = Patcher("parallel-flow.maxpat", layout="flow", flow_direction="horizontal")

    # Single input
    input_obj = p.add_textbox("adc~")

    # Parallel processing paths; svf~ outlets are low-pass, high-pass,
    # band-pass, notch
    path1_filter = p.add_textbox("svf~ 500 0.8")
    path1_gain = p.add_textbox("*~ 1.2")

    path2_filter = p.add_textbox("svf~ 2000 0.5")
    path2_gain = p.add_textbox("*~ 0.8")

    path3_filter = p.add_textbox("svf~ 8000 0.3")
    path3_gain = p.add_textbox("*~ 1.5")

    # Connect parallel paths
    p.add_line(input_obj, path1_filter)
    p.add_line(input_obj, path2_filter)
    p.add_line(input_obj, path3_filter)

    p.add_line(path1_filter, path1_gain, outlet=2)  # band-pass
    p.add_line(path2_filter, path2_gain)  # low-pass
    p.add_line(path3_filter, path3_gain, outlet=1)  # high-pass

    # Mix parallel outputs
    final_mixer = p.add_textbox("+~")
    output = p.add_textbox("dac~")

    p.add_line(path1_gain, final_mixer)
    p.add_line(path2_gain, final_mixer)
    p.add_line(path3_gain, final_mixer)
    p.add_line(final_mixer, output)

    p.optimize_layout()
    p.save()
    return p


def create_feedback_flow():
    """Flow layout with feedback connections."""
    p = Patcher("feedback-flow.maxpat", layout="flow", flow_direction="vertical")

    # Main signal path
    input_obj = p.add_textbox("adc~")
    main_gain = p.add_textbox("*~ 1.0")
    main_filter = p.add_textbox("svf~ 1000 0.5")

    # Feedback path: tapin~/tapout~, since a signal loop through delay~ is
    # not allowed
    tapin = p.add_textbox("tapin~ 1000")
    tapout = p.add_textbox("tapout~ 500")
    feedback_gain = p.add_textbox("*~ 0.3")
    feedback_filter = p.add_textbox("svf~ 2000 0.5")

    # Mix point
    input_mixer = p.add_textbox("+~")
    output = p.add_textbox("dac~")

    # Main signal path
    p.add_line(input_obj, input_mixer)
    p.add_line(input_mixer, main_gain)
    p.add_line(main_gain, main_filter)
    p.add_line(main_filter, output)

    # Feedback path
    p.add_line(main_filter, tapin)
    p.add_line(tapin, tapout)
    p.add_line(tapout, feedback_gain)
    p.add_line(feedback_gain, feedback_filter)
    p.add_line(feedback_filter, input_mixer, outlet=1, inlet=1)  # high-pass back

    p.optimize_layout()
    p.save()
    return p


if __name__ == "__main__":
    # Create horizontal flow
    horizontal_patch = create_horizontal_flow()
    print(f"Created horizontal flow with {len(horizontal_patch._boxes)} objects")

    # Create vertical flow
    vertical_patch = create_vertical_flow()
    print(f"Created vertical flow with {len(vertical_patch._boxes)} objects")

    # Create complex flow
    complex_patch = create_complex_flow()
    print(f"Created complex flow with {len(complex_patch._boxes)} objects")

    # Create parallel processing
    parallel_patch = create_parallel_processing()
    print(f"Created parallel processing with {len(parallel_patch._boxes)} objects")

    # Create feedback flow
    feedback_patch = create_feedback_flow()
    print(f"Created feedback flow with {len(feedback_patch._boxes)} objects")
