from py2max import Patcher


def test_rnbo_subpatcher():
    rsp = Patcher("outputs/test_rnbo_subpatcher_child.rnbopat", classnamespace="rnbo")
    osc = rsp.add_textbox("cycle~ 220")
    out1 = rsp.add_textbox("out~ 1")
    rsp.add_line(osc, out1)
    rsp.save()

    p = Patcher("outputs/test_rnbo_subpatcher_parent.maxpat")
    rnbo = p.add_rnbo(numoutlets=1)

    sp = rnbo.subpatcher

    subpatch = sp.add_textbox("p @file test_rnbo_subpatcher_child")
    out1 = sp.add_textbox("out~ 1")
    sp.add_line(subpatch, out1)
    p.save()
