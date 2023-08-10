
from py2max import Patcher


def test_abstraction():
    # create abstraction
    c = Patcher('outputs/half.maxpat')
    in1 = c.add_textbox('inlet')
    out1 = c.add_textbox('outlet')
    mul = c.add_textbox('*~ 0.5')
    c.add_line(in1, mul)
    c.add_line(mul, out1)
    c.save()

    # create parent
    p = Patcher('outputs/test_abstraction.maxpat')
    p.add_textbox('half')
    p.save()


if __name__ == '__main__':
    test_abstraction()
