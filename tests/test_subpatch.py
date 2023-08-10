from py2max import Patcher


def test_subpatch():
    p = Patcher('outputs/test_subpatch.maxpat')
    sbox = p.add_subpatcher('p mysub')
    sp = sbox.subpatcher
    i = sp.add_textbox('inlet')
    g = sp.add_textbox('gain~')
    o = sp.add_textbox('outlet')
    osc = p.add_textbox('cycle~ 440')
    dac = p.add_textbox('ezdac~')
    sp.add_line(i, g)
    sp.add_line(g, o)
    p.add_line(osc, sbox)
    p.add_line(sbox, dac)
    p.save()


if __name__ == '__main__':
    test_subpatch()
