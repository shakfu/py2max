#!/usr/bin/env python3
"""
Tutorial 3: Interactive Controller
===================================

Create an interactive MIDI controller interface with 8 CC channels and preset management.

This example is used in:
- docs/source/user_guide/tutorial.rst
"""

from py2max import Patcher


def create_midi_controller():
    """Create an interactive MIDI controller interface."""
    # Create controller with automatic layout
    p = Patcher("midi-controller.maxpat", layout="grid", cluster_connected=True)

    # MIDI input
    midi_in = p.add_textbox("ctlin")

    # Create 8 controller channels
    controllers = []
    for cc_num in range(1, 9):  # CC 1-8
        # CC number selection
        cc_select = p.add_intparam(f"CC{cc_num}", initial=cc_num)

        # Route specific CC
        route = p.add_textbox(f"route {cc_num}")

        # Scale 0-127 to 0.0-1.0
        scale = p.add_textbox("/ 127.")

        # Value display
        value_display = p.add_floatparam(f"value{cc_num}", initial=0.0)

        # Connect chain
        p.add_line(midi_in, route)
        p.add_line(route, scale)
        p.add_line(scale, value_display)

        controllers.append(
            {"cc": cc_select, "route": route, "scale": scale, "value": value_display}
        )

    # Add preset management
    preset_slot = p.add_intparam("preset_slot", initial=1)
    preset_store = p.add_message("store $1")
    preset_recall = p.add_message("recall $1")
    preset_obj = p.add_textbox("preset")

    p.add_line(preset_slot, preset_store)
    p.add_line(preset_slot, preset_recall)
    p.add_line(preset_store, preset_obj)
    p.add_line(preset_recall, preset_obj)

    # preset's left outlet names the objects whose values it stores
    for ctrl in controllers:
        p.add_line(preset_obj, ctrl["value"])

    # Add comments for clarity
    p.add_comment("MIDI Controller Interface")
    p.add_comment("Controllers 1-8")
    p.add_comment("Preset Management")

    p.optimize_layout()
    p.save()

    return p


if __name__ == "__main__":
    patch = create_midi_controller()
    print(f"Created MIDI controller with {len(patch._boxes)} objects")
    print("Patch saved as 'midi-controller.maxpat'")
