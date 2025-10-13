from py2max import Patcher
from py2max.layout import GridLayoutManager
from py2max.layout import HorizontalLayoutManager
from py2max.layout import VerticalLayoutManager


def example(p, optimize_layout=False):
    fbox = p.add_floatbox
    ibox = p.add_intbox
    tbox = p.add_textbox
    link = p.add_line

    # objects
    freq1 = fbox()
    freq2 = fbox()
    phase = fbox()
    osc1 = tbox("cycle~")
    osc2 = tbox("cycle~")
    amp1 = fbox()
    amp2 = fbox()
    mul1 = tbox("*~")
    mul2 = tbox("*~")
    add1 = tbox("+~")
    dac = tbox("ezdac~")
    scop = tbox("scope~")
    scp1 = ibox()
    scp2 = ibox()

    # lines
    link(freq1, osc1)
    link(osc1, mul1)
    link(mul1, add1)
    link(amp1, mul1, inlet=1)
    link(freq2, osc2)
    link(phase, osc2, inlet=1)
    link(osc2, mul2)
    link(amp2, mul2, inlet=1)
    link(mul2, add1, inlet=1)
    link(add1, dac)
    link(add1, dac, inlet=1)
    link(add1, scop)
    link(scp1, scop)
    link(scp2, scop, inlet=1)

    if optimize_layout:
        p.optimize_layout()
    p.save()


def test_layout_horizontal():
    p = Patcher("outputs/test_layout_builtins_horizontal.maxpat", layout="horizontal")
    example(p)


def test_layout_vertical():
    p = Patcher("outputs/test_layout_builtins_vertical.maxpat", layout="vertical")
    example(p)


def test_layout_flow_horizontal():
    p = Patcher("outputs/test_layout_builtins_flow_horizontal.maxpat", layout="flow")
    example(p)


def test_layout_flow_vertical():
    p = Patcher(
        "outputs/test_layout_builtins_flow_vertical.maxpat",
        layout="flow",
        flow_direction="vertical",
    )
    example(p)


def test_layout_grid_horizontal():
    """Test new GridLayoutManager with horizontal flow direction."""
    p = Patcher(
        "outputs/test_layout_builtins_grid_horizontal.maxpat",
        layout="grid",
        flow_direction="horizontal",
        cluster_connected=False,
    )
    example(p)

    # Verify layout manager type
    assert isinstance(p._layout_mgr, GridLayoutManager)
    assert p._layout_mgr.flow_direction == "horizontal"
    # assert p._layout_mgr.cluster_connected == False


def test_layout_grid_horizontal_clustered():
    """Test new GridLayoutManager with horizontal flow direction."""
    p = Patcher(
        "outputs/test_layout_builtins_grid_horizontal_clustered.maxpat",
        layout="grid",
        flow_direction="horizontal",
        cluster_connected=True,
    )
    example(p, optimize_layout=True)

    # Verify layout manager type
    assert isinstance(p._layout_mgr, GridLayoutManager)
    assert p._layout_mgr.flow_direction == "horizontal"
    assert p._layout_mgr.cluster_connected == True


def test_layout_grid_vertical():
    """Test new GridLayoutManager with vertical flow direction."""
    p = Patcher(
        "outputs/test_layout_builtins_grid_vertical.maxpat",
        layout="grid",
        flow_direction="vertical",
        cluster_connected=False,
    )
    example(p)

    # Verify layout manager type
    assert isinstance(p._layout_mgr, GridLayoutManager)
    assert p._layout_mgr.flow_direction == "vertical"
    assert p._layout_mgr.cluster_connected == False


def test_layout_grid_vertical_clustered():
    """Test new GridLayoutManager with vertical flow direction."""
    p = Patcher(
        "outputs/test_layout_builtins_grid_vertical_clustered.maxpat",
        layout="grid",
        flow_direction="vertical",
        cluster_connected=True,
    )
    example(p, optimize_layout=True)

    # Verify layout manager type
    assert isinstance(p._layout_mgr, GridLayoutManager)
    assert p._layout_mgr.flow_direction == "vertical"
    assert p._layout_mgr.cluster_connected == True


def test_layout_grid_default():
    """Test new GridLayoutManager with default (horizontal) flow direction."""
    p = Patcher("outputs/test_layout_builtins_grid_default.maxpat", layout="grid")
    example(p)

    # Verify layout manager type and default direction
    assert isinstance(p._layout_mgr, GridLayoutManager)
    assert p._layout_mgr.flow_direction == "horizontal"  # Should default to horizontal


