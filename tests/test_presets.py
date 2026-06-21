"""Tests for preset / pattrstorage scaffolding."""

from py2max import Patcher


def test_add_pattrstorage_names_storage():
    p = Patcher("outputs/preset_store.maxpat")
    store = p.add_pattrstorage("mypresets")
    assert store.text == "pattrstorage mypresets"
    assert store.numinlets == 1
    assert "saved_object_attributes" in store._kwds


def test_add_autopattr():
    p = Patcher("outputs/preset_auto.maxpat")
    auto = p.add_autopattr()
    assert auto.text == "autopattr"
    assert auto.numoutlets == 4


def test_add_preset_system_wires_autopattr_to_storage():
    p = Patcher("outputs/preset_sys.maxpat")
    auto, store = p.add_preset_system("presets")
    assert auto.text == "autopattr"
    assert store.text == "pattrstorage presets"
    # autopattr outlet 0 -> pattrstorage inlet 0
    assert any(ln.src == auto.id and ln.dst == store.id for ln in p._lines)


def test_enable_parameter_sets_parameter_attributes():
    p = Patcher("outputs/preset_param.maxpat")
    tog = p.add_textbox("toggle", varname="mute")
    returned = p.enable_parameter(tog, "Mute", shortname="mt", ptype=1, initial=1)

    assert returned is tog  # chainable
    assert tog._kwds["parameter_enable"] == 1
    valueof = tog._kwds["saved_attribute_attributes"]["valueof"]
    assert valueof["parameter_longname"] == "Mute"
    assert valueof["parameter_shortname"] == "mt"
    assert valueof["parameter_type"] == 1
    assert valueof["parameter_initial"] == [1]
    assert valueof["parameter_initial_enable"] == 1


def test_enable_parameter_without_initial():
    p = Patcher("outputs/preset_param2.maxpat")
    dial = p.add_textbox("live.dial")
    p.enable_parameter(dial, "Cutoff")
    valueof = dial._kwds["saved_attribute_attributes"]["valueof"]
    assert "parameter_initial" not in valueof
    assert valueof["parameter_longname"] == "Cutoff"


def test_preset_system_round_trips():
    p = Patcher("outputs/preset_rt.maxpat")
    tog = p.add_textbox("toggle", varname="mute")
    p.enable_parameter(tog, "Mute")
    p.add_preset_system("presets")
    p.save()

    reloaded = Patcher.from_file("outputs/preset_rt.maxpat")
    texts = [getattr(b, "text", "") for b in reloaded._boxes]
    assert "autopattr" in texts
    assert any(t.startswith("pattrstorage") for t in texts)
