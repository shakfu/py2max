"""Tests for MatrixLayoutManager."""

import pytest
from py2max import Patcher
from py2max.layout import MatrixLayoutManager
from py2max.common import Rect


def test_layout_matrix_basic():
    """Test basic matrix layout functionality."""
    p = Patcher(layout="matrix")
    assert isinstance(p._layout_mgr, MatrixLayoutManager)

    # Test basic positioning
    rect = p._layout_mgr.get_relative_pos(Rect(0, 0, 66, 22))
    assert isinstance(rect, Rect)
    assert rect.x >= p._layout_mgr.pad
    assert rect.y >= p._layout_mgr.pad


def test_layout_matrix_inheritance():
    """Test that MatrixLayoutManager inherits object classification capabilities."""
    p = Patcher(layout="matrix")
    layout_mgr = p._layout_mgr

    # Should inherit object classification
    control = p.add_floatbox()
    generator = p.add_textbox('cycle~ 440')
    processor = p.add_textbox('gain~')
    output = p.add_textbox('ezdac~')

    # Test inherited classification
    assert layout_mgr._classify_object(control) == 0  # Controls
    assert layout_mgr._classify_object(generator) == 1  # Generators
    assert layout_mgr._classify_object(processor) == 2  # Processors
    assert layout_mgr._classify_object(output) == 3  # Outputs


def test_signal_chain_analysis():
    """Test signal chain detection and analysis."""
    p = Patcher(layout="matrix")

    # Create two separate signal chains
    # Chain 1
    metro1 = p.add_textbox('metro 500')  # Control
    osc1 = p.add_textbox('cycle~ 440')   # Generator
    gain1 = p.add_textbox('gain~')       # Processor
    dac1 = p.add_textbox('ezdac~')       # Output

    # Chain 2
    metro2 = p.add_textbox('metro 1000') # Control
    osc2 = p.add_textbox('saw~ 220')     # Generator
    filter2 = p.add_textbox('lores~')    # Processor
    dac2 = p.add_textbox('print')        # Output

    # Connect Chain 1
    p.add_line(metro1, osc1)
    p.add_line(osc1, gain1)
    p.add_line(gain1, dac1)

    # Connect Chain 2
    p.add_line(metro2, osc2)
    p.add_line(osc2, filter2)
    p.add_line(filter2, dac2)

    # Optimize layout
    p.optimize_layout()

    # Check signal chain analysis
    chain_info = p._layout_mgr.get_signal_chain_info()
    assert chain_info["num_chains"] == 2
    assert len(chain_info["chains"]) == 2

    # Verify each chain contains the right objects
    chains = chain_info["chains"]
    chain1_ids = set(chains[0])
    chain2_ids = set(chains[1])

    # Each chain should contain objects from that signal path
    assert metro1.id in chain1_ids or metro1.id in chain2_ids
    assert osc1.id in chain1_ids or osc1.id in chain2_ids
    assert metro2.id in chain1_ids or metro2.id in chain2_ids
    assert osc2.id in chain1_ids or osc2.id in chain2_ids


def test_layout_matrix_positioning():
    """Test that objects are positioned in matrix pattern."""
    p = Patcher("outputs/test_layout_matrix_positioning.maxpat",
        layout="matrix")

    # Create simple two-chain patch
    # Chain 1
    control1 = p.add_textbox('metro 500')
    gen1 = p.add_textbox('cycle~ 440')
    proc1 = p.add_textbox('gain~')
    out1 = p.add_textbox('ezdac~')

    # Chain 2
    control2 = p.add_textbox('loadbang')
    gen2 = p.add_textbox('noise~')
    proc2 = p.add_textbox('lores~')
    out2 = p.add_textbox('print')

    # Connect chains
    p.add_line(control1, gen1)
    p.add_line(gen1, proc1)
    p.add_line(proc1, out1)

    p.add_line(control2, gen2)
    p.add_line(gen2, proc2)
    p.add_line(proc2, out2)

    # Optimize layout
    p.optimize_layout()

    # Get positions of objects from chain 1
    c1_y = control1.patching_rect.y
    g1_y = gen1.patching_rect.y
    p1_y = proc1.patching_rect.y
    o1_y = out1.patching_rect.y

    # Get positions of objects from chain 2
    c2_y = control2.patching_rect.y
    g2_y = gen2.patching_rect.y
    p2_y = proc2.patching_rect.y
    o2_y = out2.patching_rect.y

    # Objects of same type should be in same row (similar y coordinates)
    assert abs(c1_y - c2_y) < 50  # Controls in same row
    assert abs(g1_y - g2_y) < 50  # Generators in same row
    assert abs(p1_y - p2_y) < 50  # Processors in same row
    assert abs(o1_y - o2_y) < 50  # Outputs in same row

    # Objects should be ordered by category vertically
    assert c1_y < g1_y < p1_y < o1_y  # Chain 1 vertical order
    assert c2_y < g2_y < p2_y < o2_y  # Chain 2 vertical order

    p.save()


def test_matrix_empty_patch():
    """Test matrix layout with empty patch."""
    p = Patcher(layout="matrix")
    p.optimize_layout()
    assert len(p._objects) == 0

    chain_info = p._layout_mgr.get_signal_chain_info()
    assert chain_info["num_chains"] == 0
    assert chain_info["chains"] == []


def test_matrix_single_object():
    """Test matrix layout with single object."""
    p = Patcher(layout="matrix")
    osc = p.add_textbox('cycle~ 440')
    p.optimize_layout()

    chain_info = p._layout_mgr.get_signal_chain_info()
    assert chain_info["num_chains"] == 1
    assert len(chain_info["chains"][0]) == 1
    assert osc.id in chain_info["chains"][0]


