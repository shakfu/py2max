from py2max import Patcher

# minimal requirement


def test_attrui():
    p = Patcher("outputs/test_attrui.maxpat")
    osc = p.add_textbox("cycle~")
    freq = p.add_textbox(
        "attrui",
        maxclass="attrui",
        attr="frequency",
        parameter_enable=1,
        saved_attribute_attributes={
            "valueof": {
                "parameter_initial": ["frequency", 440.0],
                "parameter_initial_enable": 1,
                # "parameter_invisible" : 1,
                # "parameter_longname" : "frequency",
                # "parameter_shortname" : "freq",
                # "parameter_type" : 3
            }
        },
    )
    phase = p.add_textbox(
        "attrui",
        maxclass="attrui",
        attr="phase",
        parameter_enable=1,
        saved_attribute_attributes={
            "valueof": {
                "parameter_initial": ["phase", 0.6],
                "parameter_initial_enable": 1,
                # "parameter_invisible" : 1,
                # "parameter_longname" : "phase",
                # "parameter_shortname" : "phase",
                # "parameter_type" : 3
            }
        },
    )
    p.add_line(freq, osc)
    p.add_line(phase, osc)
    p.save()

    fd = freq.to_dict()["box"]
    assert fd["maxclass"] == "attrui"
    assert fd["attr"] == "frequency"
    assert fd["parameter_enable"] == 1
    assert fd["saved_attribute_attributes"]["valueof"]["parameter_initial"] == [
        "frequency",
        440.0,
    ]
    pd = phase.to_dict()["box"]
    assert pd["attr"] == "phase"
    assert pd["saved_attribute_attributes"]["valueof"]["parameter_initial"] == [
        "phase",
        0.6,
    ]

    # both attrui feed the oscillator
    assert len(p._lines) == 2
    assert p._lines[0].source == [freq.id, 0]
    assert p._lines[0].destination == [osc.id, 0]
    assert p._lines[1].source == [phase.id, 0]
    assert p._lines[1].destination == [osc.id, 0]


# short-way
def test_attr():
    p = Patcher("outputs/test_attr.maxpat")
    osc = p.add_textbox("cycle~")
    freq = p.add_attr("frequency", 440.0)
    phase = p.add_attr("phase", 0.6, show_label=True)
    p.add_line(freq, osc)
    p.add_line(phase, osc)
    p.save()

    fd = freq.to_dict()["box"]
    assert fd["maxclass"] == "attrui"
    assert fd["attr"] == "frequency"
    assert fd["saved_attribute_attributes"]["valueof"]["parameter_initial"] == [
        "frequency",
        440.0,
    ]
    # show_label controls the attr_display flag
    assert freq.to_dict()["box"].get("attr_display") is False
    assert phase.to_dict()["box"].get("attr_display") is True

    assert len(p._lines) == 2
    assert p._lines[0].destination == [osc.id, 0]
    assert p._lines[1].destination == [osc.id, 0]
