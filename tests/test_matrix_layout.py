"""Tests for MatrixLayoutManager in both columnar and matrix modes."""

import pytest
from py2max import Patcher
from py2max.layout import MatrixLayoutManager
from py2max.common import Rect
import py2max.category as category


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


def test_object_classification():
    """Test object classification into columns."""
    p = Patcher(layout="matrix", flow_direction="column")
    layout_mgr = p._layout_mgr

    # Add objects from different categories
    control = p.add_floatbox()
    generator = p.add_textbox('cycle~ 440')
    processor = p.add_textbox('gain~')
    output = p.add_textbox('ezdac~')

    # Test classification
    assert layout_mgr._classify_object(control) == 0  # Controls column
    assert layout_mgr._classify_object(generator) == 1  # Generators column
    assert layout_mgr._classify_object(processor) == 2  # Processors column
    assert layout_mgr._classify_object(output) == 3  # Outputs column


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
    # Run columnar mode tests
    test_layout_columnar_basic()
    test_object_classification()
    test_unknown_object_inference()
    test_layout_columnar_with_connections()
    test_layout_columnar_multiple_objects()
    print("All columnar layout tests passed!")

    # Run matrix mode tests
    test_matrix_mode_basic()
    test_matrix_mode_signal_chains()
    test_get_signal_chain_info()
    test_flow_direction_property()
    print("All matrix layout tests passed!")

    print("All MatrixLayoutManager tests passed!")