def test_backward_compatibility_horizontal():
    """Test that legacy horizontal layout still works (backward compatibility)."""
    p = Patcher(
        "outputs/test_layout_builtins_backward_horizontal.maxpat", layout="horizontal"
    )
    example(p)

    # Verify it still creates a HorizontalLayoutManager (legacy alias)
    assert isinstance(p._layout_mgr, HorizontalLayoutManager)


def test_backward_compatibility_vertical():
    """Test that legacy vertical layout still works (backward compatibility)."""
    p = Patcher(
        "outputs/test_layout_builtins_backward_vertical.maxpat", layout="vertical"
    )
    example(p)

    # Verify it still creates a VerticalLayoutManager (legacy alias)
    assert isinstance(p._layout_mgr, VerticalLayoutManager)


def test_grid_clustering_horizontal():
    """Test GridLayoutManager clustering functionality with horizontal layout."""
    p = Patcher(
        "outputs/test_grid_clustering_horizontal.maxpat",
        layout="grid",
        flow_direction="horizontal",
        cluster_connected=True,
    )

    # Create two separate clusters of connected objects
    # Cluster 1: osc1 -> gain1 -> filter1
    osc1 = p.add_textbox("cycle~ 440")
    gain1 = p.add_textbox("gain~")
    filter1 = p.add_textbox("lores~")

    # Cluster 2: osc2 -> gain2 -> filter2
    osc2 = p.add_textbox("cycle~ 220")
    gain2 = p.add_textbox("gain~")
    filter2 = p.add_textbox("lores~")

    # Isolated object (no connections)
    dac = p.add_textbox("ezdac~")

    # Store initial positions before clustering
    initial_positions = {
        "osc1": (osc1.patching_rect.x, osc1.patching_rect.y),
        "osc2": (osc2.patching_rect.x, osc2.patching_rect.y),
    }

    # Create connections for cluster 1
    p.add_line(osc1, gain1)
    p.add_line(gain1, filter1)

    # Create connections for cluster 2
    p.add_line(osc2, gain2)
    p.add_line(gain2, filter2)

    # Optimize layout to cluster connected objects
    p.optimize_layout()

    # Get positions after clustering
    osc1_pos = osc1.patching_rect
    gain1_pos = gain1.patching_rect
    filter1_pos = filter1.patching_rect
    osc2_pos = osc2.patching_rect
    gain2_pos = gain2.patching_rect
    filter2_pos = filter2.patching_rect
    dac_pos = dac.patching_rect

    # Verify that clustering moved objects from their initial positions
    final_osc1_pos = (osc1_pos.x, osc1_pos.y)
    final_osc2_pos = (osc2_pos.x, osc2_pos.y)

    # At least one object should have moved (clustering should change positions)
    positions_changed = (
        initial_positions["osc1"] != final_osc1_pos
        or initial_positions["osc2"] != final_osc2_pos
    )
    assert positions_changed, "Clustering should change object positions"

    # Verify objects within the same cluster are relatively close
    # (within the same cluster area)
    cluster1_objects = [osc1_pos, gain1_pos, filter1_pos]
    cluster2_objects = [osc2_pos, gain2_pos, filter2_pos]

    # Calculate cluster bounding boxes
    cluster1_min_x = min(pos.x for pos in cluster1_objects)
    cluster1_max_x = max(pos.x for pos in cluster1_objects)
    cluster2_min_x = min(pos.x for pos in cluster2_objects)
    cluster2_max_x = max(pos.x for pos in cluster2_objects)

    # Clusters should be separated (non-overlapping in x-axis for horizontal layout)
    clusters_separated = (
        cluster1_max_x < cluster2_min_x or cluster2_max_x < cluster1_min_x
    )
    assert clusters_separated, "Different clusters should be spatially separated"

    # Verify objects have been positioned (not all at origin)
    positions = [
        osc1_pos,
        gain1_pos,
        filter1_pos,
        osc2_pos,
        gain2_pos,
        filter2_pos,
        dac_pos,
    ]
    unique_positions = set((pos.x, pos.y) for pos in positions)
    assert len(unique_positions) > 1, "Objects should have different positions"

    # Verify layout manager has clustering enabled
    assert isinstance(p._layout_mgr, GridLayoutManager)
    assert p._layout_mgr.cluster_connected == True

    p.save()


