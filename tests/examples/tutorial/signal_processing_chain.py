#!/usr/bin/env python3
"""
Tutorial 2: Signal Processing Chain
====================================

Create a complex audio processing chain with EQ, distortion, delay, and output.

This example is used in:
- docs/source/user_guide/tutorial.rst
"""

from py2max import Patcher


def create_fx_chain():
    """Create a complex audio processing chain."""
    # Use flow layout for signal processing
    p = Patcher("fx-chain.maxpat", layout="flow", flow_direction="vertical")

    # Input section
    input_obj = p.add_textbox("adc~ 1 2")
    input_gain = p.add_textbox("*~ 1.0")
    p.add_line(input_obj, input_gain)

    # Add input level control
    input_level = p.add_floatparam("input_level", initial=1.0)
    p.add_line(input_level, input_gain, outlet=0, inlet=1)

    # EQ section: svf~ outlets are low-pass, high-pass, band-pass, notch
    highpass = p.add_textbox("svf~ 100 0.5")
    lowpass = p.add_textbox("svf~ 8000 0.5")

    p.add_line(input_gain, highpass)
    p.add_line(highpass, lowpass, outlet=1)  # high-pass output

    # Distortion section
    drive = p.add_floatparam("drive", initial=1.0)
    drive_mult = p.add_textbox("*~")
    overdrive = p.add_textbox("overdrive~")

    p.add_line(lowpass, drive_mult)  # low-pass output
    p.add_line(drive, drive_mult, outlet=0, inlet=1)
    p.add_line(drive_mult, overdrive)

    # Delay section: tapin~/tapout~, since a signal loop through delay~ is
    # not allowed
    delay_time = p.add_floatparam("delay_time", initial=250.0)
    tapin = p.add_textbox("tapin~ 1000")
    tapout = p.add_textbox("tapout~ 250")
    delay_feedback = p.add_floatparam("feedback", initial=0.3)
    feedback_mult = p.add_textbox("*~")

    p.add_line(overdrive, tapin)
    p.add_line(tapin, tapout)
    p.add_line(delay_time, tapout)  # delay time in ms
    p.add_line(tapout, feedback_mult)
    p.add_line(delay_feedback, feedback_mult, outlet=0, inlet=1)
    p.add_line(feedback_mult, tapin)  # feedback loop

    # Wet/dry mix: wet * mix + dry * (1 - mix)
    delay_mix = p.add_floatparam("delay_mix", initial=0.3)
    dry_level = p.add_textbox("!- 1.")
    wet_gain = p.add_textbox("*~")
    dry_gain = p.add_textbox("*~")
    wet_dry = p.add_textbox("+~")

    p.add_line(tapout, wet_gain)
    p.add_line(delay_mix, wet_gain, outlet=0, inlet=1)
    p.add_line(delay_mix, dry_level)
    p.add_line(overdrive, dry_gain)
    p.add_line(dry_level, dry_gain, outlet=0, inlet=1)
    p.add_line(wet_gain, wet_dry)
    p.add_line(dry_gain, wet_dry, outlet=0, inlet=1)

    # Output section
    output_gain = p.add_textbox("*~")
    output_level = p.add_floatparam("output_level", initial=0.7)
    output = p.add_textbox("dac~ 1 2")

    p.add_line(wet_dry, output_gain)
    p.add_line(output_level, output_gain, outlet=0, inlet=1)
    p.add_line(output_gain, output)
    p.add_line(output_gain, output, outlet=0, inlet=1)

    # Optimize layout for signal flow
    p.optimize_layout()
    p.save()

    return p


if __name__ == "__main__":
    patch = create_fx_chain()
    print(f"Created FX chain with {len(patch._boxes)} objects")
    print("Patch saved as 'fx-chain.maxpat'")
