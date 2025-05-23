from py2max import Patcher


def test_gen():
    p = Patcher("outputs/test_gen.maxpat")
    sbox = p.add_gen("@title windowSync")
    sp = sbox.subpatcher
    i3 = sp.add_textbox("in 3")
    i4 = sp.add_textbox("in 4")
    plus = sp.add_textbox("+")
    sp.add_line(i3, plus)
    sp.add_line(i4, plus)
    p.save()


def test_gen_tilde():
    p = Patcher("outputs/test_gen_tilde.maxpat")
    sbox = p.add_gen_tilde("@nocache 0")  # also p.add_gen(tilde=True)
    sp = sbox.subpatcher
    i1 = sp.add_textbox("in 1")
    i2 = sp.add_textbox("in 2")
    o1 = sp.add_textbox("out 1")
    plus = sp.add_textbox("+")
    sp.add_line(i1, plus)
    sp.add_line(i2, plus, inlet=1)
    sp.add_line(plus, o1)
    p.save()
