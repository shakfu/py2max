from py2max import Patcher


def test_linking1():
	p = Patcher("outputs/test_linking1.maxpat", layout="vertical")
	osc = p.add_textbox('cycle~ 440')
	gain = p.add_textbox('live.gain~')
	dac = p.add_textbox('ezdac~')
	limi = p.add_textbox('limi~ 2 @threshold -1.')

	p.add_line(osc, gain)			# osc outlet 0 -> gain inlet 0
	p.add_line(osc, gain, inlet=1)  # osc outlet 0 -> gain inlet 1

	p.add_line(gain, limi) 			# gain outlet 0 -> limi inlet 0
	p.add_line(gain, limi, outlet=1, inlet=1) # gain outlet 1 -> limi inlet 1

	# def add_line(src_obj: "Box", dst_obj: "Box", inlet: int = 0, outlet: int = 0) -> "Patchline"
	p.add_line(limi, dac) 			# limi outlet 0 -> dac inlet 0
	p.add_line(limi, dac, outlet=1, inlet=1)	# limi outlet 1 -> dac inlet 1)
	
	p.save()


def test_linking2():
	p = Patcher("outputs/test_linking2.maxpat", layout="vertical")
	osc = p.add('cycle~ 440')
	gain = p.add('live.gain~')
	dac = p.add('ezdac~')
	limi = p.add('limi~ 2 @threshold -1.')

	p.link(osc, gain)			# osc outlet 0 -> gain inlet 0
	p.link(osc, gain, inlet=1)  # osc outlet 0 -> gain inlet 1

	p.link(gain, limi) 			# gain outlet 0 -> limi inlet 0
	p.link(gain, limi, outlet=1, inlet=1) # gain outlet 1 -> limi inlet 1

	p.link(limi, dac) 			# limi outlet 0 -> dac inlet 0
	p.link(limi, dac, outlet=1, inlet=1)	# limi outlet 1 -> dac inlet 1)
	
	p.save()