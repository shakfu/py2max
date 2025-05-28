from py2max import Patcher


def test_mypatch():
    p = Patcher(path="outputs/test_mypatch.maxpat", layout="vertical")
    osc1 = p.add_box("cycle~ 440")
    gain = p.add_box("gain~")
    dac = p.add_box("ezdac~")
    p.add_line(osc1, gain)
    p.add_line(gain, dac)
    p.add_line(gain, dac, inlet=1)
    p.save()
