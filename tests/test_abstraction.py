from py2max import Patcher


def test_abstraction():
    # create abstraction
    c = Patcher("outputs/half.maxpat")
    in1 = c.add_textbox("inlet")
    out1 = c.add_textbox("outlet")
    mul = c.add_textbox("*~ 0.5")
    c.add_line(in1, mul)
    c.add_line(mul, out1)
    c.save()

    # Abstraction: inlet -> *~ 0.5 -> outlet.
    assert mul.maxclass == "newobj"
    assert mul.text == "*~ 0.5"
    assert len(c._boxes) == 3
    assert len(c._lines) == 2

    # create parent
    p = Patcher("outputs/test_abstraction.maxpat")
    half = p.add_textbox("half")
    p.save()

    # Parent instantiates the abstraction by name as a single newobj.
    assert half.maxclass == "newobj"
    assert half.text == "half"
    assert len(p._boxes) == 1
    assert len(p._lines) == 0
    assert p.to_dict()["patcher"]["boxes"][0]["box"]["text"] == "half"


if __name__ == "__main__":
    test_abstraction()
