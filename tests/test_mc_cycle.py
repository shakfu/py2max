from py2max import Patcher


def test_mc_cycle():
    p = Patcher("outputs/test_mc_cycle.maxpat")
    mc = p.add_textbox("mc.cycle~ 440")
    p.save()

    assert len(p._boxes) == 1
    assert mc.maxclass == "newobj"
    assert mc.text == "mc.cycle~ 440"

    box = mc.to_dict()["box"]
    assert box["maxclass"] == "newobj"
    assert "mc.cycle~ 440" in box["text"]

    boxes = p.to_dict()["patcher"]["boxes"]
    assert len(boxes) == 1
    assert boxes[0]["box"]["text"] == "mc.cycle~ 440"
