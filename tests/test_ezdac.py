from py2max import Patcher


def test_ezdac():
    p = Patcher("outputs/test_ezdac.maxpat")
    osc = p.add_textbox("cycle~ 440")
    dac = p.add_textbox("ezdac~")
    p.add_line(osc, dac)
    p.add_line(osc, dac, inlet=1)
    p.save()
