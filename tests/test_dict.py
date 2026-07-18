from py2max import Patcher


def test_dict():
    p = Patcher("outputs/test_dict.maxpat")
    mdict = p.add_dict("bob", dictionary=dict(a=1, b=list(range(20)), c=3))
    p.save()

    assert len(p._boxes) == 1
    assert mdict.maxclass == "newobj"
    assert mdict.text == "dict bob @embed 1"

    d = mdict.to_dict()["box"]
    assert d["saved_object_attributes"]["embed"] == 1
    assert d["data"] == {"a": 1, "b": list(range(20)), "c": 3}
