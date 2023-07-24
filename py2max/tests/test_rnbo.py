from .. import Patcher

CODE = """\
out1 = in1
out2 = in2
"""

class Case:
    def __init__(self, output_file):
        self.output_file = output_file

    def setup(self):
        self.p = Patcher(self.output_file)
        self.sbox = self.p.add_rnbo()
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
        self.p = Patcher(self.output_file)
        self.sbox = self.p.add_rnbo()
        self.sp = self.sbox.subpatcher

        self.in1 = self.sp.add_textbox('in~ 1')
        self.in2 = self.sp.add_textbox('in~ 2')

        self.out1 = self.sp.add_textbox('out~ 1')
        self.out2 = self.sp.add_textbox('out~ 2')
        return self.sp


def test_rnb_codebox():
    case = Case('outputs/test_rnbo_codebox.maxpat')
    sp = case.setup()
    codebox = sp.add_codebox(
        code=CODE,                                 # required
        patching_rect=[200.0, 120.0, 200.0, 200.0] # optional
    )
    case.save(codebox)

def test_rnb_codebox_tilde():
    case = CaseTilde('outputs/test_rnbo_codebox_tilde.maxpat')
    sp = case.setup()
    codebox = sp.add_codebox(
        code=CODE,                                 # required
        tilde=True,
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


if __name__ == '__main__':
    test_rnb_codebox()
    test_rnb_codebox_tilde()
    test_rnbo_textbox()
    test_rnbo_textbox_tilde()

