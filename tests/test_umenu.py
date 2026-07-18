from py2max import Patcher


def test_umenu():
    p = Patcher("outputs/test_umenu.maxpat")
    umenu = p.add_umenu(items=["01.wav", "02.wav", "03.wav"])
    p.save()

    assert len(p._boxes) == 1
    assert umenu.maxclass == "umenu"

    d = umenu.to_dict()["box"]
    assert d["items"] == ["01.wav", ",", "02.wav", ",", "03.wav", ","]
    assert d["autopopulate"] == 1


if __name__ == "__main__":
    test_umenu()
