from py2max import Patcher

def test_layout_flow():
    p = Patcher("outputs/test_layout_flow.maxpat", layout="flow")

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
    p.optimize_layout()
    p.save()


def test_layout_flow2():
    """Test the new FlowLayoutManager with a complex signal chain."""
    p = Patcher("outputs/test_layout_flow2.maxpat", layout="flow")

    # Create a signal processing chain to test flow layout
    # Input section
    freq_control = p.add_floatbox()
    phase_control = p.add_floatbox()
    
    # Oscillator section
    osc1 = p.add_textbox("cycle~ 440")
    osc2 = p.add_textbox("cycle~ 220")
    
    # Processing section
    gain1 = p.add_textbox("gain~")
    gain2 = p.add_textbox("gain~")
    amp_control1 = p.add_floatbox()
    amp_control2 = p.add_floatbox()
    
    # Mixing section
    mixer = p.add_textbox("+~")
    
    # Effects section
    filter_obj = p.add_textbox("lores~")
    cutoff_control = p.add_floatbox()
    
    # Output section
    output_gain = p.add_textbox("gain~")
    master_vol = p.add_floatbox()
    dac = p.add_textbox("ezdac~")
    scope = p.add_textbox("scope~")
    
    # Create patchlines to define signal flow
    # Control connections
    p.add_line(freq_control, osc1)
    p.add_line(phase_control, osc2, inlet=1)  # phase inlet
    p.add_line(amp_control1, gain1, inlet=1)
    p.add_line(amp_control2, gain2, inlet=1)
    p.add_line(cutoff_control, filter_obj, inlet=1)
    p.add_line(master_vol, output_gain, inlet=1)
    
    # Signal flow
    p.add_line(osc1, gain1)
    p.add_line(osc2, gain2)
    p.add_line(gain1, mixer)
    p.add_line(gain2, mixer, inlet=1)
    p.add_line(mixer, filter_obj)
    p.add_line(filter_obj, output_gain)
    p.add_line(output_gain, dac)
    p.add_line(output_gain, dac, inlet=1)  # stereo
    p.add_line(output_gain, scope)
    
    # Test that we can optimize layout after creating connections
    p.optimize_layout()
    
    # Verify layout manager is FlowLayoutManager
    from py2max.core import FlowLayoutManager
    assert isinstance(p._layout_mgr, FlowLayoutManager)
    
    # Verify objects have reasonable positions
    positions = []
    for box in p._boxes:
        pos = box.patching_rect
        positions.append((pos.x, pos.y))
        # Check that positions are within patcher bounds
        assert 0 <= pos.x <= p.width
        assert 0 <= pos.y <= p.height
    
    # Verify that positions are not all the same (layout actually worked)
    unique_positions = set(positions)
    assert len(unique_positions) > 1, "Layout should create different positions for objects"
    
    p.save()


def test_layout_flow_simple():
    """Test FlowLayoutManager with a simple signal chain."""
    p = Patcher("outputs/test_layout_flow_simple.maxpat", layout="flow")

    # Simple chain: oscillator -> gain -> dac
    osc = p.add_textbox("cycle~ 440")
    gain = p.add_textbox("gain~")
    dac = p.add_textbox("ezdac~")
    
    # Connect them
    p.add_line(osc, gain)
    p.add_line(gain, dac)
    
    # Optimize layout
    p.optimize_layout()
    
    # Verify positions make sense (left-to-right flow)
    osc_x = osc.patching_rect.x
    gain_x = gain.patching_rect.x
    dac_x = dac.patching_rect.x
    
    # Should be roughly left-to-right ordering
    assert osc_x < gain_x, "Oscillator should be left of gain"
    assert gain_x < dac_x, "Gain should be left of DAC"
    
    p.save()


def test_layout_flow_fallback():
    """Test FlowLayoutManager fallback behavior with no connections."""
    p = Patcher("outputs/test_layout_flow_fallback.maxpat", layout="flow")

    # Add objects without connections
    obj1 = p.add_textbox("cycle~")
    obj2 = p.add_textbox("gain~")
    obj3 = p.add_textbox("ezdac~")
    
    # Should still work and place objects
    positions = []
    for box in p._boxes:
        pos = box.patching_rect
        positions.append((pos.x, pos.y))
        assert 0 <= pos.x <= p.width
        assert 0 <= pos.y <= p.height
    
    # Should create different positions even without connections
    unique_positions = set(positions)
    assert len(unique_positions) > 1, "Should still layout objects without connections"
    
    p.save()