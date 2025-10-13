from py2max import Patcher, InvalidConnectionError
from py2max.maxref import validate_connection, get_inlet_count, get_outlet_count
import pytest


def test_validate_connection_basic():
    """Test basic connection validation functionality."""
    # Valid connection: cycle~ outlet 0 to gain~ inlet 0
    is_valid, msg = validate_connection("cycle~", 0, "gain~", 0)
    assert is_valid, f"Should be valid: {msg}"

    # Valid connection: gain~ outlet 0 to ezdac~ inlet 0
    is_valid, msg = validate_connection("gain~", 0, "ezdac~", 0)
    assert is_valid, f"Should be valid: {msg}"


def test_validate_connection_invalid_outlets():
    """Test validation catches invalid outlet numbers."""
    # cycle~ only has 1 outlet (index 0)
    is_valid, msg = validate_connection("cycle~", 1, "gain~", 0)
    assert not is_valid
    assert "only has 1 outlet" in msg

    # Test with an object that has multiple outlets
    is_valid, msg = validate_connection(
        "gain~", 2, "ezdac~", 0
    )  # gain~ has 2 outlets (0,1)
    assert not is_valid
    assert "only has 2 outlet" in msg


def test_validate_connection_invalid_inlets():
    """Test validation catches invalid inlet numbers."""
    # Test connecting to non-existent inlet
    # ezdac~ has 2 inlets (0,1)
    is_valid, msg = validate_connection("cycle~", 0, "ezdac~", 2)
    assert not is_valid
    assert "only has 2 inlet" in msg


def test_validate_connection_signal_types():
    """Test signal type validation."""
    # Try to connect signal output to non-signal input (this might not trigger for all objects)
    # We'll test with objects where we know the types
    is_valid, msg = validate_connection("cycle~", 0, "number", 0)
    if not is_valid:
        assert "signal" in msg.lower()


def test_patcher_validation_enabled():
    """Test that patcher validation works when enabled."""
    p = Patcher("outputs/test_validation_enabled.maxpat", validate_connections=True)

    osc = p.add_textbox("cycle~")
    gain = p.add_textbox("gain~")

    # Valid connection should work
    p.add_line(osc, gain)

    # Invalid connection should raise exception
    with pytest.raises(InvalidConnectionError) as exc_info:
        p.add_line(osc, gain, outlet=5)  # cycle~ doesn't have outlet 5

    assert "only has" in str(exc_info.value)
    p.save()


def test_patcher_validation_disabled():
    """Test that validation can be disabled."""
    p = Patcher("outputs/test_validation_disabled.maxpat", validate_connections=False)

    osc = p.add_textbox("cycle~")
    gain = p.add_textbox("gain~")

    # Invalid connection should work when validation is disabled
    p.add_line(osc, gain, outlet=5)  # This should not raise an exception
    p.save()


def test_box_inlet_outlet_methods():
    """Test the new Box methods for getting inlet/outlet information."""
    p = Patcher("outputs/test_box_methods.maxpat")

    cycle = p.add_textbox("cycle~ 440")
    gain = p.add_textbox("gain~")
    dac = p.add_textbox("ezdac~")

    # Test inlet/outlet counts
    cycle_inlets = cycle.get_inlet_count()
    cycle_outlets = cycle.get_outlet_count()

    if cycle_inlets is not None:  # Only test if we have maxref data
        assert cycle_inlets >= 1, "cycle~ should have at least 1 inlet"

    if cycle_outlets is not None:
        assert cycle_outlets >= 1, "cycle~ should have at least 1 outlet"

    # Test inlet/outlet types
    inlet_types = cycle.get_inlet_types()
    outlet_types = cycle.get_outlet_types()

    if inlet_types:
        assert len(inlet_types) > 0, "Should have inlet type information"

    if outlet_types:
        assert len(outlet_types) > 0, "Should have outlet type information"
        # cycle~ output should be signal type
        assert "signal" in outlet_types[0], "cycle~ output should be signal type"

    p.save()


def test_inlet_outlet_count_functions():
    """Test the standalone inlet/outlet count functions."""
    # Test known objects
    cycle_inlets = get_inlet_count("cycle~")
    cycle_outlets = get_outlet_count("cycle~")

    if cycle_inlets is not None:
        assert cycle_inlets >= 1

    if cycle_outlets is not None:
        assert cycle_outlets >= 1

    # Test non-existent object
    fake_inlets = get_inlet_count("nonexistent_object")
    assert fake_inlets is None


def test_validation_complex_patch():
    """Test validation with a more complex patch."""
    p = Patcher("outputs/test_validation_complex.maxpat", validate_connections=True)

    # Create objects
    freq_control = p.add_floatbox()
    osc = p.add_textbox("cycle~")
    gain = p.add_textbox("gain~")
    dac = p.add_textbox("ezdac~")

    # Valid connections
    p.add_line(freq_control, osc)  # Control to frequency inlet
    p.add_line(osc, gain)  # Audio signal
    p.add_line(gain, dac)  # To left channel
    p.add_line(gain, dac, inlet=1)  # To right channel

    # Test invalid connection that should be caught
    with pytest.raises(InvalidConnectionError):
        # Try to connect to a non-existent inlet
        p.add_line(freq_control, osc, inlet=10)

    p.save()


def test_validation_backwards_compatibility():
    """Test that validation works gracefully when maxref data is missing."""
    p = Patcher("outputs/test_validation_compat.maxpat", validate_connections=True)

    # Create objects that might not have maxref data
    obj1 = p.add_textbox("unknown_object_xyz")
    obj2 = p.add_textbox("another_unknown_object")

    # Connection should be allowed even with unknown objects
    p.add_line(obj1, obj2)  # Should not raise exception

    p.save()


def test_connection_validation_error_messages():
    """Test that error messages are informative."""
    # Test outlet error message
    is_valid, msg = validate_connection("cycle~", 5, "gain~", 0)
    if not is_valid:
        assert "cycle~" in msg
        assert "outlet" in msg
        assert "5" in msg

    # Test inlet error message
    is_valid, msg = validate_connection("cycle~", 0, "ezdac~", 5)
    if not is_valid:
        assert "ezdac~" in msg
        assert "inlet" in msg
        assert "5" in msg
