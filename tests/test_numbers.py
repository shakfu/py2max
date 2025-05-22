from py2max import Patcher


def test_add_floatbox():
    p = Patcher("outputs/test_floatbox.maxpat")

    d = {}
    for i in range(4):
        d[i] = p.add_floatbox()

    d[4] = p.add_intbox()

    for i in range(4):
        p.add_line(d[i], d[i + 1])
    p.save()


def test_add_intbox():
    p = Patcher("outputs/test_intbox.maxpat")

    d = {}
    for i in range(4):
        d[i] = p.add_intbox()

    d[4] = p.add_floatbox()

    for i in range(4):
        p.add_line(d[i], d[i + 1])
    p.save()


if __name__ == "__main__":
    test_add_floatbox()
    test_add_intbox()
