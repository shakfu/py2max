#!/usr/bin/env python3
"""
API Reference Examples: Patcher Class
======================================

Examples demonstrating the Patcher API methods and features.

This example is used in:
- docs/source/api/py2max.rst
"""

from py2max import Patcher
from py2max.common import Rect


def demonstrate_patcher_creation():
    """Demonstrate different ways to create patchers."""
    # Basic patcher
    p1 = Patcher('basic.maxpat')

    # Patcher with layout configuration
    p2 = Patcher('grid-patch.maxpat', layout="grid", flow_direction="horizontal")
    p3 = Patcher('flow-patch.maxpat', layout="flow", flow_direction="vertical")

    # Patcher with validation settings
    p4 = Patcher('validated.maxpat', validate_connections=True)
    p5 = Patcher('unvalidated.maxpat', validate_connections=False)

    # Patcher with clustering
    p6 = Patcher('clustered.maxpat', layout="grid", cluster_connected=True)

    return [p1, p2, p3, p4, p5, p6]


def demonstrate_object_creation():
    """Demonstrate different object creation methods."""
    p = Patcher('objects-demo.maxpat')

    # Generic text-based objects
    osc = p.add_textbox('cycle~ 440')
    filter_obj = p.add_textbox('biquad~ 1000 0.707')
    gain = p.add_textbox('gain~')

    # UI objects
    button = p.add_message('bang')
    comment = p.add_comment('This is a comment')
    float_num = p.add_floatbox(440.0, name='frequency')
    int_num = p.add_intbox(127, name='velocity')

    # Container objects
    table = p.add_table('wavetable', data=[0.5, 0.3, -0.2, 0.8])
    coll = p.add_coll('sequence', data=["0, 60 127", "1, 64 100"])
    dict_obj = p.add_dict('patch-data')

    # Objects with custom positioning
    custom_obj = p.add_textbox('ezdac~', patching_rect=Rect(300, 200, 66, 22))

    # Subpatchers
    sub_box = p.add_subpatcher('voice-processor')
    sub = sub_box.subpatcher
    sub_inlet = sub.add_textbox('inlet~')
    sub_outlet = sub.add_textbox('outlet~')
    sub.add_line(sub_inlet, sub_outlet)

    p.save()
    return p


def demonstrate_connections():
    """Demonstrate different connection patterns."""
    p = Patcher('connections-demo.maxpat')

    # Create objects
    osc1 = p.add_textbox('cycle~ 220')
    osc2 = p.add_textbox('cycle~ 330')
    mixer = p.add_textbox('+~')
    filter_obj = p.add_textbox('biquad~')
    gain1 = p.add_textbox('*~ 0.5')
    gain2 = p.add_textbox('*~ 0.3')
    output = p.add_textbox('ezdac~')

    # Basic connections (outlet 0 to inlet 0)
    p.add_line(osc1, mixer)
    p.add_line(osc2, mixer)

    # Specific outlet/inlet connections
    p.add_line(mixer, filter_obj, outlet=0, inlet=0)

    # Multiple outputs from one object
    p.add_line(filter_obj, gain1)
    p.add_line(filter_obj, gain2)

    # Fan-in to single destination
    p.add_line(gain1, output)
    p.add_line(gain2, output)

    p.save()
    return p


def demonstrate_layout_management():
    """Demonstrate layout management features."""
    # Grid layout with clustering
    p1 = Patcher('layout-grid.maxpat', layout="grid", cluster_connected=True)

    # Create connected components
    for i in range(3):
        osc = p1.add_textbox(f'cycle~ {220 * (i + 1)}')
        gain = p1.add_textbox('*~ 0.3')
        p1.add_line(osc, gain)

    # Add unconnected objects
    p1.add_textbox('metro 500')
    p1.add_textbox('counter')

    p1.optimize_layout()
    p1.save()

    # Flow layout
    p2 = Patcher('layout-flow.maxpat', layout="flow", flow_direction="horizontal")

    input_obj = p2.add_textbox('adc~')
    proc1 = p2.add_textbox('biquad~')
    proc2 = p2.add_textbox('delay~ 250')
    output_obj = p2.add_textbox('dac~')

    p2.add_line(input_obj, proc1)
    p2.add_line(proc1, proc2)
    p2.add_line(proc2, output_obj)

    p2.optimize_layout()
    p2.save()

    return p1, p2


def demonstrate_file_operations():
    """Demonstrate file loading and saving."""
    # Create and save a patch
    p1 = Patcher('original.maxpat')
    osc = p1.add_textbox('cycle~ 440')
    gain = p1.add_textbox('gain~')
    output = p1.add_textbox('ezdac~')

    p1.add_line(osc, gain)
    p1.add_line(gain, output)
    p1.save()

    # Create a second patch (file loading can be complex)
    p2 = Patcher('modified.maxpat')
    osc2 = p2.add_textbox('cycle~ 330')
    delay = p2.add_textbox('delay~ 250')
    gain2 = p2.add_textbox('gain~')
    output2 = p2.add_textbox('ezdac~')

    # Connect with delay
    p2.add_line(osc2, delay)
    p2.add_line(delay, gain2)
    p2.add_line(gain2, output2)

    # Save modified version
    p2.save()

    return p1, p2


def demonstrate_patch_introspection():
    """Demonstrate patch introspection and information retrieval."""
    p = Patcher('introspection-demo.maxpat')

    # Add various objects
    osc = p.add_textbox('cycle~ 440')
    umenu = p.add_textbox('umenu')
    gain = p.add_textbox('gain~')

    p.add_line(osc, gain)

    # Object information
    print(f"Oscillator outlets: {osc.get_outlet_count()}")
    print(f"Gain inlets: {gain.get_inlet_count()}")

    # Get help for objects
    umenu_help = umenu.help()
    umenu_info = umenu.get_info()

    methods_count = len(umenu_info.get('methods', [])) if umenu_info else 0
    attrs_count = len(umenu_info.get('attributes', [])) if umenu_info else 0

    print(f"umenu methods: {methods_count}")
    print(f"umenu attributes: {attrs_count}")

    # Patch statistics
    print(f"Total objects: {len(p._boxes)}")
    print(f"Total connections: {len(p._lines)}")

    p.save()
    return p


if __name__ == '__main__':
    # Demonstrate patcher creation
    patchers = demonstrate_patcher_creation()
    print(f"Created {len(patchers)} different patcher configurations")

    # Demonstrate object creation
    objects_patch = demonstrate_object_creation()
    print(f"Created object demo with {len(objects_patch._boxes)} objects")

    # Demonstrate connections
    connections_patch = demonstrate_connections()
    print(f"Created connections demo with {len(connections_patch._lines)} connections")

    # Demonstrate layout management
    grid_patch, flow_patch = demonstrate_layout_management()
    print(f"Created layout demos: grid ({len(grid_patch._boxes)} objects), flow ({len(flow_patch._boxes)} objects)")

    # Demonstrate file operations
    original_patch, modified_patch = demonstrate_file_operations()
    print("Demonstrated file save and load operations")

    # Demonstrate introspection
    intro_patch = demonstrate_patch_introspection()
    print("Demonstrated patch introspection features")