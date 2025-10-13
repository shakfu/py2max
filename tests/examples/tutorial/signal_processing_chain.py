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
    input_level = p.add_floatbox(1.0, name="input_level")
    p.add_line(input_level, input_gain, outlet=0, inlet=1)

    # EQ section
    highpass = p.add_textbox("biquad~ 100. 0.707 highpass")
    lowpass = p.add_textbox("biquad~ 8000. 0.707 lowpass")

    p.add_line(input_gain, highpass)
    p.add_line(highpass, lowpass)

    # Distortion section
    drive = p.add_floatbox(1.0, name="drive")
    drive_mult = p.add_textbox("*~")
    overdrive = p.add_textbox("overdrive~")

    p.add_line(lowpass, drive_mult)
    p.add_line(drive, drive_mult, outlet=0, inlet=1)
    p.add_line(drive_mult, overdrive)

    # Delay section
    delay_time = p.add_floatbox(250.0, name="delay_time")
    delay = p.add_textbox("delay~")
    delay_feedback = p.add_floatbox(0.3, name="feedback")
    feedback_mult = p.add_textbox("*~")
    delay_mix = p.add_floatbox(0.3, name="delay_mix")
    wet_dry = p.add_textbox("crossfade~")

    # Delay connections
    p.add_line(delay_time, delay)
    p.add_line(overdrive, delay)
    p.add_line(delay, feedback_mult)
    p.add_line(delay_feedback, feedback_mult, outlet=0, inlet=1)
    p.add_line(feedback_mult, delay, outlet=0, inlet=1)  # feedback loop

    # Wet/dry mix
    p.add_line(overdrive, wet_dry, outlet=0, inlet=0)  # dry signal
    p.add_line(delay, wet_dry, outlet=0, inlet=1)  # wet signal
    p.add_line(delay_mix, wet_dry, outlet=0, inlet=2)  # mix control

    # Output section
    output_gain = p.add_textbox("*~")
    output_level = p.add_floatbox(0.7, name="output_level")
    output = p.add_textbox("dac~ 1 2")

    p.add_line(wet_dry, output_gain)
    p.add_line(output_level, output_gain, outlet=0, inlet=1)
    p.add_line(output_gain, output)

    # Optimize layout for signal flow
    p.optimize_layout()
    p.save()

    return p


if __name__ == "__main__":
    patch = create_fx_chain()
    print(f"Created FX chain with {len(patch._boxes)} objects")
    print("Patch saved as 'fx-chain.maxpat'")
