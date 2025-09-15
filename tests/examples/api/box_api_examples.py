#!/usr/bin/env python3
"""
API Reference Examples: Box Class
==================================

Examples demonstrating the Box API methods and object introspection.

This example is used in:
- docs/source/api/py2max.rst
"""

from py2max import Patcher


def demonstrate_object_help():
    """Demonstrate object help and documentation system."""
    p = Patcher('help-demo.maxpat')

    # Create various Max objects
    cycle = p.add_textbox('cycle~ 440')
    umenu = p.add_textbox('umenu')
    biquad = p.add_textbox('biquad~')
    metro = p.add_textbox('metro 500')
    select = p.add_textbox('select 0 1 2 3')

    # Get formatted help for objects
    print("=== cycle~ Help ===")
    print(cycle.help())

    print("\n=== umenu Help ===")
    print(umenu.help())

    print("\n=== biquad~ Help ===")
    print(biquad.help())

    # Get structured object information
    cycle_info = cycle.get_info()
    umenu_info = umenu.get_info()

    cycle_methods = len(cycle_info.get('methods', [])) if cycle_info else 0
    cycle_attrs = len(cycle_info.get('attributes', [])) if cycle_info else 0
    umenu_methods = len(umenu_info.get('methods', [])) if umenu_info else 0
    umenu_attrs = len(umenu_info.get('attributes', [])) if umenu_info else 0

    print(f"\ncycle~ - Methods: {cycle_methods}, Attributes: {cycle_attrs}")
    print(f"umenu - Methods: {umenu_methods}, Attributes: {umenu_attrs}")

    p.save()
    return p


def demonstrate_inlet_outlet_introspection():
    """Demonstrate inlet/outlet introspection capabilities."""
    p = Patcher('io-introspection.maxpat')

    # Create objects with different I/O configurations
    objects = [
        ('cycle~', p.add_textbox('cycle~ 440')),
        ('biquad~', p.add_textbox('biquad~')),
        ('select', p.add_textbox('select 0 1 2 3 4')),
        ('gate', p.add_textbox('gate 4')),
        ('umenu', p.add_textbox('umenu')),
        ('flonum', p.add_floatbox(0.5)),
        ('metro', p.add_textbox('metro 500'))
    ]

    print("Object I/O Information:")
    print("=" * 50)

    for name, obj in objects:
        inlets = obj.get_inlet_count()
        outlets = obj.get_outlet_count()
        inlet_types = obj.get_inlet_types()
        outlet_types = obj.get_outlet_types()

        print(f"{name}:")
        print(f"  Inlets: {inlets} ({inlet_types})")
        print(f"  Outlets: {outlets} ({outlet_types})")
        print()

    p.save()
    return p


def demonstrate_object_properties():
    """Demonstrate object property access and modification."""
    p = Patcher('properties-demo.maxpat')

    # Create objects
    osc = p.add_textbox('cycle~ 440')
    gain = p.add_floatbox(0.5, name='gain_control')
    comment = p.add_comment('Signal processing chain')

    # Access object properties
    print("Object Properties:")
    print("=" * 30)

    print(f"Oscillator:")
    print(f"  ID: {osc.id}")
    print(f"  Max class: {osc.maxclass}")
    print(f"  Text: {osc.text}")
    print(f"  Position: {osc.patching_rect}")

    print(f"\nGain control:")
    print(f"  ID: {gain.id}")
    print(f"  Max class: {gain.maxclass}")
    print(f"  Text: {gain.text}")
    print(f"  Value: {getattr(gain, 'floatvalue', 'N/A')}")

    print(f"\nComment:")
    print(f"  ID: {comment.id}")
    print(f"  Max class: {comment.maxclass}")
    print(f"  Text: {comment.text}")

    p.save()
    return p


