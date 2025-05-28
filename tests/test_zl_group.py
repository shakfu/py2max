from py2max import Patcher


def test_zl_group():
    p = Patcher(path="outputs/test_zl_group.maxpat")
    lst = p.add_message("1 2 2 3 4 3 4 5 6 7 7 8 8 9 9 10")
    zlg = p.add_box("zl.group 2")
    out = p.add_box("print group")
    p.link(lst, zlg)
    p.link(zlg, out)
    p.save()
