from py2max import Patcher


def test_rnbo_subpatcher():
    rsp = Patcher("outputs/test_rnbo_subpatcher_child.rnbopat", classnamespace="rnbo")
    osc = rsp.add_textbox("cycle~ 220")
    out1 = rsp.add_textbox("out~ 1")
    rsp.add_line(osc, out1)
    rsp.save()

    # The standalone .rnbopat file uses the rnbo classnamespace.
    assert rsp.classnamespace == "rnbo"
    assert len(rsp._boxes) == 2
    assert len(rsp._lines) == 1
    assert osc.maxclass == "newobj"
    assert osc.text == "cycle~ 220"

    p = Patcher("outputs/test_rnbo_subpatcher_parent.maxpat")
    rnbo = p.add_rnbo(numoutlets=1)

    sp = rnbo.subpatcher

    subpatch = sp.add_textbox("p @file test_rnbo_subpatcher_child")
    out1 = sp.add_textbox("out~ 1")
    sp.add_line(subpatch, out1)
    p.save()

    assert rnbo.numoutlets == 1
    assert sp.classnamespace == "rnbo"
    # The @file reference into the child .rnbopat is preserved on the box.
    assert subpatch.text == "p @file test_rnbo_subpatcher_child"
    assert len(sp._boxes) == 2
    assert len(sp._lines) == 1
    # The saved parent embeds the rnbo subpatcher.
    inner = p.to_dict()["patcher"]["boxes"][0]["box"]["patcher"]
    assert inner["classnamespace"] == "rnbo"
