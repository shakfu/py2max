from py2max import Patcher

CODE = """\
out1 = in1
out2 = in2
"""

# Max serializes multi-line code with CRLF line endings.
CODE_EMITTED = CODE.replace("\n", "\r\n")


class Case:
    def __init__(self, output_file):
        self.output_file = output_file

    def setup(self):
        self.p = Patcher(self.output_file)
        self.sbox = self.p.add_rnbo(numinlets=2, numoutlets=2)
        self.sp = self.sbox.subpatcher

        self.in1 = self.sp.add_textbox("inport left_in")
        self.in2 = self.sp.add_textbox("inport right_in")

        self.out1 = self.sp.add_textbox("outport left_out")
        self.out2 = self.sp.add_textbox("outport right_out")
        return self.sp

    def save(self, codebox):
        self.sp.add_line(self.in1, codebox)
        self.sp.add_line(self.in2, codebox, inlet=1)

        self.sp.add_line(codebox, self.out1)
        self.sp.add_line(codebox, self.out2, outlet=1)
        self.p.save()


class CaseTilde(Case):
    def setup(self):
        self.p = Patcher(self.output_file)
        self.sbox = self.p.add_rnbo(numinlets=2, numoutlets=2)
        self.sp = self.sbox.subpatcher

        self.in1 = self.sp.add_textbox("in~ 1")
        self.in2 = self.sp.add_textbox("in~ 2")

        self.out1 = self.sp.add_textbox("out~ 1")
        self.out2 = self.sp.add_textbox("out~ 2")
        return self.sp


def test_rnb_optimization():
    p = Patcher("outputs/test_rnbo_optimization.maxpat")
    rnbo = p.add_rnbo(saved_object_attributes=dict(optimization="O3"))
    p.save()

    # The rnbo object is a newobj wrapper around a subpatcher.
    assert rnbo.maxclass == "newobj"
    assert rnbo.subpatcher is not None
    assert rnbo.subpatcher.classnamespace == "rnbo"
    # The optimization attribute must be emitted verbatim on the box.
    box = rnbo.to_dict()["box"]
    assert box["saved_object_attributes"] == {"optimization": "O3"}
    # The saved patcher embeds the inner rnbo patcher.
    inner = p.to_dict()["patcher"]["boxes"][0]["box"]["patcher"]
    assert inner["classnamespace"] == "rnbo"


def test_rnb_codebox():
    case = Case("outputs/test_rnbo_codebox.maxpat")
    sp = case.setup()
    codebox = sp.add_codebox(
        code=CODE,  # required
        patching_rect=[200.0, 120.0, 200.0, 200.0],  # optional
    )
    case.save(codebox)

    assert sp.classnamespace == "rnbo"
    assert codebox.maxclass == "codebox"
    assert codebox.to_dict()["box"]["code"] == CODE_EMITTED
    # 2 inports + 2 outports + codebox.
    assert len(sp._boxes) == 5
    # Two inputs and two outputs wired to the codebox.
    assert len(sp._lines) == 4


def test_rnb_codebox_tilde():
    case = CaseTilde("outputs/test_rnbo_codebox_tilde.maxpat")
    sp = case.setup()
    codebox = sp.add_codebox_tilde(
        code=CODE,  # required
        patching_rect=[200.0, 120.0, 200.0, 200.0],  # optional
    )
    case.save(codebox)

    assert sp.classnamespace == "rnbo"
    assert codebox.maxclass == "codebox~"
    assert codebox.to_dict()["box"]["code"] == CODE_EMITTED
    # 2 in~ + 2 out~ + codebox~.
    assert len(sp._boxes) == 5
    assert len(sp._lines) == 4


def test_rnbo_textbox():
    case = Case("outputs/test_rnbo_textbox.maxpat")
    sp = case.setup()
    codebox = sp.add_textbox("codebox", code=CODE)
    case.save(codebox)

    assert sp.classnamespace == "rnbo"
    assert codebox.maxclass == "codebox"
    assert codebox.text == "codebox"
    assert codebox.to_dict()["box"]["code"] == CODE_EMITTED
    assert len(sp._boxes) == 5
    assert len(sp._lines) == 4


