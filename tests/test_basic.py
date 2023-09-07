from py2max import Patcher


def test_basic():
    p = Patcher('outputs/test_basic.maxpat')
    osc1 = p.add_textbox('cycle~ 440')
    gain = p.add_textbox('gain~')
    dac = p.add_textbox('ezdac~')
    p.add_line(osc1, gain)
    p.add_line(gain, dac)
    p.save()
