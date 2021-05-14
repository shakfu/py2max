
from .. import Patcher


def test_mc_cycle():
    p = Patcher('outputs/test_mc_cycle.maxpat')
    obj = p.add_textbox('mc.cycle~ 440')
    p.save()


if __name__ == '__main__':
    test_mc_cycle()
