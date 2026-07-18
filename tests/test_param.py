from py2max import Patcher


def test_param():
    p = Patcher("outputs/test_param.maxpat")
    fp = p.add_floatparam("frequency1", 230, 0, 1000)
    ip = p.add_intparam("size", 341, 0, 1000)
    p.save()

    # each param adds a value box plus a label comment box
    assert len(p._boxes) == 4
    assert [b.maxclass for b in p._boxes] == [
        "flonum",
        "number",
        "comment",
        "comment",
    ]

    fbox = fp.to_dict()["box"]
    assert fbox["maxclass"] == "flonum"
    assert fbox["parameter_enable"] == 1
    fparam = fbox["saved_attribute_attributes"]["valueof"]
    assert fparam["parameter_longname"] == "frequency1"
    assert fparam["parameter_initial"] == [230]
    assert fparam["parameter_type"] == 0
    assert fbox["minimum"] == 0
    assert fbox["maximum"] == 1000

    ibox = ip.to_dict()["box"]
    assert ibox["maxclass"] == "number"
    assert ibox["parameter_enable"] == 1
    iparam = ibox["saved_attribute_attributes"]["valueof"]
    assert iparam["parameter_longname"] == "size"
    assert iparam["parameter_initial"] == [341]
    assert iparam["parameter_type"] == 1
    assert iparam["parameter_mmax"] == 1000
