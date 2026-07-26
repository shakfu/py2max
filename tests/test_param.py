import json

from py2max import Patcher


def test_param():
    p = Patcher("outputs/test_param.maxpat")
    fp = p.add_floatparam("frequency1", 230, 0, 1000)
    ip = p.add_intparam("size", 341, 0, 1000)
    p.save()

    # each param adds a value box plus a label comment box
    assert len(p._boxes) == 4
    assert [b.maxclass for b in p._boxes] == [
        "flonum",
        "number",
        "comment",
        "comment",
    ]

    fbox = fp.to_dict()["box"]
    assert fbox["maxclass"] == "flonum"
    assert fbox["parameter_enable"] == 1
    fparam = fbox["saved_attribute_attributes"]["valueof"]
    assert fparam["parameter_longname"] == "frequency1"
    assert fparam["parameter_initial"] == [230]
    assert fparam["parameter_type"] == 0
    assert fbox["minimum"] == 0
    assert fbox["maximum"] == 1000

    ibox = ip.to_dict()["box"]
    assert ibox["maxclass"] == "number"
    assert ibox["parameter_enable"] == 1
    iparam = ibox["saved_attribute_attributes"]["valueof"]
    assert iparam["parameter_longname"] == "size"
    assert iparam["parameter_initial"] == [341]
    assert iparam["parameter_type"] == 1
    assert iparam["parameter_mmax"] == 1000


def _find_nulls(node, path=""):
    """Every path in `node` whose value is None."""
    if isinstance(node, dict):
        out = []
        for key, value in node.items():
            here = f"{path}.{key}" if path else key
            out.extend([here] if value is None else _find_nulls(value, here))
        return out
    if isinstance(node, (list, tuple)):
        return [
            p for i, v in enumerate(node) for p in _find_nulls(v, f"{path}[{i}]")
        ]
    return []


def test_unset_param_bounds_are_absent_not_null():
    """Max distinguishes an absent key from a null one.

    `add_intparam` wrote `parameter_mmax` unconditionally, so an unset maximum
    shipped as `"parameter_mmax": null` -- one level below the shallow scrub in
    `Box._remove_none_entries`, which is why nothing removed it. `add_floatparam`
    omitted the key entirely; the asymmetry was the tell.
    """
    p = Patcher("outputs/test_param_nulls.maxpat")

    for box in (p.add_intparam("i"), p.add_floatparam("f")):
        valueof = box.to_dict()["box"]["saved_attribute_attributes"]["valueof"]
        assert "parameter_mmax" not in valueof
        assert "minimum" not in box.to_dict()["box"]
        assert "maximum" not in box.to_dict()["box"]

    # a bound that *was* given still arrives
    box = p.add_intparam("j", initial=1, maximum=127)
    valueof = box.to_dict()["box"]["saved_attribute_attributes"]["valueof"]
    assert valueof["parameter_mmax"] == 127


def test_no_nulls_anywhere_in_a_representative_patch():
    """A null in the emitted JSON is a key Max should not have been given.

    Reads back `to_json()`, not `to_dict()`: only the former renders the boxes,
    so inspecting the dict would examine an empty patcher and assert nothing.
    """
    p = Patcher("outputs/test_no_nulls.maxpat")
    p.add_floatparam("freq")
    p.add_intparam("size")
    p.add_textbox("cycle~ 440")
    p.add_message("1 2 3")
    p.add_comment("a note")
    p.add_subpatcher("p sub")
    p.add_coll("mycoll", dictionary={"a": 1})
    p.add_umenu()
    p.add_floatbox()
    p.add_intbox()

    emitted = json.loads(p.to_json())
    assert emitted["patcher"]["boxes"], "nothing was rendered, so nothing was checked"

    nulls = _find_nulls(emitted)
    assert not nulls, f"null values emitted at: {nulls}"


def test_none_elements_of_a_list_survive():
    """Lists are positional -- scrubbing an element would change the arity."""
    p = Patcher("outputs/test_list_nulls.maxpat")
    box = p.add_textbox("cycle~ 440", outlettype=["signal", None])
    assert box.to_dict()["box"]["outlettype"] == ["signal", None]
