from .. import Patcher


def test_gen():
    p = Patcher('outputs/test_gen.maxpat')
    sbox = p.add_gen()
    sp = sbox.subpatcher
    i3 = sp.add_textbox('in 3')
    i4 = sp.add_textbox('in 4')
    plus = sp.add_textbox('+')
    sp.add_line(i3, plus)
    sp.add_line(i4, plus)
    p.save()


if __name__ == '__main__':
    test_gen()
