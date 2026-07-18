from py2max import Patcher


def test_coll():
    p = Patcher("outputs/test_coll.maxpat")
    coll = p.add_coll(
        "store",
        dictionary={
            1: [1, 1.5, "sam"],
            2: [1.5, 2, "ok"],
            3: ["A", 25, 1.2],
            "a": ["abcd"],
            "b": [1, 2, 3, 4, 5, 4],
        },
    )
    p.save()

    assert len(p._boxes) == 1
    assert coll.maxclass == "newobj"
    assert coll.text == "coll store @embed 1"

    d = coll.to_dict()["box"]
    assert d["saved_object_attributes"]["embed"] == 1
    assert d["coll_data"]["count"] == 5
    entries = {e["key"]: e["value"] for e in d["coll_data"]["data"]}
    assert entries[1] == [1, 1.5, "sam"]
    assert entries["a"] == ["abcd"]
    assert entries["b"] == [1, 2, 3, 4, 5, 4]
