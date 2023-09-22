from py2max import Patcher
from py2max.common import Rect

CODE = """\
out1 = in1
out2 = in2
"""

class Case:
    def __init__(self, output_file):
        self.output_file = output_file

    def setup(self):
        self.p = Patcher(path=self.output_file)
        self.sbox = self.p.add_rnbo(numinlets=2, numoutlets=2)
        self.sp = self.sbox.subpatcher

        self.in1 = self.sp.add_textbox('inport left_in')
        self.in2 = self.sp.add_textbox('inport right_in')

        self.out1 = self.sp.add_textbox('outport left_out')
        self.out2 = self.sp.add_textbox('outport right_out')
        return self.sp

    def save(self, codebox):
        self.sp.add_line(self.in1, codebox)
        self.sp.add_line(self.in2, codebox, inlet=1)

        self.sp.add_line(codebox, self.out1)
        self.sp.add_line(codebox, self.out2, outlet=1)
        self.p.save()


class CaseTilde(Case):

    def setup(self):
        self.p = Patcher(path=self.output_file)
        self.sbox = self.p.add_rnbo(numinlets=2, numoutlets=2)
        self.sp = self.sbox.subpatcher

        self.in1 = self.sp.add_textbox('in~ 1')
        self.in2 = self.sp.add_textbox('in~ 2')

        self.out1 = self.sp.add_textbox('out~ 1')
        self.out2 = self.sp.add_textbox('out~ 2')
        return self.sp

def test_rnb_optimization():
    p = Patcher(path='outputs/test_rnbo_optimization.maxpat')
    sbox = p.add_rnbo(saved_object_attributes=dict(optimization="O3"))
    p.save()


def test_rnb_codebox():
    case = Case('outputs/test_rnbo_codebox.maxpat')
    sp = case.setup()
    codebox = sp.add_codebox(
        code=CODE,                                 # required
        patching_rect=Rect(200.0, 120.0, 200.0, 200.0) # optional
    )
    case.save(codebox)

def test_rnb_codebox_tilde():
    case = CaseTilde('outputs/test_rnbo_codebox_tilde.maxpat')
    sp = case.setup()
    codebox = sp.add_codebox_tilde(
        code=CODE,                                 # required
        patching_rect=[200.0, 120.0, 200.0, 200.0] # optional
    )
    case.save(codebox)

def test_rnbo_textbox():
    case = Case('outputs/test_rnbo_textbox.maxpat')
    sp = case.setup()
    codebox = sp.add_textbox('codebox', code=CODE)
    case.save(codebox)

def test_rnbo_textbox_tilde():
    case = CaseTilde('outputs/test_rnbo_textbox_tilde.maxpat')
    sp = case.setup()
    codebox = sp.add_textbox('codebox~', code=CODE)
    case.save(codebox)


def populate_rnbo_patch(p, rnbo):
    sp = rnbo.subpatcher

    in1 = sp.add_textbox('in~ 1')
    in2 = sp.add_textbox('in~ 2')

    out1 = sp.add_textbox('out~ 1')
    out2 = sp.add_textbox('out~ 2')

    codebox = sp.add_textbox('codebox~', code=CODE)

    sp.add_line(in1, codebox)
    sp.add_line(in2, codebox, inlet=1)

    sp.add_line(codebox, out1)
    sp.add_line(codebox, out2, outlet=1)

    osc = p.add_textbox('cycle~ 440')
    dac = p.add_textbox('ezdac~')

    p.add_line(osc, rnbo)
    p.add_line(osc, rnbo, inlet=1)
    p.add_line(rnbo, dac)
    p.add_line(rnbo, dac, outlet=1, inlet=1)
    p.save()


def test_rnbo_ezdac():
    p = Patcher(path='outputs/test_rnbo_ezdac.maxpat')
    rnbo = p.add_rnbo(

        inletInfo=dict(
            IOInfo=[
                dict(
                    comment='',
                    index= 1,
                    tag='in1',
                    type='signal'
                ),
                dict(
                    comment='',
                    index= 2,
                    tag='in2',
                    type='signal'
                ),
            ],
        ),
        outletInfo=dict(
            IOInfo=[
                dict(
                    comment='',
                    index= 1,
                    tag='out1',
                    type='signal'
                ),
                dict(
                    comment='',
                    index= 2,
                    tag='out2',
                    type='signal'
                ),
            ],
        ),
      # outlettype = ['signal', 'signal', 'list'],
    )

    populate_rnbo_patch(p, rnbo)


def test_rnbo_ezdac2():
    p = Patcher(path='outputs/test_rnbo_ezdac2.maxpat')
    rnbo = p.add_rnbo(numinlets=2, numoutlets=2)
    sp = rnbo.subpatcher
    populate_rnbo_patch(p, rnbo)


def test_rnbo_add():
    p = Patcher(path='outputs/test_rnbo_add.maxpat')
    rnbo = p.add("rnbo~", numinlets=2, numoutlets=2)
    populate_rnbo_patch(p, rnbo)


