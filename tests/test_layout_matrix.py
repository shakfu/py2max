"""Tests for MatrixLayoutManager in both columnar and matrix modes."""

import pytest
from py2max import Patcher
from py2max.layout import MatrixLayoutManager
from py2max.common import Rect
import py2max.category as category


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


def test_layout_columnar_basic():
    """Test basic columnar layout functionality."""
    p = Patcher(layout="matrix", flow_direction="column")
    assert isinstance(p._layout_mgr, MatrixLayoutManager)
    assert p._layout_mgr.flow_direction == "column"

    # Test basic positioning
    rect = p._layout_mgr.get_relative_pos(Rect(0, 0, 66, 22))
    assert isinstance(rect, Rect)
    assert rect.x >= p._layout_mgr.pad
    assert rect.y >= p._layout_mgr.pad


def test_unknown_object_inference():
    """Test inference of unknown object types."""
    p = Patcher(layout="matrix", flow_direction="column")
    layout_mgr = p._layout_mgr

    # Test audio object inference
    audio_obj = p.add_textbox('customfilter~ 1000')
    assert layout_mgr._classify_object(audio_obj) == 2  # Should be processors

    # Test generator-like audio object
    gen_obj = p.add_textbox('customosc~ 220')
    assert layout_mgr._classify_object(gen_obj) == 1  # Should be generators

    # Test control-like object
    ctrl_obj = p.add_textbox('customslider')
    assert layout_mgr._classify_object(ctrl_obj) == 0  # Should be controls

    # Test output-like object
    out_obj = p.add_textbox('customdac~')
    assert layout_mgr._classify_object(out_obj) == 3  # Should be outputs


def test_layout_columnar_with_connections():
    """Test columnar layout with connected objects."""
    p = Patcher("outputs/test_layout_columnar_with_connections.maxpat", layout="matrix", flow_direction="column")

    # Create a typical signal chain
    metro = p.add_textbox('metro 500')  # Control
    osc = p.add_textbox('cycle~ 440')   # Generator
    gain = p.add_textbox('gain~')       # Processor
    dac = p.add_textbox('ezdac~')       # Output

    # Connect them in signal chain order
    p.add_line(metro, osc)
    p.add_line(osc, gain)
    p.add_line(gain, dac)

    # Optimize layout
    p.optimize_layout()

    # Check that objects are positioned in columns
    metro_x = metro.patching_rect.x
    osc_x = osc.patching_rect.x
    gain_x = gain.patching_rect.x
    dac_x = dac.patching_rect.x

    # Objects should be arranged left-to-right by function
    assert metro_x < osc_x < gain_x < dac_x

    p.save()


def test_layout_columnar_multiple_objects():
    """Test columnar layout with multiple objects per column."""
    p = Patcher("outputs/test_layout_columnar_multiple_objects.maxpat",
        layout="matrix", flow_direction="column")

    # Add multiple objects to same categories
    metro1 = p.add_textbox('metro 500')
    metro2 = p.add_textbox('metro 1000')

    osc1 = p.add_textbox('cycle~ 440')
    osc2 = p.add_textbox('saw~ 220')

    gain1 = p.add_textbox('gain~')
    gain2 = p.add_textbox('gain~')

    dac = p.add_textbox('ezdac~')

    # Connect in parallel chains
    p.add_line(metro1, osc1)
    p.add_line(metro2, osc2)
    p.add_line(osc1, gain1)
    p.add_line(osc2, gain2)
    p.add_line(gain1, dac)
    p.add_line(gain2, dac)

    # Optimize layout
    p.optimize_layout()

    # Check that objects in same column have similar x positions
    assert abs(metro1.patching_rect.x - metro2.patching_rect.x) < 100
    assert abs(osc1.patching_rect.x - osc2.patching_rect.x) < 100
    assert abs(gain1.patching_rect.x - gain2.patching_rect.x) < 100

    # Check vertical ordering within columns
    assert metro1.patching_rect.y != metro2.patching_rect.y
    assert osc1.patching_rect.y != osc2.patching_rect.y

    # save
    p.save()


