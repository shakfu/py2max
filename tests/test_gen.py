from py2max import Patcher


def test_gen():
    p = Patcher(path="outputs/test_gen.maxpat")
    sbox = p.add_gen()
    sp = sbox.subpatcher
    i3 = sp.add_box("in 3")
    i4 = sp.add_box("in 4")
    plus = sp.add_box("+")
    sp.add_line(i3, plus)
    sp.add_line(i4, plus)
    p.save()


def test_gen_tilde():
    p = Patcher(path="outputs/test_gen_tilde.maxpat")
    sbox = p.add_gen_tilde()  # also p.add_gen(tilde=True)
    sp = sbox.subpatcher
    i1 = sp.add_box("in 1")
    i2 = sp.add_box("in 2")
    o1 = sp.add_box("out 1")
    plus = sp.add_box("+")
    sp.add_line(i1, plus)
    sp.add_line(i2, plus, inlet=1)
    sp.add_line(plus, o1)
    p.save()
