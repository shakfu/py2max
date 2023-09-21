from py2max import Patcher


def test_comment():
    p = Patcher(path='outputs/test_comment.maxpat')
    osc1 = p.add_textbox('cycle~ 440', comment="sine osc")
    fparam = p.add_floatparam('Frequency', 10.2, 0.0, 20.0)
    p.save()

