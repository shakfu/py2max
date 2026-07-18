from py2max import Patcher
from py2max.utils import pitch2freq


def pitched_osc(p, pitch):
    freq = pitch2freq(pitch)
    return p.add_textbox(f"cycle~ {freq}")


def test_combo_osc():
    p = Patcher("outputs/test_combo_osc.maxpat", layout="vertical")
    osc = pitched_osc(p, "C3")
    dac = p.add_textbox("ezdac~")
    p.link(osc, dac)
    p.save()

    freq = pitch2freq("C3")
    assert osc.maxclass == "newobj"
    assert osc.text == f"cycle~ {freq}"
    assert dac.maxclass == "ezdac~"

    assert len(p._boxes) == 2
    assert len(p._lines) == 1

    line = p._lines[0].to_dict()["patchline"]
    assert line["source"][0] == osc.id
    assert line["destination"][0] == dac.id
