from py2max import Patcher


def test_scripting_name():
    p = Patcher("outputs/test_scripting_name.maxpat")
    osc = p.add_textbox("cycle~ 440", varname="osc1")
    p.save()

    assert len(p._boxes) == 1
    assert osc.maxclass == "newobj"
    assert osc.text == "cycle~ 440"

    box = osc.to_dict()["box"]
    assert box["varname"] == "osc1"
    assert box["text"] == "cycle~ 440"

    boxes = p.to_dict()["patcher"]["boxes"]
    assert boxes[0]["box"]["varname"] == "osc1"
