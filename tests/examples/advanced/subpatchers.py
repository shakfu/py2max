#!/usr/bin/env python3
"""
Advanced Usage: Subpatchers
============================

Examples demonstrating subpatcher creation and nested structures.

This example is used in:
- docs/source/user_guide/advanced_usage.rst
"""

from py2max import Patcher


def create_basic_subpatcher():
    """Create a basic subpatcher example."""
    # Create main patch
    main = Patcher("main.maxpat")

    # Create subpatcher
    sub_box = main.add_subpatcher("voice")
    sub = sub_box.subpatcher  # Access the actual subpatcher

    # Add objects to subpatcher
    inlet = sub.add_textbox("inlet~")
    filter_obj = sub.add_textbox("biquad~ 1000 0.707")
    env = sub.add_textbox("adsr~ 10 100 0.3 500")
    vca = sub.add_textbox("*~")
    outlet = sub.add_textbox("outlet~")

    # Connect subpatcher internals
    sub.add_line(inlet, filter_obj)
    sub.add_line(filter_obj, vca)
    sub.add_line(env, vca, outlet=0, inlet=1)
    sub.add_line(vca, outlet)

    # Use subpatcher in main patch
    osc = main.add_textbox("cycle~ 440")
    voice_instance = main.add_textbox("p voice")
    output = main.add_textbox("dac~")

    main.add_line(osc, voice_instance)
    main.add_line(voice_instance, output)

    main.save()
    return main


def create_nested_subpatchers():
    """Create deeply nested subpatcher structure."""
    # Create main patch
    main = Patcher("complex.maxpat")

    # Level 1 subpatcher
    synth_box = main.add_subpatcher("synthesizer")
    synth = synth_box.subpatcher

    # Level 2 subpatcher inside synth
    osc_bank_box = synth.add_subpatcher("oscillator-bank")
    oscillator_bank = osc_bank_box.subpatcher

    # Add objects to nested subpatcher
    for i in range(4):
        osc = oscillator_bank.add_textbox(f"cycle~ {220 * (i + 1)}")
        out = oscillator_bank.add_textbox(f"outlet~ {i}")
        oscillator_bank.add_line(osc, out)

    # Use nested subpatchers
    bank_instance = synth.add_textbox("p oscillator-bank")
    mixer = synth.add_textbox("+~")
    synth_out = synth.add_textbox("outlet~")

    # Connect multiple outlets
    for i in range(4):
        synth.add_line(bank_instance, mixer, outlet=i, inlet=0)

    synth.add_line(mixer, synth_out)

    main.save()
    return main


if __name__ == "__main__":
    # Create basic subpatcher example
    basic_patch = create_basic_subpatcher()
    print(f"Created basic subpatcher with {len(basic_patch._boxes)} objects")

    # Create nested subpatcher example
    nested_patch = create_nested_subpatchers()
    print(f"Created nested subpatcher system with {len(nested_patch._boxes)} objects")
