from py2max import Patcher


def test_varname():
    p = Patcher(path='outputs/test_varname.maxpat')
    osc1 = p.add_box('cycle~ 440', varname='osc')
    gain = p.add_box('gain~', varname="volume")
    dac = p.add_box('ezdac~')
    p.add_line(osc1, gain)
    p.add_line(gain, dac)
    p.save()

