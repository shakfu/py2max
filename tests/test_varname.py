from py2max import Patcher


def test_varname():
    p = Patcher("outputs/test_varname.maxpat")
    osc1 = p.add_textbox("cycle~ 440", varname="osc")
    gain = p.add_textbox("gain~", varname="volume")
    dac = p.add_textbox("ezdac~")
    p.add_line(osc1, gain)
    p.add_line(gain, dac)
    p.save()

    assert len(p._boxes) == 3
    assert len(p._lines) == 2

    assert osc1.to_dict()["box"]["varname"] == "osc"
    assert gain.to_dict()["box"]["varname"] == "volume"
    # dac was created without a varname; none should be emitted
    assert "varname" not in dac.to_dict()["box"]

    varnames = {
        b["box"].get("varname")
        for b in p.to_dict()["patcher"]["boxes"]
    }
    assert "osc" in varnames
    assert "volume" in varnames
