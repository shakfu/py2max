from py2max import Patcher


def test_message():
    p = Patcher("outputs/test_message.maxpat")
    msg = p.add_message("a b c d")
    p.save()

    assert msg.maxclass == "message"
    assert msg.text == "a b c d"
    assert len(p._boxes) == 1

    box = msg.to_dict()["box"]
    assert box["maxclass"] == "message"
    assert box["text"] == "a b c d"
    assert box["numoutlets"] == 1
