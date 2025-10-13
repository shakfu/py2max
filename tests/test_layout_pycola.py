"""adaptagrams.org LIBCOLA library, wrapped by pycola

This implementation, `pycola`, is created by a sister
project: https://github.com/shakfu/pycola

"""

import pytest

try:
    from pycola.layout import Layout

    # from adaptagrams import Graph, DialectNode, HolaOpts, doHOLA
    HAS_PYCOLA = True
except ImportError:
    HAS_PYCOLA = False

from py2max import Patcher
from py2max.common import Rect


class ColaPatcher(Patcher):
    def reposition(self):
        # add nodes
        nodes = []
        id_to_index = {}
        for i, box in enumerate(self._boxes):
            x, y, h, w = box.patching_rect

            node = {
                "id": box.id,
                "x": x,
                "y": y,
                "width": w,  # Add this
                "height": h,  # Add this
            }
            nodes.append(node)
            id_to_index[box.id] = i  # Map ID to index

        # Build edges using indices
        edges = []
        for line in self._lines:
            edge = {
                "source": id_to_index[line.src],  # Use index, not ID
                "target": id_to_index[line.dst],  # Use index, not ID
            }
            edges.append(edge)

        layout = Layout()
        layout.nodes(nodes)
        layout.links(edges)
        layout.start()

        # scale = self.rect[2]
        scale = 1
        repos = []
        for node in nodes:
            repos.append((node["x"] * scale, node["y"] * scale))

        _boxes = []
        for box, xy in zip(self._boxes, repos):
            x, y, h, w = box.patching_rect
            newx, newy = xy
            box.patching_rect = Rect(newx, newy, h, w)
            _boxes.append(box)
        self.boxes = _boxes


@pytest.mark.skipif(not HAS_PYCOLA, reason="requires pycola")
def test_graph():
    p = ColaPatcher("outputs/test_layout_pycola.maxpat")

    fbox = p.add_floatbox
    ibox = p.add_intbox
    tbox = p.add_textbox
    link = p.add_line

    # objects
    freq1 = fbox()
    freq2 = fbox()
    phase = fbox()
    osc1 = tbox("cycle~")
    osc2 = tbox("cycle~")
    amp1 = fbox()
    amp2 = fbox()
    mul1 = tbox("*~")
    mul2 = tbox("*~")
    add1 = tbox("+~")
    dac = tbox("ezdac~")
    scop = tbox("scope~")
    scp1 = ibox()
    scp2 = ibox()

    # lines
    link(freq1, osc1)
    link(osc1, mul1)
    link(mul1, add1)
    link(amp1, mul1, inlet=1)
    link(freq2, osc2)
    link(phase, osc2, inlet=1)
    link(osc2, mul2)
    link(amp2, mul2, inlet=1)
    link(mul2, add1, inlet=1)
    link(add1, dac)
    link(add1, dac, inlet=1)
    link(add1, scop)
    link(scp1, scop)
    link(scp2, scop, inlet=1)
    p.reposition()
    # p.graph()
    p.save()
