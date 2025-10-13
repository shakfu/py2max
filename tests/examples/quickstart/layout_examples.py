#!/usr/bin/env python3
"""
Layout Examples
===============

Examples demonstrating different layout managers.

This example is used in:
- docs/source/user_guide/quickstart.rst
"""

from py2max import Patcher


def grid_layout_example():
    """Grid layout with automatic clustering."""
    # Horizontal grid with automatic clustering
    p = Patcher("grid-example.maxpat", layout="grid", flow_direction="horizontal")

    # Add several objects
    objects = []
    for i in range(5):
        obj = p.add_textbox(f"cycle~ {440 + i * 110}")
        objects.append(obj)

    # Connect them in sequence
    for i in range(len(objects) - 1):
        p.add_line(objects[i], objects[i + 1])

    # Optimize layout to cluster connected objects
    p.optimize_layout()
    p.save()

    return p


def flow_layout_example():
    """Signal flow-based layout."""
    # Signal flow-based layout
    p = Patcher("flow-example.maxpat", layout="flow", flow_direction="vertical")

    # Create a signal processing chain
    input_obj = p.add_textbox("adc~")
    eq = p.add_textbox("filtergraph~")
    delay = p.add_textbox("delay~ 500")
    reverb = p.add_textbox("freeverb~")
    output = p.add_textbox("dac~")

    # Connect in signal flow order
    p.add_line(input_obj, eq)
    p.add_line(eq, delay)
    p.add_line(delay, reverb)
    p.add_line(reverb, output)

    # Layout will arrange objects hierarchically
    p.optimize_layout()
    p.save()

    return p


def object_help_example():
    """Getting object help."""
    p = Patcher("help-example.maxpat")

    # Add an object
    umenu = p.add_textbox("umenu")

    # Get formatted help (returns string, don't print in example)
    help_text = umenu.help()

    # Get detailed object information
    info = umenu.get_info()
    methods_count = len(info.get("methods", [])) if info else 0
    attributes_count = len(info.get("attributes", [])) if info else 0
    inlets = umenu.get_inlet_count()
    outlets = umenu.get_outlet_count()

    p.save()

    return p, help_text, methods_count, attributes_count, inlets, outlets


def connection_validation_example():
    """Connection validation demonstration."""
    from py2max import InvalidConnectionError

    # Enable validation (default)
    p = Patcher("validation-example.maxpat", validate_connections=True)

    osc = p.add_textbox("cycle~ 440")
    gain = p.add_textbox("gain~")

    # Valid connection
    p.add_line(osc, gain)

    # This would raise an error (cycle~ only has 1 outlet)
    try:
        p.add_line(osc, gain, outlet=5)
        error_occurred = False
    except InvalidConnectionError as e:
        error_occurred = True
        error_message = str(e)

    p.save()

    return p, error_occurred


if __name__ == "__main__":
    # Run all examples
    print("Creating grid layout example...")
    grid_patch = grid_layout_example()
    print(f"Grid patch created with {len(grid_patch._boxes)} objects")

    print("\nCreating flow layout example...")
    flow_patch = flow_layout_example()
    print(f"Flow patch created with {len(flow_patch._boxes)} objects")

    print("\nTesting object help...")
    help_patch, help_text, methods, attrs, inlets, outlets = object_help_example()
    print(
        f"umenu object: {methods} methods, {attrs} attributes, {inlets} inlets, {outlets} outlets"
    )

    print("\nTesting connection validation...")
    val_patch, error_occurred = connection_validation_example()
    print(f"Connection validation {'worked' if error_occurred else 'failed'}")
