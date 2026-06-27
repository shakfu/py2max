import pytest

from py2max import InvalidConnectionError, Patcher


def test_gen():
    p = Patcher("outputs/test_gen.maxpat")
    sbox = p.add_gen("@title windowSync")
    sp = sbox.subpatcher
    i3 = sp.add_textbox("in 3")
    i4 = sp.add_textbox("in 4")
    plus = sp.add_textbox("+")
    sp.add_line(i3, plus)
    sp.add_line(i4, plus)
    p.save()


def test_gen_tilde():
    p = Patcher("outputs/test_gen_tilde.maxpat")
    sbox = p.add_gen_tilde("@nocache 0")  # also p.add_gen(tilde=True)
    sp = sbox.subpatcher
    i1 = sp.add_textbox("in 1")
    i2 = sp.add_textbox("in 2")
    o1 = sp.add_textbox("out 1")
    plus = sp.add_textbox("+")
    sp.add_line(i1, plus)
    sp.add_line(i2, plus, inlet=1)
    sp.add_line(plus, o1)
    p.save()


def test_gen_codebox():
    code = "Param fb(0.5, min=0.0, max=0.95);\nout1 = in1 * fb;"
    p = Patcher("outputs/test_gen_codebox.maxpat")
    box = p.add_gen_codebox(code)
    d = box.to_dict()["box"]

    # standalone gen.codebox~ lives directly in a regular ("box") patcher,
    # unlike the inner "codebox~" emitted by add_codebox.
    assert box.maxclass == "gen.codebox~"
    assert p.classnamespace == "box"
    assert box.numinlets == 1
    assert box.numoutlets == 1
    assert d["outlettype"] == ["signal"]
    assert d["fontname"] == "<Monospaced>"
    # newlines are normalized to CRLF as Max expects
    assert "\r\n" in d["code"]
    p.save()


def test_gen_codebox_multi_io():
    p = Patcher("outputs/test_gen_codebox_multi.maxpat")
    box = p.add_gen_codebox("out1 = in1;\nout2 = in2;", numinlets=2, numoutlets=2)
    assert box.numinlets == 2
    assert box.numoutlets == 2
    d = box.to_dict()["box"]
    assert d["outlettype"] == ["signal", "signal"]
    p.save()


def test_gen_codebox_io_autoderived_from_code():
    # inlet/outlet counts follow the highest in<N>/out<N> referenced in the code
    p = Patcher("outputs/test_gen_codebox_auto.maxpat")
    box = p.add_gen_codebox("out1 = in1 + in3;\nout2 = in2;")
    assert box.numinlets == 3
    assert box.numoutlets == 2
    # always at least one signal inlet and outlet, even with no references
    bare = p.add_gen_codebox("history h(0.);\nout1 = h;")
    assert bare.numinlets == 1
    assert bare.numoutlets == 1


def test_gen_codebox_string_dispatch():
    p = Patcher("outputs/test_gen_codebox_dispatch.maxpat")
    box = p.add("gen.codebox~ out1 = in1 * 0.5;")
    assert box.maxclass == "gen.codebox~"
    assert box.to_dict()["box"]["code"].startswith("out1 = in1 * 0.5;")


def test_gen_codebox_connection_validation():
    # validation uses the codebox's declared (dynamic) I/O, not static maxref
    p = Patcher("outputs/test_gen_codebox_validate.maxpat", validate_connections=True)
    box = p.add_gen_codebox("out1 = in1 + in3;\nout2 = in2;")  # 3 in, 2 out
    dac = p.add("ezdac~")
    src = p.add("cycle~ 440")

    # connecting from the second outlet is valid (codebox has 2 outlets)
    p.add_line(box, dac, outlet=1)
    # connecting into the third inlet is valid (codebox has 3 inlets)
    p.add_line(src, box, inlet=2)

    # out-of-range outlet/inlet are rejected against the box's own counts
    with pytest.raises(InvalidConnectionError):
        p.add_line(box, dac, outlet=5)
    with pytest.raises(InvalidConnectionError):
        p.add_line(src, box, inlet=9)
