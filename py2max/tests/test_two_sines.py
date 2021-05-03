from .. import Patcher


def test_mix_two_sinusoids():
    p = Patcher('output/two-sines.maxpat')
    
    # objects
    freq1 = p.add_floatparam('frequency1', 230, 0, 1000)
    freq2 = p.add_floatparam('frequency2', 341, 0, 1000)
    phase = p.add_floatbox()
    osc1 = p.add_textbox('cycle~')
    osc2 = p.add_textbox('cycle~')
    amp1 = p.add_floatbox()
    amp2 = p.add_floatbox()
    mul1 = p.add_textbox('*~')
    mul2 = p.add_textbox('*~')
    add1 = p.add_textbox('+~')
    dac = p.add_textbox('ezdac~')
    scop = p.add_textbox('scope~')
    scp1 = p.add_intbox()
    scp2 = p.add_intbox()

    # lines
    p.add_line(freq1, osc1)
    p.add_line(osc1, mul1)
    p.add_line(mul1, add1)
    p.add_line(amp1, mul1, inlet=1)
    p.add_line(freq2, osc2)
    p.add_line(phase, osc2, inlet=1)
    p.add_line(osc2, mul2)
    p.add_line(amp2, mul2, inlet=1)
    p.add_line(mul2, add1, inlet=1)
    p.add_line(add1, dac)
    p.add_line(add1, dac, inlet=1)
    p.add_line(add1, scop)
    p.add_line(scp1, scop)
    p.add_line(scp2, scop, inlet=1)
    p.save()


if __name__ == '__main__':
    test_mix_two_sinusoids()
