from py2max import Patcher


def test_mypatch():
    p = Patcher("outputs/test_mypatch.maxpat", layout="vertical")
    osc1 = p.add_textbox("cycle~ 440")
    gain = p.add_textbox("gain~")
    dac = p.add_textbox("ezdac~")
    p.add_line(osc1, gain)
    p.add_line(gain, dac)
    p.add_line(gain, dac, inlet=1)
    p.save()

    assert osc1.text == "cycle~ 440"
    assert gain.maxclass == "gain~"
    assert dac.maxclass == "ezdac~"
    # cycle~ -> gain~ -> ezdac~ (two lines into ezdac, inlets 0 and 1).
    assert len(p._boxes) == 3
    assert len(p._lines) == 3
    # The two gain~ -> ezdac~ lines target distinct inlets.
    dac_lines = [ln for ln in p._lines if ln.destination[0] == dac.id]
    assert sorted(ln.destination[1] for ln in dac_lines) == [0, 1]
