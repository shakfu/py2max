from .. import Patcher



def test_rnb_codebox():

	p = Patcher('outputs/test_rnb_codebox.maxpat')
	sbox = p.add_rnbo()
	sp = sbox.subpatcher

	in1 = sp.add_textbox('inport left_in')
	in2 = sp.add_textbox('inport right_in')

	out1 = sp.add_textbox('outport left_out')
	out2 = sp.add_textbox('outport right_out')

	_code = """\
	out1 = in1
	out2 = in2
	"""

	codebox = sp.add_codebox(
		code=_code,								   # required
		patching_rect=[200.0, 120.0, 200.0, 200.0] # optional
	)

	sp.add_line(in1, codebox)
	sp.add_line(in2, codebox, inlet=1)

	sp.add_line(codebox, out1)
	sp.add_line(codebox, out2, outlet=1)
	p.save()



def test_rnbo_textbox():

	p = Patcher('outputs/test_rnbo_textbox.maxpat')
	sbox = p.add_rnbo()
	sp = sbox.subpatcher

	in1 = sp.add_textbox('inport left_in')
	in2 = sp.add_textbox('inport right_in')

	out1 = sp.add_textbox('outport left_out')
	out2 = sp.add_textbox('outport right_out')

	_code = """\
	out1 = in1
	out2 = in2
	"""

	_code.replace('\n', '\r\n')
	codebox = sp.add_textbox('codebox',
		maxclass = "codebox",
		code=_code,
	    rnbo_extra_attributes=dict( # required
	    	code=_code,
	    	hot=0,
	    ),
	    patching_rect=[191.0, 118.0, 200.0, 200.0] # optional
	)

	sp.add_line(in1, codebox)
	sp.add_line(in2, codebox, inlet=1)

	sp.add_line(codebox, out1)
	sp.add_line(codebox, out2, outlet=1)
	p.save()

if __name__ == '__main__':
	test_rnb_codebox()
	test_rnbo_textbox()

