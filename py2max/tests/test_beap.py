
from .. import Patcher


def test_beap():
    p = Patcher('outputs/test_beap.maxpat')
    p.add_beap('bp.LFO.maxpat')
    # p.add('bpatcher bp.LFO.maxpat', extract=1, numinlets=0, numoutlets=5, outlettype=[
    #       "signal", "signal", "signal", "signal", "signal"], varname="bp.LFO")
    p.save()


if __name__ == '__main__':
    test_beap()
