from py2max import Patcher

def test_scripting_name():
	p = Patcher("outputs/test_scripting_name.maxpat")
	p.add_textbox('cycle~ 440', varname='osc1')
	p.save()