def demonstrate_object_validation():
    """Demonstrate object validation and error handling."""
    from py2max import InvalidConnectionError

    p = Patcher('validation-demo.maxpat', validate_connections=True)

    # Create objects
    cycle = p.add_textbox('cycle~ 440')
    gain = p.add_textbox('gain~')
    select = p.add_textbox('select 0 1 2')

    print("Connection Validation Tests:")
    print("=" * 40)

    # Valid connections
    try:
        p.add_line(cycle, gain)
        print("✓ Valid connection: cycle~ -> gain~")
    except InvalidConnectionError as e:
        print(f"✗ Unexpected error: {e}")

    # Invalid outlet test
    try:
        p.add_line(cycle, gain, outlet=5)  # cycle~ only has 1 outlet
        print("✗ Should have failed: invalid outlet")
    except InvalidConnectionError as e:
        print(f"✓ Caught invalid outlet: {e}")

    # Invalid inlet test
    try:
        p.add_line(cycle, select, inlet=10)  # select doesn't have inlet 10
        print("✗ Should have failed: invalid inlet")
    except InvalidConnectionError as e:
        print(f"✓ Caught invalid inlet: {e}")

    # Check object capabilities
    print(f"\nObject capabilities:")
    print(f"cycle~ - Inlets: {cycle.get_inlet_count()}, Outlets: {cycle.get_outlet_count()}")
    print(f"gain~ - Inlets: {gain.get_inlet_count()}, Outlets: {gain.get_outlet_count()}")
    print(f"select - Inlets: {select.get_inlet_count()}, Outlets: {select.get_outlet_count()}")

    p.save()
    return p


def demonstrate_object_types():
    """Demonstrate different object types and their characteristics."""
    p = Patcher('object-types.maxpat')

    # Signal objects (MSP)
    signal_objects = [
        ('cycle~', p.add_textbox('cycle~ 440')),
        ('biquad~', p.add_textbox('biquad~ 1000 0.707')),
        ('delay~', p.add_textbox('delay~ 500')),
        ('*~', p.add_textbox('*~')),
        ('dac~', p.add_textbox('dac~'))
    ]

    # Control objects (Max)
    control_objects = [
        ('metro', p.add_textbox('metro 500')),
        ('counter', p.add_textbox('counter 0 7')),
        ('select', p.add_textbox('select 0 1 2 3')),
        ('route', p.add_textbox('route note vel')),
        ('pack', p.add_textbox('pack i i'))
    ]

    # UI objects
    ui_objects = [
        ('flonum', p.add_floatbox(440.0)),
        ('button', p.add_message('bang')),
        ('comment', p.add_comment('Interface'))
    ]

    # Data objects
    data_objects = [
        ('table', p.add_table('wavetable')),
        ('coll', p.add_coll('sequence')),
        ('dict', p.add_dict('patch_data'))
    ]

    print("Object Type Analysis:")
    print("=" * 30)

    print("\nSignal Objects (MSP):")
    for name, obj in signal_objects:
        info = obj.get_info()
        print(f"  {name}: {obj.get_inlet_count()}in/{obj.get_outlet_count()}out")

    print("\nControl Objects (Max):")
    for name, obj in control_objects:
        print(f"  {name}: {obj.get_inlet_count()}in/{obj.get_outlet_count()}out")

    print("\nUI Objects:")
    for name, obj in ui_objects:
        print(f"  {name}: {obj.maxclass}")

    print("\nData Objects:")
    for name, obj in data_objects:
        print(f"  {name}: {obj.maxclass}")

    p.save()
    return p


if __name__ == '__main__':
    # Demonstrate object help
    help_patch = demonstrate_object_help()
    print(f"Created help demo with {len(help_patch._boxes)} objects")

    # Demonstrate I/O introspection
    io_patch = demonstrate_inlet_outlet_introspection()
    print(f"\nCreated I/O introspection demo with {len(io_patch._boxes)} objects")

    # Demonstrate object properties
    properties_patch = demonstrate_object_properties()
    print(f"\nCreated properties demo with {len(properties_patch._boxes)} objects")

    # Demonstrate validation
    validation_patch = demonstrate_object_validation()
    print(f"\nCreated validation demo with {len(validation_patch._boxes)} objects")

    # Demonstrate object types
    types_patch = demonstrate_object_types()
    print(f"\nCreated object types demo with {len(types_patch._boxes)} objects")