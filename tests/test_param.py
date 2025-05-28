from py2max import Patcher


def test_param():
    p = Patcher(path="outputs/test_param.maxpat")
    freq = p.add_floatparam("frequency1", 230, 0, 1000)
    size = p.add_intparam("size", 341, 0, 1000)
    p.save()
