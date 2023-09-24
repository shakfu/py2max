from py2max import Patcher

def test_scripting_name():
	p = Patcher(path="outputs/test_scripting_name.maxpat")
	p.add_box('cycle~ 440', varname='osc1')
	p.save()

