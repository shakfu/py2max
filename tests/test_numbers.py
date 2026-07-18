from py2max import Patcher


def test_add_floatbox():
    p = Patcher("outputs/test_floatbox.maxpat")

    d = {}
    for i in range(4):
        d[i] = p.add_floatbox()

    d[4] = p.add_intbox()

    lines = []
    for i in range(4):
        lines.append(p.add_line(d[i], d[i + 1]))
    p.save()

    assert len(p._boxes) == 5
    for i in range(4):
        assert d[i].maxclass == "flonum"
    assert d[4].maxclass == "number"

    assert len(p._lines) == 4
    for i, ln in enumerate(lines):
        assert ln.source[0] == d[i].id
        assert ln.destination[0] == d[i + 1].id


def test_add_intbox():
    p = Patcher("outputs/test_intbox.maxpat")

    d = {}
    for i in range(4):
        d[i] = p.add_intbox()

    d[4] = p.add_floatbox()

    lines = []
    for i in range(4):
        lines.append(p.add_line(d[i], d[i + 1]))
    p.save()

    assert len(p._boxes) == 5
    for i in range(4):
        assert d[i].maxclass == "number"
    assert d[4].maxclass == "flonum"

    assert len(p._lines) == 4
    for i, ln in enumerate(lines):
        assert ln.source[0] == d[i].id
        assert ln.destination[0] == d[i + 1].id


if __name__ == "__main__":
    test_add_floatbox()
    test_add_intbox()
