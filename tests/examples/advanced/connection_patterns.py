#!/usr/bin/env python3
"""
Advanced Usage: Connection Patterns
====================================

Examples demonstrating fan-out, feedback loops, and matrix routing.

This example is used in:
- docs/source/user_guide/advanced_usage.rst
"""

from py2max import Patcher


def create_fan_out_example():
    """Create a fan-out connection pattern."""
    p = Patcher('fan-out.maxpat', layout="flow")

    source = p.add_textbox('cycle~ 440')

    # Connect one source to multiple destinations
    destinations = []
    for i in range(6):
        dest = p.add_textbox(f'biquad~ {200 + i * 300} 0.707')
        destinations.append(dest)

        # Fan out from source
        p.add_line(source, dest)

    # Collect all processed signals
    collector = p.add_textbox('+~')
    for dest in destinations:
        p.add_line(dest, collector)

    p.optimize_layout()
    p.save()
    return p


def create_feedback_delay():
    """Create a feedback delay system."""
    p = Patcher('feedback-delay.maxpat')

    # Input
    input_obj = p.add_textbox('adc~')

    # Delay line with feedback
    delay = p.add_textbox('delay~ 500')
    feedback_gain = p.add_floatbox(0.3, name='feedback')
    feedback_mult = p.add_textbox('*~')
    input_mix = p.add_textbox('+~')

    # Create feedback loop
    p.add_line(input_obj, input_mix)
    p.add_line(input_mix, delay)
    p.add_line(delay, feedback_mult)
    p.add_line(feedback_gain, feedback_mult, outlet=0, inlet=1)
    p.add_line(feedback_mult, input_mix, outlet=0, inlet=1)  # Feedback

    # Output
    output = p.add_textbox('dac~')
    p.add_line(delay, output)

    p.save()
    return p


def create_matrix_mixer():
    """Create a 4x4 matrix mixer."""
    p = Patcher('matrix-mixer.maxpat', layout="grid")

    # Create 4x4 matrix mixer
    sources = []
    destinations = []

    # Create sources
    for i in range(4):
        source = p.add_textbox(f'cycle~ {220 * (i + 1)}')
        sources.append(source)

    # Create destinations
    for i in range(4):
        dest = p.add_textbox(f'dac~ {i + 1}')
        destinations.append(dest)

    # Create matrix of gain controls
    matrix = {}
    for src_idx in range(4):
        for dst_idx in range(4):
            # Gain control
            gain = p.add_floatbox(0.0, name=f'gain_{src_idx}_{dst_idx}')
            mult = p.add_textbox('*~')

            # Store for routing
            matrix[(src_idx, dst_idx)] = {'gain': gain, 'mult': mult}

            # Connect source to multiplier
            p.add_line(sources[src_idx], mult)
            p.add_line(gain, mult, outlet=0, inlet=1)

    # Create summing for each destination
    for dst_idx in range(4):
        summer = p.add_textbox('+~')

        # Sum all sources for this destination
        for src_idx in range(4):
            p.add_line(matrix[(src_idx, dst_idx)]['mult'], summer)

        # Connect to destination
        p.add_line(summer, destinations[dst_idx])

    p.optimize_layout()
    p.save()
    return p


if __name__ == '__main__':
    # Create fan-out example
    fanout_patch = create_fan_out_example()
    print(f"Created fan-out example with {len(fanout_patch._boxes)} objects")

    # Create feedback delay
    feedback_patch = create_feedback_delay()
    print(f"Created feedback delay with {len(feedback_patch._boxes)} objects")

    # Create matrix mixer
    matrix_patch = create_matrix_mixer()
    print(f"Created matrix mixer with {len(matrix_patch._boxes)} objects")