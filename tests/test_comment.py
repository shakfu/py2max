from py2max import Patcher


def test_comment():
    p = Patcher("outputs/test_comment.maxpat")
    p.add_textbox("cycle~ 440", comment="sine osc")
    p.add_floatparam("Frequency", 10.2, 0.0, 20.0)
    p.save()
