#!/usr/bin/env python3
"""
Advanced Usage: Connection Patterns
====================================

Examples demonstrating fan-out, feedback loops, and matrix routing.

This example is used in:
- docs/source/user_guide/advanced_usage.rst
"""

from py2max import Patcher
from py2max.core.common import Rect


def create_fan_out_example():
    """Create a fan-out connection pattern."""
    p = Patcher("fan-out.maxpat", layout="flow")

    source = p.add_textbox("cycle~ 440")

    # Connect one source to multiple destinations
    destinations = []
    for i in range(6):
        dest = p.add_textbox(f"svf~ {200 + i * 300} 0.5")
        destinations.append(dest)

        # Fan out from source
        p.add_line(source, dest)

    # Collect all processed signals
    collector = p.add_textbox("+~")
    for dest in destinations:
        p.add_line(dest, collector, outlet=2)  # svf~ band-pass

    p.optimize_layout()
    p.save()
    return p


def create_feedback_delay():
    """Create a feedback delay system."""
    p = Patcher("feedback-delay.maxpat")

    # Input
    input_obj = p.add_textbox("adc~")

    # Delay line with feedback: tapin~/tapout~, since a signal loop
    # through delay~ is not allowed
    tapin = p.add_textbox("tapin~ 1000")
    tapout = p.add_textbox("tapout~ 500")  # ms
    feedback_gain = p.add_floatparam("feedback", initial=0.3)
    feedback_mult = p.add_textbox("*~")
    input_mix = p.add_textbox("+~")

    # Create feedback loop
    p.add_line(input_obj, input_mix)
    p.add_line(input_mix, tapin)
    p.add_line(tapin, tapout)
    p.add_line(tapout, feedback_mult)
    p.add_line(feedback_gain, feedback_mult, outlet=0, inlet=1)
    p.add_line(feedback_mult, input_mix, outlet=0, inlet=1)  # Feedback

    # Output
    output = p.add_textbox("dac~")
    p.add_line(tapout, output)

    p.save()
    return p


def create_matrix_mixer(n=4):
    """Create an n x n matrix mixer abstraction, ``matrix-mixer.maxpat``.

    Inlets 1-n take signals, inlet n+1 takes ``src dst gain`` messages
    (0-based indices); outlets 1-n carry the mixes. Gains start as the
    identity, so each input passes to the matching output.
    """
    p = Patcher("matrix-mixer.maxpat")
    col = 120  # x spacing; Max numbers inlets and outlets by x

    def rect(x, y, w=60.0):
        return Rect(x, y, w, 22.0)

    # Signal inlets and the control inlet, left to right
    inlets = [
        p.add_textbox("inlet", patching_rect=rect(40 + col * i, 20, 30))
        for i in range(n)
    ]
    control = p.add_textbox("inlet", patching_rect=rect(40 + col * n, 20, 30))

    # "src dst gain": route by src, then by dst, leaving the gain
    indices = " ".join(str(i) for i in range(n))
    by_src = p.add_textbox(
        f"route {indices}", patching_rect=rect(40 + col * n, 60, 100)
    )
    p.add_line(control, by_src)

    # Gain matrix: one *~ per (src, dst), in a column per source
    mults = {}
    for src in range(n):
        by_dst = p.add_textbox(
            f"route {indices}", patching_rect=rect(40 + col * n, 100 + 30 * src, 100)
        )
        p.add_line(by_src, by_dst, outlet=src)
        for dst in range(n):
            gain = 1.0 if src == dst else 0.0
            mult = p.add_textbox(
                f"*~ {gain}", patching_rect=rect(40 + col * src, 100 + 40 * dst)
            )
            p.add_line(inlets[src], mult)
            p.add_line(by_dst, mult, outlet=dst, inlet=1)
            mults[src, dst] = mult

    # Sum each destination's column of gains into its outlet
    for dst in range(n):
        summer = p.add_textbox("+~", patching_rect=rect(40 + col * dst, 120 + 40 * n))
        outlet = p.add_textbox(
            "outlet", patching_rect=rect(40 + col * dst, 160 + 40 * n, 30)
        )
        for src in range(n):
            p.add_line(mults[src, dst], summer)
        p.add_line(summer, outlet)

    p.save()
    return p


def create_matrix_mixer_host(n=4):
    """Use the ``matrix-mixer`` abstraction; save it beside this patch."""
    create_matrix_mixer(n)
    p = Patcher("matrix-mixer-host.maxpat")

    # An abstraction is an object named after its file. py2max cannot read
    # its port counts, so state them.
    mixer = p.add_textbox("matrix-mixer", numinlets=n + 1, numoutlets=n)
    channels = " ".join(str(i + 1) for i in range(n))
    dac = p.add_textbox(f"dac~ {channels}")

    for i in range(n):
        osc = p.add_textbox(f"cycle~ {220 * (i + 1)}")
        p.add_line(osc, mixer, inlet=i)
        p.add_line(mixer, dac, outlet=i, inlet=i)

    # Send source 0 to destination 1 at half gain
    msg = p.add_message("0 1 0.5")
    p.add_line(msg, mixer, inlet=n)

    p.optimize_layout()
    p.save()
    return p


if __name__ == "__main__":
    # Create fan-out example
    fanout_patch = create_fan_out_example()
    print(f"Created fan-out example with {len(fanout_patch._boxes)} objects")

    # Create feedback delay
    feedback_patch = create_feedback_delay()
    print(f"Created feedback delay with {len(feedback_patch._boxes)} objects")

    # Create the matrix mixer abstraction and a patch that uses it
    host_patch = create_matrix_mixer_host()
    print(f"Created matrix mixer host with {len(host_patch._boxes)} objects")
