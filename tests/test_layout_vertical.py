from py2max import Patcher


def test_layout_vertical():
    p = Patcher("outputs/test_layout_vertical.maxpat", layout="vertical")

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

    assert len(p._boxes) == 14
    assert len(p._lines) == 14

    # first object sits at the top-left origin of the vertical flow
    first = p._boxes[0].patching_rect
    assert first.x == 48.0 and first.y == 48.0

    # vertical layout stacks boxes downward in a column, then wraps to a new
    # column: within the first column (same x as the origin) y increases
    # strictly in add order.
    first_col = [b.patching_rect.y for b in p._boxes if b.patching_rect.x == first.x]
    assert len(first_col) >= 2
    assert first_col == sorted(first_col)
    assert len(set(first_col)) == len(first_col)  # strictly increasing, no dupes
    assert first_col[-1] > first_col[0]

    # the layout actually wrapped: more than one column exists
    xs = {b.patching_rect.x for b in p._boxes}
    assert len(xs) > 1
