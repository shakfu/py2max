from py2max import Patcher


def test_itable():
    p = Patcher(path="outputs/test_itable.maxpat")
    p.add_itable("bob", array=list(range(128)))
    p.save()
