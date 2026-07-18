from py2max import Patcher


def test_itable():
    p = Patcher("outputs/test_itable.maxpat")
    itable = p.add_itable("bob", array=list(range(128)))
    p.save()

    assert len(p._boxes) == 1
    assert itable.maxclass == "itable"
    assert itable.text == "itable bob"

    d = itable.to_dict()["box"]
    assert d["size"] == 128
    assert d["table_data"] == list(range(128))
