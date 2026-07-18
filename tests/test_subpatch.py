from py2max import Patcher


def test_subpatch():
    p = Patcher("outputs/test_subpatch.maxpat")
    sbox = p.add_subpatcher("p mysub")
    sp = sbox.subpatcher
    i = sp.add_textbox("inlet")
    g = sp.add_textbox("gain~")
    o = sp.add_textbox("outlet")
    osc = p.add_textbox("cycle~ 440")
    dac = p.add_textbox("ezdac~")
    sp.add_line(i, g)
    sp.add_line(g, o)
    p.add_line(osc, sbox)
    p.add_line(sbox, dac)
    p.save()

    # Subpatcher wrapper box and its inner patcher.
    assert sbox.maxclass == "newobj"
    assert sbox.text == "p mysub"
    assert sp is sbox.subpatcher
    assert sp.classnamespace == "box"
    # Inner: inlet -> gain~ -> outlet.
    assert len(sp._boxes) == 3
    assert len(sp._lines) == 2
    assert g.maxclass == "gain~"
    # Parent: subpatcher + cycle~ + ezdac~, wired osc -> sub -> dac.
    assert len(p._boxes) == 3
    assert len(p._lines) == 2
    # The saved parent embeds the inner patcher with its three boxes.
    box0 = p.to_dict()["patcher"]["boxes"][0]["box"]
    assert "patcher" in box0
    assert len(box0["patcher"]["boxes"]) == 3
