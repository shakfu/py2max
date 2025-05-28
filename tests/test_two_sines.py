from py2max import Patcher


def test_mix_two_sinusoids():
    p = Patcher(path="outputs/test_two_sines.maxpat")

    fparam = p.add_floatparam
    iparam = p.add_intparam
    tbox = p.add_box
    link = p.add_line

    # objects
    freq1 = fparam("frequency1", 230, 0, 1000)
    freq2 = fparam("frequency2", 341, 0, 1000)
    phase = fparam("phase_offset", 0.39)
    osc1 = tbox("cycle~")
    osc2 = tbox("cycle~")
    amp1 = fparam("amp1", 0.51)
    amp2 = fparam("amp2", 0.46)
    mul1 = tbox("*~")
    mul2 = tbox("*~")
    add1 = tbox("+~")
    dac = tbox("ezdac~")
    scop = tbox("scope~")
    scp1 = iparam("buffer_pixel", 40)
    scp2 = iparam("samples_buffer", 8)

    # lines
    link(freq1, osc1)
    link(osc1, mul1)
    link(mul1, add1)
    link(amp1, mul1, inlet=1)
    link(freq2, osc2)
    link(phase, osc2, inlet=1)
    link(osc2, mul2)
    link(amp2, mul2, inlet=1)
    link(mul2, add1, inlet=1)
    link(add1, dac)
    link(add1, dac, inlet=1)
    link(add1, scop)
    link(scp1, scop)
    link(scp2, scop, inlet=1)
    p.save()


if __name__ == "__main__":
    test_mix_two_sinusoids()
