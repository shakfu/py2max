from py2max import Patcher
from py2max.common import Rect

class group(list):
	def move_x(self, value):
		for i in self:
			x, y, w, h = i.patching_rect
			x += value
			i.patching_rect = Rect(x,y,w,h)

	def move_y(self, value):
		for i in self:
			x, y, w, h = i.patching_rect
			y += value
			i.patching_rect = Rect(x,y,w,h)




def test_group():
    p = Patcher(path='outputs/test_group.maxpat')

    osc1 = p.add_box('cycle~ 440', patching_rect=Rect(100, 148, 62, 22))
    gain = p.add_box('gain~', patching_rect=Rect(100, 204, 175, 21))
    dac = p.add_box('ezdac~', patching_rect=Rect(100, 402, 45, 45))

    p.add_line(osc1, gain)
    p.add_line(gain, dac)

    g = group((osc1, gain, dac))
    g.move_x(50)
    g.move_y(50)

    assert g[0].patching_rect[0] == 150.0
    assert g[1].patching_rect[0] == 150.0
    assert g[2].patching_rect[0] == 150.0

    assert g[0].patching_rect[1] == 198.0
    assert g[1].patching_rect[1] == 254.0
    assert g[2].patching_rect[1] == 452.0

    p.save()