def test_rnbo_textbox_tilde():
    case = CaseTilde("outputs/test_rnbo_textbox_tilde.maxpat")
    sp = case.setup()
    codebox = sp.add_textbox("codebox~", code=CODE)
    case.save(codebox)

    assert sp.classnamespace == "rnbo"
    assert codebox.maxclass == "codebox~"
    assert codebox.text == "codebox~"
    assert codebox.to_dict()["box"]["code"] == CODE_EMITTED
    assert len(sp._boxes) == 5
    assert len(sp._lines) == 4


def populate_rnbo_patch(p, rnbo):
    sp = rnbo.subpatcher

    in1 = sp.add_textbox("in~ 1")
    in2 = sp.add_textbox("in~ 2")

    out1 = sp.add_textbox("out~ 1")
    out2 = sp.add_textbox("out~ 2")

    codebox = sp.add_textbox("codebox~", code=CODE)

    sp.add_line(in1, codebox)
    sp.add_line(in2, codebox, inlet=1)

    sp.add_line(codebox, out1)
    sp.add_line(codebox, out2, outlet=1)

    osc = p.add_textbox("cycle~ 440")
    dac = p.add_textbox("ezdac~")

    p.add_line(osc, rnbo)
    p.add_line(osc, rnbo, inlet=1)
    p.add_line(rnbo, dac)
    p.add_line(rnbo, dac, outlet=1, inlet=1)
    p.save()


def test_rnbo_ezdac():
    p = Patcher("outputs/test_rnbo_ezdac.maxpat")
    rnbo = p.add_rnbo(
        inletInfo=dict(
            IOInfo=[
                dict(comment="", index=1, tag="in1", type="signal"),
                dict(comment="", index=2, tag="in2", type="signal"),
            ],
        ),
        outletInfo=dict(
            IOInfo=[
                dict(comment="", index=1, tag="out1", type="signal"),
                dict(comment="", index=2, tag="out2", type="signal"),
            ],
        ),
        # outlettype = ['signal', 'signal', 'list'],
    )

    # inletInfo/outletInfo must be emitted verbatim on the rnbo box.
    box = rnbo.to_dict()["box"]
    assert [io["tag"] for io in box["inletInfo"]["IOInfo"]] == ["in1", "in2"]
    assert [io["tag"] for io in box["outletInfo"]["IOInfo"]] == ["out1", "out2"]
    assert all(io["type"] == "signal" for io in box["inletInfo"]["IOInfo"])

    populate_rnbo_patch(p, rnbo)

    # Parent: rnbo + cycle~ + ezdac~ with 4 connections.
    assert len(p._boxes) == 3
    assert len(p._lines) == 4
    # Inner rnbo subpatcher: 2 in~ + 2 out~ + codebox~, 4 connections.
    sp = rnbo.subpatcher
    assert sp.classnamespace == "rnbo"
    assert len(sp._boxes) == 5
    assert len(sp._lines) == 4


def test_rnbo_ezdac2():
    p = Patcher("outputs/test_rnbo_ezdac2.maxpat")
    rnbo = p.add_rnbo(numinlets=2, numoutlets=2)
    populate_rnbo_patch(p, rnbo)

    assert rnbo.numinlets == 2
    assert rnbo.numoutlets == 2
    assert rnbo.subpatcher.classnamespace == "rnbo"
    assert len(p._boxes) == 3
    assert len(p._lines) == 4
    assert len(rnbo.subpatcher._boxes) == 5
    assert len(rnbo.subpatcher._lines) == 4


def test_rnbo_add():
    p = Patcher("outputs/test_rnbo_add.maxpat")
    rnbo = p.add("rnbo~", numinlets=2, numoutlets=2)
    populate_rnbo_patch(p, rnbo)

    # p.add("rnbo~") must produce the same rnbo subpatcher wrapper.
    assert rnbo.maxclass == "newobj"
    assert rnbo.numinlets == 2
    assert rnbo.numoutlets == 2
    assert rnbo.subpatcher is not None
    assert rnbo.subpatcher.classnamespace == "rnbo"
    assert len(p._boxes) == 3
    assert len(p._lines) == 4
    assert len(rnbo.subpatcher._boxes) == 5
    assert len(rnbo.subpatcher._lines) == 4
