from py2max import Patcher


def test_bpatcher():
    # create bpatcher
    bp = Patcher("outputs/test_bpatcher_child.maxpat", openinpresentation=1)
    in1 = bp.add("inlet")
    scope = bp.add("scope~", presentation=1, presentation_rect=[4.0, 4.0, 130.0, 130.0])
    bp.link(in1, scope)
    bp.save()

    assert len(bp._boxes) == 2
    assert bp.to_dict()["patcher"]["openinpresentation"] == 1
    assert in1.text == "inlet"
    scope_box = scope.to_dict()["box"]
    assert scope_box["maxclass"] == "scope~"
    assert scope_box["presentation"] == 1
    assert scope_box["presentation_rect"] == [4.0, 4.0, 130.0, 130.0]

    # create parent patcher
    p = Patcher("outputs/test_bpatcher_parent.maxpat")
    osc = p.add("cycle~ 2")
    bp2 = p.add_bpatcher(
        "test_bpatcher_child", patching_rect=[32.0, 92.0, 140.0, 140.0]
    )
    dac = p.add("ezdac~")
    p.link(osc, bp2)
    p.save()

    assert len(p._boxes) == 3
    assert len(p._lines) == 1

    bp2_box = bp2.to_dict()["box"]
    assert bp2_box["maxclass"] == "bpatcher"
    assert bp2_box["name"] == "test_bpatcher_child"
    assert bp2_box["patching_rect"] == [32.0, 92.0, 140.0, 140.0]

    assert osc.maxclass == "newobj"
    assert osc.text == "cycle~ 2"
    assert dac.maxclass == "ezdac~"

    line = p._lines[0].to_dict()["patchline"]
    assert line["source"][0] == osc.id
    assert line["destination"][0] == bp2.id