def test_layout_columnar_signal_flow_refinement():
    """Test that signal flow analysis refines column assignments."""
    p = Patcher("outputs/test_layout_columnar_signal_flow_refinement.maxpat",
        layout="matrix", flow_direction="column")

    # Create objects where initial classification might be refined by connections
    osc = p.add_textbox('cycle~ 440')
    unknown_audio = p.add_textbox('unknown~ 100')  # Will be classified as processor initially
    dac = p.add_textbox('ezdac~')

    # Connect in generator->processor->output pattern
    p.add_line(osc, unknown_audio)
    p.add_line(unknown_audio, dac)

    # Optimize layout (includes signal flow refinement)
    p.optimize_layout()

    # unknown_audio should be positioned between osc and dac
    assert osc.patching_rect.x < unknown_audio.patching_rect.x < dac.patching_rect.x


def test_layout_columnar_column_spacing():
    """Test that column spacing parameter works correctly."""
    p1 = Patcher("outputs/test_layout_columnar_column_spacing.maxpat",
        layout="matrix", flow_direction="column")
    p1._layout_mgr.column_spacing = 50.0

    p2 = Patcher(layout="matrix", flow_direction="column")
    p2._layout_mgr.column_spacing = 200.0

    # Add same objects to both
    for p in [p1, p2]:
        p.add_textbox('metro 500')
        p.add_textbox('cycle~ 440')
        p.optimize_layout()

    # p2 should have wider spacing between columns
    p1_metro = list(p1._objects.values())[0]
    p1_osc = list(p1._objects.values())[1]
    p2_metro = list(p2._objects.values())[0]
    p2_osc = list(p2._objects.values())[1]

    p1_spacing = p1_osc.patching_rect.x - p1_metro.patching_rect.x
    p2_spacing = p2_osc.patching_rect.x - p2_metro.patching_rect.x

    assert p2_spacing > p1_spacing


def test_layout_columnar_empty_patch():
    """Test columnar layout with empty patch."""
    p = Patcher(layout="matrix", flow_direction="column")

    # Should not crash with empty patch
    p.optimize_layout()
    assert len(p._objects) == 0


def test_layout_columnar_single_object():
    """Test columnar layout with single object."""
    p = Patcher("outputs/test_layout_columnar_single_object.maxpat", layout="matrix", flow_direction="column")

    osc = p.add_textbox('cycle~ 440')
    p.optimize_layout()

    # Should position object correctly
    assert osc.patching_rect.x >= p._layout_mgr.pad
    assert osc.patching_rect.y >= p._layout_mgr.pad


def test_object_category_sets():
    """Test that object category sets contain expected objects."""
    # Test a few key objects from each category
    assert 'flonum' in category.CONTROL_OBJECTS
    assert 'metro' in category.CONTROL_OBJECTS
    assert 'button' in category.CONTROL_OBJECTS

    assert 'cycle~' in category.GENERATOR_OBJECTS
    assert 'noise~' in category.GENERATOR_OBJECTS
    assert 'saw~' in category.GENERATOR_OBJECTS

    assert 'gain~' in category.PROCESSOR_OBJECTS
    assert 'lores~' in category.PROCESSOR_OBJECTS
    assert 'delay~' in category.PROCESSOR_OBJECTS

    assert 'dac~' in category.OUTPUT_OBJECTS
    assert 'ezdac~' in category.OUTPUT_OBJECTS
    assert 'print' in category.OUTPUT_OBJECTS

    # Test INPUT_OBJECTS
    assert 'adc~' in category.INPUT_OBJECTS
    assert 'inlet' in category.INPUT_OBJECTS
    assert 'receive' in category.INPUT_OBJECTS
    assert 'bendin' in category.INPUT_OBJECTS
    assert 'ctlin' in category.INPUT_OBJECTS
    assert 'midiin' in category.INPUT_OBJECTS


