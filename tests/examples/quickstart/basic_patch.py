#!/usr/bin/env python3
"""
Basic Patch Example
===================

Your first py2max patch: a simple oscillator.

This example is used in:
- docs/source/index.rst (Quick Start section)
- docs/source/user_guide/quickstart.rst
"""

from py2max import Patcher


def create_basic_patch():
    """Create a simple oscillator patch."""
    # Create a new patcher
    p = Patcher("my-first-patch.maxpat")

    # Add a sine wave oscillator
    osc = p.add_textbox("cycle~ 440")

    # Add a gain control
    gain = p.add_textbox("gain~ 0.5")

    # Add audio output
    dac = p.add_textbox("ezdac~")

    # Connect the objects
    p.add_line(osc, gain)  # oscillator -> gain
    p.add_line(gain, dac)  # gain -> output

    # Save the patch
    p.save()

    return p


if __name__ == "__main__":
    patch = create_basic_patch()
    print(f"Created basic patch with {len(patch._boxes)} objects")
    print("Patch saved as 'my-first-patch.maxpat'")
