from py2max import Patcher


def test_subpatch():
    p = Patcher(path='outputs/test_subpatch.maxpat')
    sbox = p.add_subpatcher('p mysub')
    sp = sbox.subpatcher
    i = sp.add_box('inlet')
    g = sp.add_box('gain~')
    o = sp.add_box('outlet')
    osc = p.add_box('cycle~ 440')
    dac = p.add_box('ezdac~')
    sp.add_line(i, g)
    sp.add_line(g, o)
    p.add_line(osc, sbox)
    p.add_line(sbox, dac)
    p.save()


