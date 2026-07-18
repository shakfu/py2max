from py2max import Patcher


def test_ezdac():
    p = Patcher("outputs/test_ezdac.maxpat")
    osc = p.add_textbox("cycle~ 440")
    dac = p.add_textbox("ezdac~")
    l1 = p.add_line(osc, dac)
    l2 = p.add_line(osc, dac, inlet=1)
    p.save()

    assert dac.maxclass == "ezdac~"
    assert dac.text == "ezdac~"

    assert len(p._lines) == 2
    assert l1.source[0] == osc.id
    assert l1.destination[0] == dac.id
    assert l1.destination[1] == 0
    assert l2.source[0] == osc.id
    assert l2.destination[0] == dac.id
    assert l2.destination[1] == 1
