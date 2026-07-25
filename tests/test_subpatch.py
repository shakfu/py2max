import json

from py2max import Patcher


def test_subpatch():
    p = Patcher("outputs/test_subpatch.maxpat")
    sbox = p.add_subpatcher("p mysub")
    sp = sbox.subpatcher
    i = sp.add_textbox("inlet")
    g = sp.add_textbox("gain~")
    o = sp.add_textbox("outlet")
    osc = p.add_textbox("cycle~ 440")
    dac = p.add_textbox("ezdac~")
    sp.add_line(i, g)
    sp.add_line(g, o)
    p.add_line(osc, sbox)
    p.add_line(sbox, dac)
    p.save()

    # Subpatcher wrapper box and its inner patcher.
    assert sbox.maxclass == "newobj"
    assert sbox.text == "p mysub"
    assert sp is sbox.subpatcher
    assert sp.classnamespace == "box"
    # Inner: inlet -> gain~ -> outlet.
    assert len(sp._boxes) == 3
    assert len(sp._lines) == 2
    assert g.maxclass == "gain~"
    # Parent: subpatcher + cycle~ + ezdac~, wired osc -> sub -> dac.
    assert len(p._boxes) == 3
    assert len(p._lines) == 2
    # The saved parent embeds the inner patcher with its three boxes.
    box0 = p.to_dict()["patcher"]["boxes"][0]["box"]
    assert "patcher" in box0
    assert len(box0["patcher"]["boxes"]) == 3


def test_explicit_zero_port_counts_are_honored():
    """``Box`` must not promote a meaningful 0 to its default.

    Regression test: ``numoutlets or 1`` silently turned an explicit
    ``numoutlets=0`` into 1, so a deliberately source-less object still claimed
    an outlet.
    """
    p = Patcher("outputs/test_zero_ports.maxpat")
    assert p.add_textbox("nooutlets", numoutlets=0).numoutlets == 0
    assert p.add_textbox("noinlets", numinlets=0).numinlets == 0
    # Non-zero values and omitted values keep working.
    assert p.add_textbox("two", numoutlets=2).numoutlets == 2
    assert p.add_textbox("plain").numoutlets == 1


def test_subpatcher_ports_track_inner_inlet_outlet_objects():
    """A subpatcher box must declare as many ports as it actually has.

    The ``inlet``/``outlet`` objects are added after the box, so the counts fixed
    at construction go stale; Max renders the declared count, so a two-outlet
    subpatcher declaring one outlet emits an unconnectable second outlet.
    """
    p = Patcher("outputs/test_subpatch_ports.maxpat")
    sbox = p.add_subpatcher("p ports")
    sp = sbox.subpatcher
    for _ in range(2):
        sp.add_textbox("inlet")
    for _ in range(3):
        sp.add_textbox("outlet")

    box = json.loads(p.to_json())["patcher"]["boxes"][0]["box"]
    assert box["numinlets"] == 2
    assert box["numoutlets"] == 3
    assert box["outlettype"] == ["", "", ""]


def test_empty_subpatcher_keeps_its_default_ports():
    """An empty subpatcher is a stub; do not zero its ports.

    Port syncing only overrides a dimension it found objects for, so a nested
    patcher whose I/O this cannot interpret is left alone.
    """
    p = Patcher("outputs/test_subpatch_empty.maxpat")
    p.add_subpatcher("p empty")
    box = json.loads(p.to_json())["patcher"]["boxes"][0]["box"]
    assert (box["numinlets"], box["numoutlets"]) == (1, 1)


def test_gen_and_rnbo_ports_are_not_zeroed():
    """``gen~``/``rnbo~`` declare I/O with ``in``/``out``, not ``inlet``/``outlet``.

    They carry a nested patcher, so a naive port sync would count zero
    ``inlet``/``outlet`` objects and strip the box of its ports.
    """
    for factory in (lambda q: q.add_gen_tilde(), lambda q: q.add_rnbo("rnbo~")):
        p = Patcher("outputs/test_gen_ports.maxpat")
        factory(p)
        box = json.loads(p.to_json())["patcher"]["boxes"][0]["box"]
        assert box["numinlets"] >= 1
        assert box["numoutlets"] >= 1
