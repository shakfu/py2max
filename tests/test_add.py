import json

import pytest
from py2max import Patcher
from py2max.core.factory import _first_param_name


def test_add():
    p = Patcher("outputs/test_add.maxpat")

    # should fail
    with pytest.raises(NotImplementedError):
        p.add(p)

    # float param
    p.add(10.2, "param1")
    p.add(0.56, name="param2")
    # floatbox
    p.add(1.2)

    # should fail
    with pytest.raises(ValueError):
        p.add(0.41, name=p)

    # int param
    p.add(10, "param3")
    p.add(56, name="param4")
    # intbox
    p.add(2)

    # should fail
    with pytest.raises(ValueError):
        p.add(2, name=p)

    # message
    p.add("m hello")

    # comment
    p.add("c my comment")

    # textbox
    p.add("cycle~ 440")

    # subpatcher
    box = p.add("p mysub")
    assert box.subpatcher

    # gen~
    gen = p.add("gen~")
    assert gen.subpatcher

    # coll
    p.add("coll", dictionary=dict(a=1, b=2))

    # dict
    p.add("dict", dictionary=dict(a=1, b=2))

    # table & itable
    p.add("table", array=list(range(128)))
    p.add("itable", array=list(range(128)))

    # umenu
    p.add("umenu", items=["a", "b", "c"])

    # bpatcher
    p.add("bpatcher bp.LFO.maxpat", extract=1)

    p.save()


# -- dispatcher keyword collisions -------------------------------------------
#
# `add()` derives the first argument of its target method from the value it was
# handed, then forwards `**kwds` to the same call. A caller keyword naming that
# parameter used to be a hard `TypeError: got multiple values for argument`.
# The explicit value now wins.


@pytest.mark.parametrize(
    "args, kwds, key, wins",
    [
        # the target's first parameter, by name, for each `add()` branch
        ((10,), {"initial": 3}, None, None),  # _add_int -> add_intparam
        ((1.5,), {"initial": 0.2}, None, None),  # _add_float -> add_floatparam
        (("cycle~ 440",), {"text": "saw~ 220"}, "text", "saw~ 220"),  # add_textbox
        (("p derived",), {"text": "explicit"}, "text", "explicit"),  # add_subpatcher
        (("gen.codebox~ x",), {"code": "out1 = in1;"}, "code", "out1 = in1;"),
        (("rnbo~ derived",), {"text": "rnbo~ explicit"}, "text", "rnbo~ explicit"),
        # a second parameter of the target, which never collided but must still
        # reach it rather than being swallowed as a box property
        ((10,), {"maximum": 127}, None, None),
    ],
)
def test_add_caller_keyword_wins(args, kwds, key, wins):
    p = Patcher("outputs/test_add_kwds.maxpat")
    box = p.add(*args, **kwds)  # must not raise TypeError
    if key is not None:
        assert box.to_dict()["box"][key] == wins


def test_add_caller_keyword_reaches_target_parameter():
    """A forwarded keyword must land on the target's parameter, not on the box.

    `initial=`/`maximum=` are `add_intparam` parameters; if the dispatcher let
    them fall through to `**kwds` they would be emitted as box properties.
    """
    p = Patcher("outputs/test_add_kwds_target.maxpat")

    box = p.add(10, initial=3, maximum=127)
    emitted = box.to_dict()["box"]
    assert emitted["saved_attribute_attributes"]["valueof"]["parameter_initial"] == [3]
    assert emitted["maximum"] == 127
    assert "initial" not in emitted


def test_add_maxclass_methods_accept_their_first_param_as_keyword():
    """Driven off `_maxclass_methods` so a new entry cannot silently regress.

    Every specialized method reached by `add()` takes its subject positionally
    (`text`, `name`, `prefix`, ...); each must also accept it by keyword.
    """
    p = Patcher("outputs/test_add_maxclass_kwds.maxpat")
    assert p._maxclass_methods, "nothing to check -- dispatch table is empty"

    for maxclass, method in p._maxclass_methods.items():
        first = _first_param_name(method)
        assert first is not None, f"{maxclass}: no positional parameter to fill"

        box = p.add(f"{maxclass} derived", **{first: "explicit"})
        emitted = json.dumps(box.to_dict())
        assert "explicit" in emitted, f"{maxclass}: caller {first}= did not reach box"
        assert "derived" not in emitted, f"{maxclass}: derived value won over {first}="


def test_add_param_name_does_not_leak_into_box():
    """`.add(<number>, name=...)` names the parameter; it is not a box property.

    It used to be read for `longname` *and* left in `**kwds`, so a stray `name`
    key shipped into the emitted patch.
    """
    p = Patcher("outputs/test_add_name_leak.maxpat")

    for value in (1.5, 10):
        box = p.add(value, name="freq")
        emitted = box.to_dict()["box"]
        assert "name" not in emitted
        valueof = emitted["saved_attribute_attributes"]["valueof"]
        assert valueof["parameter_longname"] == "freq"

    # positional form is unchanged, and still wins over a `name=` keyword
    box = p.add(2.5, "positional", name="ignored")
    valueof = box.to_dict()["box"]["saved_attribute_attributes"]["valueof"]
    assert valueof["parameter_longname"] == "positional"
    assert "name" not in box.to_dict()["box"]


def test_add_param_rejects_non_string_name():
    p = Patcher("outputs/test_add_bad_name.maxpat")
    for value in (0.41, 2):
        with pytest.raises(ValueError):
            p.add(value, name=p)
        with pytest.raises(ValueError):
            p.add(value, p)


def test_add_umenu_without_items():
    """`items` is optional, so omitting it must not raise."""
    p = Patcher("outputs/test_add_umenu.maxpat")
    assert p.add_umenu().to_dict()["box"]["items"] == []
    assert p.add("umenu").to_dict()["box"]["items"] == []
    assert p.add_umenu(items=["a", "b"]).to_dict()["box"]["items"] == [
        "a",
        ",",
        "b",
        ",",
    ]
