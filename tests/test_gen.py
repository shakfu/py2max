import pytest

from py2max import InvalidConnectionError, Patcher
from py2max.core.common import Rect


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


def test_gen_codebox_sized_to_code():
    # the default rect fits the code instead of a 66x22 textbox
    p = Patcher("outputs/test_gen_codebox_sized.maxpat")
    short = p.add_gen_codebox("out1 = in1;")
    long = p.add_gen_codebox("out1 = in1 * 0.5 + in2 * 0.25;\n" * 10)
    _, _, w1, h1 = short.patching_rect
    _, _, w2, h2 = long.patching_rect
    assert w1 >= 100 and h1 > 22
    assert w2 > w1 and h2 > h1
    # an explicit rect is kept as given
    box = p.add_gen_codebox("out1 = in1;", patching_rect=Rect(10, 10, 300, 200))
    assert tuple(box.patching_rect) == (10, 10, 300, 200)
    # codebox~ (inside gen~) is sized the same way
    g = Patcher("outputs/test_codebox_sized.maxpat")
    assert g.add_codebox_tilde("out1 = in1;").patching_rect[2] >= 100


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


def test_auto_placed_boxes_do_not_overlap():
    def overlap(a, b):
        ax, ay, aw, ah = a
        bx, by, bw, bh = b
        return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah

    for direction in ("horizontal", "vertical"):
        p = Patcher("outputs/test_no_overlap.maxpat", flow_direction=direction)
        p.add_gen_codebox("out1 = in1 * 0.5 + in2 * 0.25;\n" * 8)
        for _ in range(6):
            p.add("cycle~ 440")
        p.add("scope~")
        p.add("ezdac~")
        rects = [tuple(b.patching_rect) for b in p._boxes]
        for i, a in enumerate(rects):
            for b in rects[i + 1 :]:
                assert not overlap(a, b), (direction, a, b)


def test_explicit_rect_may_overlap():
    # only layout-issued positions move; a caller's rect is kept as given
    p = Patcher("outputs/test_explicit_overlap.maxpat")
    a = p.add("cycle~", patching_rect=Rect(10, 10, 100, 100))
    b = p.add("cycle~", patching_rect=Rect(20, 20, 100, 100))
    assert tuple(a.patching_rect)[:2] == (10, 10)
    assert tuple(b.patching_rect)[:2] == (20, 20)


def test_textbox_codebox_sized_to_code():
    p = Patcher("outputs/test_textbox_codebox.maxpat", classnamespace="rnbo")
    via_add = p.add("codebox~", code="out1 = in1;")
    via_method = p.add_codebox_tilde("out1 = in1;")
    assert via_add.patching_rect[2:] == via_method.patching_rect[2:]
