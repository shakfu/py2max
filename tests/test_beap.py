from py2max import Patcher


def test_beap():
    p = Patcher("outputs/test_beap.maxpat")
    beap = p.add_beap("bp.LFO.maxpat")
    # p.add('bpatcher bp.LFO.maxpat', extract=1, numinlets=0, numoutlets=5, outlettype=[
    #       "signal", "signal", "signal", "signal", "signal"], varname="bp.LFO")
    p.save()

    assert len(p._boxes) == 1
    assert beap.maxclass == "bpatcher"
    box = beap.to_dict()["box"]
    assert box["maxclass"] == "bpatcher"
    assert box["name"] == "bp.LFO.maxpat"
    assert box["extract"] == 1