def test_input_objects_classification():
    """Test that INPUT_OBJECTS are properly classified as category 0 (Controls/Inputs)."""
    p = Patcher(layout="matrix", flow_direction="column")
    layout_mgr = p._layout_mgr

    # Test that input objects are classified as category 0
    test_objects = [
        p.add_textbox('adc~'),      # Audio input
        p.add_textbox('inlet'),     # Generic inlet
        p.add_textbox('receive test'),  # Message receive
        p.add_textbox('bendin'),    # MIDI bend input
        p.add_textbox('ctlin'),     # MIDI controller input
        p.add_textbox('midiin')     # MIDI input
    ]

    for obj in test_objects:
        category = layout_mgr._classify_object(obj)
        assert category == 0, f"Input object {obj.maxclass} should be classified as category 0, got {category}"


def test_input_objects_priority():
    """Test that INPUT_OBJECTS have priority over CONTROL_OBJECTS in classification."""
    p = Patcher(layout="matrix", flow_direction="column")
    layout_mgr = p._layout_mgr

    # Objects that are in both INPUT_OBJECTS and CONTROL_OBJECTS
    overlapping_objects = ['bendin', 'ctlin', 'key', 'keyup', 'midiin', 'mousestate', 'notein', 'pgmin', 'touchin']

    for obj_name in overlapping_objects:
        obj = p.add_textbox(obj_name)
        category = layout_mgr._classify_object(obj)
        assert category == 0, f"Overlapping object {obj_name} should be classified as category 0 (inputs take priority)"


def test_row_spacing_property():
    """Test that row_spacing property works correctly and updates dimension_spacing."""
    p = Patcher(layout="matrix", flow_direction="column")
    layout_mgr = p._layout_mgr

    # Test initial value
    initial_spacing = layout_mgr.dimension_spacing
    assert layout_mgr.row_spacing == initial_spacing

    # Test setting row_spacing updates dimension_spacing
    layout_mgr.row_spacing = 150.0
    assert layout_mgr.dimension_spacing == 150.0
    assert layout_mgr.row_spacing == 150.0

    # Test that column_spacing and row_spacing are synchronized
    layout_mgr.column_spacing = 200.0
    assert layout_mgr.row_spacing == 200.0
    assert layout_mgr.dimension_spacing == 200.0


def test_sort_objects_in_column():
    """Test internal sorting of objects within a column."""
    p = Patcher(layout="matrix", flow_direction="column")

    # Create a chain within the same column (processors)
    obj1 = p.add_textbox('gain~')
    obj2 = p.add_textbox('lores~')
    obj3 = p.add_textbox('delay~')

    # Connect them in a chain
    p.add_line(obj1, obj2)
    p.add_line(obj2, obj3)

    # Test sorting function
    obj_ids = [obj1.id, obj2.id, obj3.id]
    sorted_ids = p._layout_mgr._sort_objects_in_column(obj_ids)

    # Should maintain signal flow order
    assert len(sorted_ids) == 3
    assert obj1.id in sorted_ids
    assert obj2.id in sorted_ids
    assert obj3.id in sorted_ids


def test_matrix_mode_basic():
    """Test basic matrix layout functionality (flow_direction='row')."""
    p = Patcher(layout="matrix", flow_direction="row")
    assert isinstance(p._layout_mgr, MatrixLayoutManager)
    assert p._layout_mgr.flow_direction == "row"

    # Test basic positioning
    rect = p._layout_mgr.get_relative_pos(Rect(0, 0, 66, 22))
    assert isinstance(rect, Rect)
    assert rect.x >= p._layout_mgr.pad
    assert rect.y >= p._layout_mgr.pad


