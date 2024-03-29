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
