from py2max import Patcher
from py2max.utils import pitch2freq


def build_patch():
    # Create patcher with layout
    p = Patcher(
        "outputs/test_tutorial_simple_synthesis.maxpat",
        layout="matrix",
    )

    # Create oscillators for a C major chord
    freqs = [pitch2freq("C4"), pitch2freq("E4"), pitch2freq("G4")]
    oscillators = []

    for i, freq in enumerate(freqs):
        osc = p.add_textbox(f"cycle~ {freq:.2f}")
        oscillators.append(osc)

    # Add gain controls
    gain_mults = []
    gain_params = []
    for i in range(3):
        gain_param = p.add_floatparam(f"gain{i}", initial=0.3)
        gain_params.append(gain_param)
        gain_mult = p.add_textbox("*~")
        gain_mults.append(gain_mult)
        # Connect param and oscillator to gain_mult
        p.add_line(gain_param, gain_mult)
        p.add_line(oscillators[i], gain_mult, inlet=1)

    # Add master volume and output
    master_vol = p.add_floatparam("master", initial=0.5)
    master_mult = p.add_textbox("*~")
    output = p.add_textbox("ezdac~")

    for gain_mult in gain_mults:
        # mix the input signals
        p.add_line(gain_mult, master_mult)

    p.add_line(master_vol, master_mult, inlet=1)
    p.add_line(master_mult, output)
    p.add_line(master_mult, output, inlet=1)

    # Optimize layout
    p.optimize_layout()
    p.save()

    return p, oscillators, gain_params, gain_mults, master_vol, master_mult, output


def test_tutorial_simple_synthesis():
    p, oscs, gain_params, gain_mults, master_vol, master_mult, output = build_patch()

    # 3 osc + 3 gain mults + master mult + dac = 8 objects, plus each of the
    # 4 floatparams emits a flonum + its label comment (8 boxes) -> 16 total.
    assert len(p._boxes) == 16
    flonums = [b for b in p._boxes if b.maxclass == "flonum"]
    assert len(flonums) == 4
    # 3*(param->mult) + 3*(osc->mult) + 3*(mult->master) + master_vol + 2*(master->dac)
    assert len(p._lines) == 12

    # oscillator frequencies match the C major chord (C4, E4, G4)
    freqs = [pitch2freq(n) for n in ("C4", "E4", "G4")]
    for osc, f in zip(oscs, freqs):
        assert osc.text == f"cycle~ {f:.2f}"
        assert osc.maxclass == "newobj"

    # gain params are float parameters carrying the correct longnames
    for i, gp in enumerate(gain_params):
        gd = gp.to_dict()["box"]
        assert gd["maxclass"] == "flonum"
        val = gd["saved_attribute_attributes"]["valueof"]
        assert val["parameter_longname"] == f"gain{i}"
        assert val["parameter_initial"] == [0.3]

    assert master_vol.to_dict()["box"]["saved_attribute_attributes"]["valueof"][
        "parameter_initial"
    ] == [0.5]
    assert output.text == "ezdac~"

    # verify the wiring: each osc[i] -> gain_mult[i] inlet 1, gain_param[i] -> mult inlet 0
    def has_line(src_id, dst_id, outlet=0, inlet=0):
        return any(
            ln.source == [src_id, outlet] and ln.destination == [dst_id, inlet]
            for ln in p._lines
        )

    for i in range(3):
        assert has_line(gain_params[i].id, gain_mults[i].id, inlet=0)
        assert has_line(oscs[i].id, gain_mults[i].id, inlet=1)
        assert has_line(gain_mults[i].id, master_mult.id)

    assert has_line(master_vol.id, master_mult.id, inlet=1)
    assert has_line(master_mult.id, output.id, inlet=0)
    assert has_line(master_mult.id, output.id, inlet=1)


if __name__ == "__main__":
    test_tutorial_simple_synthesis()
