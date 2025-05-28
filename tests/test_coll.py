from py2max import Patcher


def test_coll():
    p = Patcher(path="outputs/test_coll.maxpat")
    p.add_coll(
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
