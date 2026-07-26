from py2max import Patcher


def test_comment():
    p = Patcher("outputs/test_comment.maxpat")
    osc = p.add_textbox("cycle~ 440", comment="sine osc")
    fparam = p.add_floatparam("Frequency", 10.2, 0.0, 20.0)
    p.save()

    assert osc.maxclass == "newobj"
    assert osc.text == "cycle~ 440"

    assert fparam.maxclass == "flonum"
    fbox = fparam.to_dict()["box"]
    assert fbox["maxclass"] == "flonum"
    assert fbox["minimum"] == 0.0
    assert fbox["maximum"] == 20.0
    valueof = fbox["saved_attribute_attributes"]["valueof"]
    assert valueof["parameter_longname"] == "Frequency"
    assert valueof["parameter_initial"] == [10.2]


def test_comment_port_counts_match_max():
    """A comment takes a `set` message and emits nothing: 1 inlet, 0 outlets.

    `add_comment` passed neither, so `Box.__init__`'s defaults applied and got
    them backwards (0 in / 1 out). Caught by round-tripping a py2max patch
    through Max: Max rewrote the values on save.
    """
    p = Patcher("outputs/test_comment_ports.maxpat")
    box = p.add_comment("hello").to_dict()["box"]

    assert box["maxclass"] == "comment"
    assert box["numinlets"] == 1
    assert box["numoutlets"] == 0
