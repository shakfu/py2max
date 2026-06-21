"""Tests for multichannel (mc.) and poly~ helpers."""

from py2max import Patcher


def test_add_mc_prefixes_and_chans():
    p = Patcher("outputs/mc.maxpat")
    assert p.add_mc("cycle~ 440", chans=4).text == "mc.cycle~ 440 @chans 4"


def test_add_mc_no_double_prefix():
    p = Patcher("outputs/mc2.maxpat")
    assert p.add_mc("mc.pack~ 8").text == "mc.pack~ 8"


def test_add_mc_without_chans():
    p = Patcher("outputs/mc3.maxpat")
    assert p.add_mc("noise~").text == "mc.noise~"


def test_add_poly():
    p = Patcher("outputs/poly.maxpat")
    assert p.add_poly("mysynth", 8).text == "poly~ mysynth 8"


def test_add_poly_default_voices():
    p = Patcher("outputs/poly2.maxpat")
    assert p.add_poly("voice").text == "poly~ voice 1"


def test_mc_objects_connect_and_round_trip():
    p = Patcher("outputs/mc_chain.maxpat")
    osc = p.add_mc("cycle~ 440", chans=4)
    out = p.add_mc("live.gain~")
    p.add_line(osc, out)  # one cable carries all channels
    p.save()

    reloaded = Patcher.from_file("outputs/mc_chain.maxpat")
    assert len(reloaded._boxes) == 2
    assert len(reloaded._lines) == 1