def test_matrix_mode_signal_chains():
    """Test matrix mode with multiple signal chains."""
    p = Patcher("outputs/test_matrix_mode_signal_chains.maxpat", layout="matrix", flow_direction="row")

    # Create two parallel signal chains
    # Chain 1
    metro1 = p.add_textbox('metro 250')        # Row 0 (Controls)
    osc1 = p.add_textbox('cycle~ 440')         # Row 1 (Generators)
    filter1 = p.add_textbox('lores~ 1000')     # Row 2 (Processors)

    # Chain 2
    metro2 = p.add_textbox('metro 333')        # Row 0 (Controls)
    osc2 = p.add_textbox('saw~ 220')           # Row 1 (Generators)
    delay2 = p.add_textbox('delay~ 500')       # Row 2 (Processors)

    # Shared output
    dac = p.add_textbox('ezdac~')              # Row 3 (Outputs)

    # Connect the chains
    p.add_line(metro1, osc1)
    p.add_line(osc1, filter1)
    p.add_line(metro2, osc2)
    p.add_line(osc2, delay2)
    p.add_line(filter1, dac)
    p.add_line(delay2, dac)

    # Optimize layout
    p.optimize_layout()

    # In matrix mode, objects of same category should have similar y positions
    # (they're in the same row)
    assert abs(metro1.patching_rect.y - metro2.patching_rect.y) < 50
    assert abs(osc1.patching_rect.y - osc2.patching_rect.y) < 50
    assert abs(filter1.patching_rect.y - delay2.patching_rect.y) < 50

    # Objects in different categories should have different y positions
    assert metro1.patching_rect.y != osc1.patching_rect.y
    assert osc1.patching_rect.y != filter1.patching_rect.y
    assert filter1.patching_rect.y != dac.patching_rect.y

    p.save()


def test_get_signal_chain_info():
    """Test the get_signal_chain_info method for matrix analysis."""
    p = Patcher(layout="matrix", flow_direction="row")

    # Create signal chains
    metro = p.add_textbox('metro 500')
    osc1 = p.add_textbox('cycle~ 440')
    osc2 = p.add_textbox('saw~ 220')
    gain = p.add_textbox('gain~')
    dac = p.add_textbox('ezdac~')

    # Connect in branching pattern
    p.add_line(metro, osc1)
    p.add_line(metro, osc2)
    p.add_line(osc1, gain)
    p.add_line(osc2, gain)
    p.add_line(gain, dac)

    p.optimize_layout()

    # Test signal chain analysis
    chain_info = p._layout_mgr.get_signal_chain_info()
    assert isinstance(chain_info, dict)
    assert "num_chains" in chain_info
    assert "matrix_size" in chain_info
    assert chain_info["num_chains"] >= 1
    assert isinstance(chain_info["matrix_size"], tuple)
    assert len(chain_info["matrix_size"]) == 2


def test_flow_direction_property():
    """Test that flow_direction property works correctly."""
    # Test column flow direction
    p1 = Patcher(layout="matrix", flow_direction="column")
    assert p1._layout_mgr.flow_direction == "column"

    # Test row flow direction
    p2 = Patcher(layout="matrix", flow_direction="row")
    assert p2._layout_mgr.flow_direction == "row"


if __name__ == "__main__":
    # Run matrix mode tests (original tests)
    test_layout_matrix_basic()
    test_layout_matrix_inheritance()
    test_signal_chain_analysis()
    test_layout_matrix_positioning()
    print("Matrix layout tests passed!")

    # Run columnar mode tests
    test_layout_columnar_basic()
    test_object_category_sets()
    test_unknown_object_inference()
    test_layout_columnar_with_connections()
    test_layout_columnar_multiple_objects()
    test_input_objects_classification()
    test_input_objects_priority()
    print("Columnar layout tests passed!")

    # Run flow direction and matrix-specific tests
    test_matrix_mode_basic()
    test_matrix_mode_signal_chains()
    test_get_signal_chain_info()
    test_flow_direction_property()
    print("Flow direction tests passed!")

    print("All MatrixLayoutManager tests passed!")