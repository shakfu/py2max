
from py2max import Patcher

# minimal requirement


def test_attrui():
    p = Patcher('outputs/test_attrui.maxpat')
    osc = p.add_textbox('cycle~')
    freq = p.add_textbox('attrui',
        maxclass="attrui",
        attr="frequency",
        parameter_enable=1,
        saved_attribute_attributes = {
            'valueof': {
                "parameter_initial" : [ "frequency", 440. ],
                "parameter_initial_enable" : 1,
                # "parameter_invisible" : 1,
                # "parameter_longname" : "frequency",
                # "parameter_shortname" : "freq",
                # "parameter_type" : 3
            }
        }
    )
    phase = p.add_textbox('attrui',
        maxclass="attrui",
        attr="phase",
        parameter_enable=1,
        saved_attribute_attributes = {
            'valueof': {
                "parameter_initial" : [ "phase", 0.6 ],
                "parameter_initial_enable" : 1,
                # "parameter_invisible" : 1,
                # "parameter_longname" : "phase",
                # "parameter_shortname" : "phase",
                # "parameter_type" : 3
            }
        }
    )
    p.add_line(freq, osc)
    p.add_line(phase, osc)
    p.save()


# short-way
def test_attr():
    p = Patcher('outputs/test_attr.maxpat')
    osc = p.add_textbox('cycle~')
    freq = p.add_attr("frequency", 440.)
    phase = p.add_attr("phase", 0.6, show_label=True)
    p.add_line(freq, osc)
    p.add_line(phase, osc)
    p.save()

