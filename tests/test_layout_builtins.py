from py2max import Patcher

def example(p):
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
    p = Patcher("outputs/test_layout_builtins_flow_vertical.maxpat", layout="flow", flow_direction="vertical")
    example(p)


def test_layout_grid_horizontal():
    """Test new GridLayoutManager with horizontal flow direction."""
    p = Patcher("outputs/test_layout_builtins_grid_horizontal.maxpat", layout="grid", flow_direction="horizontal")
    example(p)
    
    # Verify layout manager type
    from py2max.core import GridLayoutManager
    assert isinstance(p._layout_mgr, GridLayoutManager)
    assert p._layout_mgr.flow_direction == "horizontal"


def test_layout_grid_vertical():
    """Test new GridLayoutManager with vertical flow direction."""
    p = Patcher("outputs/test_layout_builtins_grid_vertical.maxpat", layout="grid", flow_direction="vertical")
    example(p)
    
    # Verify layout manager type
    from py2max.core import GridLayoutManager
    assert isinstance(p._layout_mgr, GridLayoutManager)
    assert p._layout_mgr.flow_direction == "vertical"


def test_layout_grid_default():
    """Test new GridLayoutManager with default (horizontal) flow direction."""
    p = Patcher("outputs/test_layout_builtins_grid_default.maxpat", layout="grid")
    example(p)
    
    # Verify layout manager type and default direction
    from py2max.core import GridLayoutManager
    assert isinstance(p._layout_mgr, GridLayoutManager)
    assert p._layout_mgr.flow_direction == "horizontal"  # Should default to horizontal


def test_backward_compatibility_horizontal():
    """Test that legacy horizontal layout still works (backward compatibility)."""
    p = Patcher("outputs/test_layout_builtins_backward_horizontal.maxpat", layout="horizontal")
    example(p)
    
    # Verify it still creates a HorizontalLayoutManager (legacy alias)
    from py2max.core import HorizontalLayoutManager
    assert isinstance(p._layout_mgr, HorizontalLayoutManager)


def test_backward_compatibility_vertical():
    """Test that legacy vertical layout still works (backward compatibility)."""
    p = Patcher("outputs/test_layout_builtins_backward_vertical.maxpat", layout="vertical")
    example(p)
    
    # Verify it still creates a VerticalLayoutManager (legacy alias)
    from py2max.core import VerticalLayoutManager
    assert isinstance(p._layout_mgr, VerticalLayoutManager)

