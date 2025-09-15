#!/usr/bin/env python3
"""
Tutorial 1: Simple Synthesis
=============================

Create a basic synthesizer with multiple oscillators for a C major chord.

This example is used in:
- docs/source/user_guide/tutorial.rst
"""

from py2max import Patcher
from py2max.utils import pitch2freq


def create_chord_synthesizer():
    """Create a basic synthesizer with multiple oscillators."""
    # Create patcher with grid layout
    p = Patcher('synthesizer.maxpat', layout="grid", flow_direction="horizontal")

    # Create oscillators for a C major chord
    freqs = [pitch2freq("C4"), pitch2freq("E4"), pitch2freq("G4")]
    oscillators = []

    for i, freq in enumerate(freqs):
        osc = p.add_textbox(f'cycle~ {freq:.2f}')
        oscillators.append(osc)

    # Add gain controls
    gains = []
    gain_mults = []
    for i in range(3):
        gain = p.add_floatbox(0.3, name=f'gain{i}')
        gains.append(gain)
        gain_mult = p.add_textbox('*~')
        gain_mults.append(gain_mult)

        # Connect oscillator to gain
        p.add_line(oscillators[i], gain_mult)
        p.add_line(gain, gain_mult, outlet=0, inlet=1)

    # Mix the signals
    mixer = p.add_textbox('+~')
    for gain_mult in gain_mults:
        p.add_line(gain_mult, mixer)

    # Add master volume and output
    master_vol = p.add_floatbox(0.5, name='master')
    master_mult = p.add_textbox('*~')
    output = p.add_textbox('ezdac~')

    p.add_line(mixer, master_mult)
    p.add_line(master_vol, master_mult, outlet=0, inlet=1)
    p.add_line(master_mult, output)

    # Optimize layout
    p.optimize_layout()
    p.save()

    return p


if __name__ == '__main__':
    patch = create_chord_synthesizer()
    print(f"Created chord synthesizer with {len(patch._boxes)} objects")
    print("Patch saved as 'synthesizer.maxpat'")