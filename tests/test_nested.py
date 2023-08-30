from py2max import Patcher, Box



def test_nested():
	boxes = []
	patchers = []
	p = Patcher.from_file("tests/data/nested.maxpat")
	for obj in p: # recursive iteration
		if isinstance(obj, Box):
			boxes.append(obj)
		if isinstance(obj, Patcher):
			patchers.append(obj)
	assert boxes[-1].text == "phasor~"


def test_find_in_nested():
	p = Patcher.from_file("tests/data/nested.maxpat")
	assert p.find("phasor").text == "phasor~"
	