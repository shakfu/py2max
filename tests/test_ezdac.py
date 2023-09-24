
from py2max import Patcher


def test_ezdac():
    p = Patcher(path='outputs/test_ezdac.maxpat')
    osc = p.add_box('cycle~ 440')
    dac = p.add_box('ezdac~')
    p.add_line(osc, dac)
    p.add_line(osc, dac, inlet=1)
    p.save()

