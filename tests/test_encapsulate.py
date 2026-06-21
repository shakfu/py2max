"""Tests for Patcher.encapsulate()."""

import pytest

from py2max import Patcher


def _texts(patcher):
    return sorted(getattr(b, "text", "") for b in patcher._boxes)


def test_encapsulate_signal_chain():
    """metro -> [cycle~ -> gain~] -> dac: the middle pair is wrapped."""
    p = Patcher("outputs/enc_chain.maxpat")
    metro = p.add_textbox("metro 500")
    osc = p.add_textbox("cycle~ 440")
    gain = p.add_textbox("gain~")
    dac = p.add_textbox("ezdac~")
    p.add_line(metro, osc)
    p.add_line(osc, gain)
    p.add_line(gain, dac)

    sub_box = p.encapsulate([osc, gain], text="p dsp")
    sub = sub_box.subpatcher

    # Parent keeps metro + dac + the new subpatcher; osc/gain moved out.
    assert _texts(p) == ["ezdac~", "metro 500", "p dsp"]
    assert len(p._lines) == 2  # metro -> sub, sub -> dac
    assert sub_box.numinlets == 1
    assert sub_box.numoutlets == 1

    # The subpatcher holds the moved objects plus one inlet and one outlet.
    assert _texts(sub) == ["cycle~ 440", "gain~", "inlet", "outlet"]
    assert len(sub._lines) == 3  # cycle->gain, inlet->cycle, gain->outlet

    # Parent wires now run through the subpatcher box.
    parent_edges = {
        (p._objects[ln.src].text, p._objects[ln.dst].text) for ln in p._lines
    }
    assert parent_edges == {("metro 500", "p dsp"), ("p dsp", "ezdac~")}


def test_encapsulate_round_trips_through_file():
    p = Patcher("outputs/enc_rt.maxpat")
    a = p.add_textbox("metro 500")
    b = p.add_textbox("cycle~ 440")
    c = p.add_textbox("ezdac~")
    p.add_line(a, b)
    p.add_line(b, c)
    p.encapsulate([b], text="p mid")
    p.save()

    reloaded = Patcher.from_file("outputs/enc_rt.maxpat")
    subs = [x for x in reloaded._boxes if getattr(x, "text", "").startswith("p mid")]
    assert len(subs) == 1
    sub = subs[0].subpatcher
    assert len(sub._boxes) == 3  # cycle~ + inlet + outlet
    assert len(sub._lines) == 2


def test_encapsulate_dedups_ports_by_source():
    """One external source feeding two selected boxes shares a single inlet."""
    p = Patcher("outputs/enc_dedup.maxpat")
    src = p.add_textbox("metro 500")
    b1 = p.add_textbox("cycle~ 440")
    b2 = p.add_textbox("cycle~ 220")
    out = p.add_textbox("ezdac~")
    p.add_line(src, b1)
    p.add_line(src, b2)
    p.add_line(b1, out)
    p.add_line(b2, out)

    sub_box = p.encapsulate([b1, b2], text="p voices")
    # src fans into both selected boxes through ONE shared inlet.
    assert sub_box.numinlets == 1
    # b1 and b2 are distinct internal source ports -> two outlets.
    assert sub_box.numoutlets == 2
    # inlet feeds both internal boxes.
    sub = sub_box.subpatcher
    inlet = next(b for b in sub._boxes if getattr(b, "text", "") == "inlet")
    fanout = [ln for ln in sub._lines if ln.src == inlet.id]
    assert len(fanout) == 2


def test_encapsulate_isolated_boxes_have_no_ports():
    p = Patcher("outputs/enc_iso.maxpat")
    a = p.add_textbox("cycle~ 440")
    b = p.add_textbox("gain~")
    p.add_line(a, b)  # wholly internal
    p.add_textbox("ezdac~")  # untouched bystander

    sub_box = p.encapsulate([a, b], text="p iso")
    sub = sub_box.subpatcher
    # No crossing connections -> no generated ports.
    assert sub_box.numinlets == 0
    assert sub_box.numoutlets == 0
    assert _texts(sub) == ["cycle~ 440", "gain~"]
    assert len(sub._lines) == 1  # the internal connection is preserved
    assert len(p._lines) == 0


def test_encapsulate_empty_selection_raises():
    p = Patcher("outputs/enc_empty.maxpat")
    p.add_textbox("cycle~ 440")
    with pytest.raises(ValueError):
        p.encapsulate([])
