
from py2max import Patcher


def test_abstraction():
    # create abstraction
    c = Patcher(path='outputs/half.maxpat')
    in1 = c.add_box('inlet')
    out1 = c.add_box('outlet')
    mul = c.add_box('*~ 0.5')
    c.add_line(in1, mul)
    c.add_line(mul, out1)
    c.save()

    # create parent
    p = Patcher(path='outputs/test_abstraction.maxpat')
    p.add_box('half')
    p.save()


if __name__ == '__main__':
    test_abstraction()
