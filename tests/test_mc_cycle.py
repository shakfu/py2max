
from py2max import Patcher


def test_mc_cycle():
    p = Patcher('outputs/test_mc_cycle.maxpat')
    obj = p.add_textbox('mc.cycle~ 440')
    p.save()

