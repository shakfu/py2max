from py2max import Patcher


def test_defaults():
    p = Patcher("outputs/test_defaults.maxpat")
    for i in range(10):
        p.add(f"cycle~ {i * 20}")
    p.add_textbox("filtergraph~")
    p.add_textbox("scope~")
    p.add_textbox("ezdac~")
    p.save()

    assert len(p._boxes) == 13

    classes = [b.maxclass for b in p._boxes]
    assert classes[:10] == ["newobj"] * 10
    assert classes[10:] == ["filtergraph~", "scope~", "ezdac~"]

    assert p._boxes[0].text == "cycle~ 0"
    assert p._boxes[9].text == "cycle~ 180"

    boxes = p.to_dict()["patcher"]["boxes"]
    assert len(boxes) == 13
    assert boxes[10]["box"]["maxclass"] == "filtergraph~"
    assert boxes[11]["box"]["maxclass"] == "scope~"
    assert boxes[12]["box"]["maxclass"] == "ezdac~"
