from py2max import Patcher


def test_zl_group():
    p = Patcher("outputs/test_zl_group.maxpat")
    lst = p.add_message("1 2 2 3 4 3 4 5 6 7 7 8 8 9 9 10")
    zlg = p.add_textbox("zl.group 2")
    out = p.add_textbox("print group")
    p.link(lst, zlg)
    p.link(zlg, out)
    p.save()

    assert len(p._boxes) == 3
    assert len(p._lines) == 2

    assert lst.maxclass == "message"
    assert lst.text == "1 2 2 3 4 3 4 5 6 7 7 8 8 9 9 10"
    assert zlg.maxclass == "newobj"
    assert zlg.text == "zl.group 2"
    assert out.maxclass == "newobj"
    assert out.text == "print group"

    line1 = p._lines[0].to_dict()["patchline"]
    assert line1["source"] == [lst.id, 0]
    assert line1["destination"] == [zlg.id, 0]
    line2 = p._lines[1].to_dict()["patchline"]
    assert line2["source"] == [zlg.id, 0]
    assert line2["destination"] == [out.id, 0]
