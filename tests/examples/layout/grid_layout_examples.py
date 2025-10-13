#!/usr/bin/env python3
"""
Layout Examples: Grid Layout Manager
=====================================

Examples demonstrating grid layout with clustering and flow directions.

This example is used in:
- docs/source/user_guide/layout_managers.rst
"""

from py2max import Patcher


def create_basic_grid_horizontal():
    """Basic horizontal grid layout."""
    # Horizontal grid layout (default)
    p = Patcher("grid-horizontal.maxpat", layout="grid", flow_direction="horizontal")

    # Add objects - they'll be arranged left-to-right, wrapping when needed
    for i in range(12):
        p.add_textbox(f"cycle~ {440 + i * 55}")

    p.save()
    return p


def create_basic_grid_vertical():
    """Basic vertical grid layout."""
    # Vertical grid layout
    p = Patcher("grid-vertical.maxpat", layout="grid", flow_direction="vertical")

    # Objects arranged top-to-bottom, wrapping when needed
    for i in range(12):
        p.add_textbox(f"cycle~ {440 + i * 55}")

    p.save()
    return p


def create_clustered_grid():
    """Grid layout with connection-aware clustering."""
    # Enable clustering (default)
    p = Patcher("clustered-patch.maxpat", layout="grid", cluster_connected=True)

    # Create several signal chains
    chains = []
    for chain_num in range(3):
        # Create a signal processing chain
        osc = p.add_textbox(f"cycle~ {220 * (chain_num + 1)}")
        filter_obj = p.add_textbox("biquad~")
        delay = p.add_textbox("delay~ 500")
        gain = p.add_textbox("*~ 0.3")

        # Connect the chain
        p.add_line(osc, filter_obj)
        p.add_line(filter_obj, delay)
        p.add_line(delay, gain)

        chains.append([osc, filter_obj, delay, gain])

    # Add some control objects
    master_vol = p.add_floatbox(0.5, name="master_volume")
    output = p.add_textbox("ezdac~")

    # Connect all chains to output
    for chain in chains:
        p.add_line(chain[-1], output)  # Connect last object in each chain

    # Optimize layout - connected objects will be clustered together
    p.optimize_layout()
    p.save()
    return p


def create_mixed_layout():
    """Mixed layout with manual and automatic positioning."""
    from py2max.common import Rect

    p = Patcher("mixed-layout.maxpat", layout="grid")

    # Create manually positioned control section
    control_rect = Rect(50, 50, 200, 300)
    controls = []
    for i in range(5):
        ctrl = p.add_floatbox(
            i * 0.1,
            name=f"control{i}",
            patching_rect=Rect(control_rect.x, control_rect.y + i * 40, 60, 22),
        )
        controls.append(ctrl)

    # Let remaining objects use automatic layout
    processors = []
    for i in range(8):
        proc = p.add_textbox(f"biquad~ {100 + i * 200} 0.707")
        processors.append(proc)

    # Connect controls to processors
    for i, (ctrl, proc) in enumerate(zip(controls, processors)):
        p.add_line(ctrl, proc)

    # Only auto-positioned objects affected by optimization
    p.optimize_layout()
    p.save()
    return p


def create_large_clustered_patch():
    """Large patch demonstrating clustering performance."""
    p = Patcher("large-clustered.maxpat", layout="grid", cluster_connected=True)

    # Create multiple effect chains
    effect_chains = []
    for chain_id in range(6):
        # Input
        input_obj = p.add_textbox(f"cycle~ {110 * (chain_id + 1)}")

        # Effect chain
        eq = p.add_textbox("biquad~ 1000 0.707")
        distortion = p.add_textbox("tanh~")
        delay = p.add_textbox("delay~ 250")
        reverb = p.add_textbox("freeverb~")

        # Controls
        eq_freq = p.add_floatbox(1000 + chain_id * 500, name=f"eq_freq_{chain_id}")
        delay_time = p.add_floatbox(250 + chain_id * 50, name=f"delay_{chain_id}")

        # Connect effect chain
        p.add_line(input_obj, eq)
        p.add_line(eq, distortion)
        p.add_line(distortion, delay)
        p.add_line(delay, reverb)

        # Connect controls
        p.add_line(eq_freq, eq, outlet=0, inlet=1)
        p.add_line(delay_time, delay)

        effect_chains.append(
            {"input": input_obj, "output": reverb, "controls": [eq_freq, delay_time]}
        )

    # Master section
    master_mixer = p.add_textbox("+~")
    master_gain = p.add_floatbox(0.6, name="master_gain")
    master_mult = p.add_textbox("*~")
    output = p.add_textbox("ezdac~")

    # Connect all chains to master
    for chain in effect_chains:
        p.add_line(chain["output"], master_mixer)

    p.add_line(master_mixer, master_mult)
    p.add_line(master_gain, master_mult, outlet=0, inlet=1)
    p.add_line(master_mult, output)

    # Clustering will group connected components
    p.optimize_layout()
    p.save()
    return p


if __name__ == "__main__":
    # Create basic grid layouts
    horizontal_patch = create_basic_grid_horizontal()
    print(f"Created horizontal grid with {len(horizontal_patch._boxes)} objects")

    vertical_patch = create_basic_grid_vertical()
    print(f"Created vertical grid with {len(vertical_patch._boxes)} objects")

    # Create clustered layout
    clustered_patch = create_clustered_grid()
    print(f"Created clustered grid with {len(clustered_patch._boxes)} objects")

    # Create mixed layout
    mixed_patch = create_mixed_layout()
    print(f"Created mixed layout with {len(mixed_patch._boxes)} objects")

    # Create large clustered patch
    large_patch = create_large_clustered_patch()
    print(f"Created large clustered patch with {len(large_patch._boxes)} objects")
