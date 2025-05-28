from py2max import Patcher


def test_dict():
    p = Patcher(path="outputs/test_dict.maxpat")
    d = p.add_dict("bob", dictionary=dict(a=1, b=list(range(20)), c=3))
    p.save()
