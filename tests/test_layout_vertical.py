from py2max.core import Patcher, VerticalLayoutManager

def test_layout_vertical():
    p = Patcher('outputs/test_layout_vertical.maxpat',
                layout_mgr_class=VerticalLayoutManager)

    fbox = p.add_floatbox
    ibox = p.add_intbox
    tbox = p.add_textbox
    link = p.add_line

    # objects
    freq1 = fbox()
    freq2 = fbox()
    phase = fbox()
    osc1 = tbox('cycle~')
    osc2 = tbox('cycle~')
    amp1 = fbox()
    amp2 = fbox()
    mul1 = tbox('*~')
    mul2 = tbox('*~')
    add1 = tbox('+~')
    dac = tbox('ezdac~')
    scop = tbox('scope~')
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


if __name__ == '__main__':
    test_graph()


if __name__ == '__main__':
    test_layout_vertical()