def test_grid_clustering_vertical():
    """Test GridLayoutManager clustering functionality with vertical layout."""
    p = Patcher(
        "outputs/test_grid_clustering_vertical.maxpat",
        layout="grid",
        flow_direction="vertical",
        cluster_connected=True,
    )

    # Create a linear chain of connected objects
    freq = p.add_floatbox()
    osc = p.add_textbox("cycle~ 440")
    gain = p.add_textbox("gain~")
    filter_obj = p.add_textbox("lores~")
    output = p.add_textbox("ezdac~")

    # Create another isolated group
    lfo = p.add_textbox("cycle~ 2")
    amp_mod = p.add_textbox("*~")

    # Connect the main chain
    p.add_line(freq, osc)
    p.add_line(osc, gain)
    p.add_line(gain, filter_obj)
    p.add_line(filter_obj, output)

    # Connect the modulation chain
    p.add_line(lfo, amp_mod)

    # Optimize layout
    p.optimize_layout()

    # Verify objects have been positioned
    positions = []
    for box in p._boxes:
        pos = box.patching_rect
        positions.append((pos.x, pos.y))
        assert 0 <= pos.x <= p.width
        assert 0 <= pos.y <= p.height

    # Verify different positions
    unique_positions = set(positions)
    assert len(unique_positions) > 1, "Objects should have different positions"

    # Verify clustering is enabled
    assert p._layout_mgr.cluster_connected == True

    p.save()


def test_grid_clustering_disabled():
    """Test GridLayoutManager with clustering disabled."""
    p = Patcher(
        "outputs/test_grid_clustering_disabled.maxpat",
        layout="grid",
        cluster_connected=False,
    )

    # Create connected objects
    osc = p.add_textbox("cycle~ 440")
    gain = p.add_textbox("gain~")
    dac = p.add_textbox("ezdac~")

    p.add_line(osc, gain)
    p.add_line(gain, dac)

    # Call optimize_layout - should have no effect when clustering is disabled
    p.optimize_layout()

    # Verify clustering is disabled
    assert p._layout_mgr.cluster_connected == False

    # Objects should still be positioned (just not clustered)
    positions = []
    for box in p._boxes:
        pos = box.patching_rect
        positions.append((pos.x, pos.y))
        assert 0 <= pos.x <= p.width
        assert 0 <= pos.y <= p.height

    unique_positions = set(positions)
    assert len(unique_positions) > 1, "Objects should still have different positions"

    p.save()


def test_grid_clustering_comparison():
    """Direct comparison test showing difference between clustered and unclustered layouts."""

    def create_test_patch(clustered: bool, suffix: str):
        """Helper to create identical patches with/without clustering."""
        p = Patcher(
            f"outputs/test_grid_clustering_comparison_{suffix}.maxpat",
            layout="grid",
            cluster_connected=clustered,
        )

        # Create connected objects in a clear chain
        osc1 = p.add_textbox("cycle~ 440")
        gain1 = p.add_textbox("gain~")
        filter1 = p.add_textbox("lores~")

        # Another separate chain
        osc2 = p.add_textbox("cycle~ 220")
        gain2 = p.add_textbox("gain~")
        dac = p.add_textbox("ezdac~")

        # Connect the chains
        p.add_line(osc1, gain1)
        p.add_line(gain1, filter1)
        p.add_line(osc2, gain2)
        p.add_line(gain2, dac)

        # Apply optimization if clustering is enabled
        if clustered:
            p.optimize_layout()

        p.save()

        # Return positions for comparison
        return {
            "osc1": (osc1.patching_rect.x, osc1.patching_rect.y),
            "gain1": (gain1.patching_rect.x, gain1.patching_rect.y),
            "filter1": (filter1.patching_rect.x, filter1.patching_rect.y),
            "osc2": (osc2.patching_rect.x, osc2.patching_rect.y),
            "gain2": (gain2.patching_rect.x, gain2.patching_rect.y),
            "dac": (dac.patching_rect.x, dac.patching_rect.y),
        }

    # Create both versions
    unclustered_positions = create_test_patch(clustered=False, suffix="unclustered")
    clustered_positions = create_test_patch(clustered=True, suffix="clustered")

    # Verify that positions are different between clustered and unclustered
    differences_found = 0
    for obj_name in unclustered_positions:
        if unclustered_positions[obj_name] != clustered_positions[obj_name]:
            differences_found += 1

    # At least half the objects should have different positions
    assert differences_found >= 3, (
        f"Clustering should significantly change positions (only {differences_found} objects moved)"
    )

    # Print positions for manual verification (useful for debugging)
    # print(f"Unclustered: {unclustered_positions}")
    # print(f"Clustered: {clustered_positions}")
    # print(f"Objects moved: {differences_found}/6")
