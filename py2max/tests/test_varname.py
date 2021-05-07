from .. import Patcher


def test_varname():
    p = Patcher('outputs/test_varname.maxpat')
    osc1 = p.add_textbox('cycle~ 440', varname='osc')
    gain = p.add_textbox('gain~', varname="volume")
    dac = p.add_textbox('ezdac~')
    p.add_line(osc1, gain)
    p.add_line(gain, dac)
    p.save()


if __name__ == '__main__':
    test_varname()
