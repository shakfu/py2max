
from py2max import Patcher


def test_beap():
    p = Patcher(path='outputs/test_beap.maxpat')
    p.add_beap('bp.LFO.maxpat')
    # p.add('bpatcher bp.LFO.maxpat', extract=1, numinlets=0, numoutlets=5, outlettype=[
    #       "signal", "signal", "signal", "signal", "signal"], varname="bp.LFO")
    p.save()

