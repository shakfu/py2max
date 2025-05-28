from py2max import Patcher


def test_comment():
    p = Patcher(path="outputs/test_comment.maxpat")
    p.add_box("cycle~ 440", comment="sine osc")
    p.add_floatparam("Frequency", 10.2, 0.0, 20.0)
    p.save()
