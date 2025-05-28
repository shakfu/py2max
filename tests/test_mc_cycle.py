from py2max import Patcher


def test_mc_cycle():
    p = Patcher(path="outputs/test_mc_cycle.maxpat")
    obj = p.add_box("mc.cycle~ 440")
    p.save()