def test_matrix_disconnected_objects():
    """Test matrix layout with disconnected objects."""
    p = Patcher(layout="matrix")

    # Add objects without connections
    control = p.add_textbox('metro 500')
    gen = p.add_textbox('cycle~ 440')
    proc = p.add_textbox('gain~')
    out = p.add_textbox('ezdac~')

    p.optimize_layout()

    # Should create separate chains for disconnected objects
    chain_info = p._layout_mgr.get_signal_chain_info()
    assert chain_info["num_chains"] >= 1

    # All objects should be assigned to chains
    all_objects_in_chains = set()
    for chain in chain_info["chains"]:
        all_objects_in_chains.update(chain)

    assert control.id in all_objects_in_chains
    assert gen.id in all_objects_in_chains
    assert proc.id in all_objects_in_chains
    assert out.id in all_objects_in_chains


def test_matrix_complex_connections():
    """Test matrix layout with complex connection patterns."""
    p = Patcher(layout="matrix")

    # Create a more complex patch with branching
    metro = p.add_textbox('metro 500')
    osc1 = p.add_textbox('cycle~ 440')
    osc2 = p.add_textbox('saw~ 220')
    mixer = p.add_textbox('gain~')
    filter = p.add_textbox('lores~')
    dac = p.add_textbox('ezdac~')

    # Create branching connections
    p.add_line(metro, osc1)
    p.add_line(metro, osc2)  # Metro drives both oscillators
    p.add_line(osc1, mixer)
    p.add_line(osc2, mixer)  # Both oscillators to mixer
    p.add_line(mixer, filter)
    p.add_line(filter, dac)

    p.optimize_layout()

    chain_info = p._layout_mgr.get_signal_chain_info()

    # Should handle the branching appropriately
    assert chain_info["num_chains"] >= 1
    assert len(chain_info["chains"]) >= 1

    # All objects should be assigned
    all_objects_in_chains = set()
    for chain in chain_info["chains"]:
        all_objects_in_chains.update(chain)

    expected_objects = {metro.id, osc1.id, osc2.id, mixer.id, filter.id, dac.id}
    assert expected_objects.issubset(all_objects_in_chains)


def test_layout_matrix_spacing():
    """Test matrix layout spacing parameters."""
    p1 = Patcher(layout="matrix")
    p1._layout_mgr.row_spacing = 50.0
    p1._layout_mgr.column_spacing = 100.0

    p2 = Patcher(layout="matrix")
    p2._layout_mgr.row_spacing = 150.0
    p2._layout_mgr.column_spacing = 200.0

    # Add same structure to both
    for p in [p1, p2]:
        c1 = p.add_textbox('metro 500')
        g1 = p.add_textbox('cycle~ 440')
        c2 = p.add_textbox('loadbang')
        g2 = p.add_textbox('noise~')

        p.add_line(c1, g1)
        p.add_line(c2, g2)
        p.optimize_layout()

    # Compare spacing
    p1_objects = list(p1._objects.values())
    p2_objects = list(p2._objects.values())

    # p2 should have wider spacing
    p1_max_x = max(obj.patching_rect.x for obj in p1_objects)
    p2_max_x = max(obj.patching_rect.x for obj in p2_objects)
    assert p2_max_x >= p1_max_x

    p1_max_y = max(obj.patching_rect.y for obj in p1_objects)
    p2_max_y = max(obj.patching_rect.y for obj in p2_objects)
    assert p2_max_y >= p1_max_y


def test_matrix_signal_chain_info():
    """Test the get_signal_chain_info method."""
    p = Patcher(layout="matrix")

    metro = p.add_textbox('metro 500')
    osc = p.add_textbox('cycle~ 440')
    gain = p.add_textbox('gain~')

    p.add_line(metro, osc)
    p.add_line(osc, gain)
    p.optimize_layout()

    info = p._layout_mgr.get_signal_chain_info()

    assert "num_chains" in info
    assert "chains" in info
    assert "chain_assignments" in info
    assert "matrix_size" in info

    assert isinstance(info["num_chains"], int)
    assert isinstance(info["chains"], list)
    assert isinstance(info["chain_assignments"], dict)
    assert isinstance(info["matrix_size"], tuple)
    assert len(info["matrix_size"]) == 2


def test_matrix_multiple_objects_same_category():
    """Test matrix layout with multiple objects of same category in one chain."""
    p = Patcher(layout="matrix")

    # Chain with multiple processors
    metro = p.add_textbox('metro 500')
    osc = p.add_textbox('cycle~ 440')
    gain1 = p.add_textbox('gain~')
    gain2 = p.add_textbox('gain~')
    filter = p.add_textbox('lores~')
    dac = p.add_textbox('ezdac~')

    # Linear chain
    p.add_line(metro, osc)
    p.add_line(osc, gain1)
    p.add_line(gain1, gain2)
    p.add_line(gain2, filter)
    p.add_line(filter, dac)

    p.optimize_layout()

    # Should handle multiple objects of same category in one chain
    chain_info = p._layout_mgr.get_signal_chain_info()
    assert chain_info["num_chains"] >= 1

    # All objects should be positioned
    for obj in [metro, osc, gain1, gain2, filter, dac]:
        assert obj.patching_rect.x >= p._layout_mgr.pad
        assert obj.patching_rect.y >= p._layout_mgr.pad


if __name__ == "__main__":
    # Run basic tests
    test_layout_matrix_basic()
    test_layout_matrix_inheritance()
    test_signal_chain_analysis()
    test_matrix_positioning()
    print("All matrix layout tests passed!")