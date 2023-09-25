"""adaptagrams.org HOLA algorithm

This test is using the HOLA algorithm referenced in the paper
HOLA: Human-like Orthogonal Network Layout
by Steve Kieffer, Tim Dwyer, Kim Marriott, and Michael Wybrow
see: https://ialab.it.monash.edu/~dwyer/papers/hola2015.pdf

The algorithm is implemented in c++ and wrapped by SWIG to produce
a python extension of the API.

"""

import pytest
try:
    from adaptagrams import Graph, DialectNode, HolaOpts, doHOLA
    HAS_ADAPTAGRAMS = True
except ImportError:
    HAS_ADAPTAGRAMS = False

from py2max import Patcher


def dump(g, prefix):
    with open(f'{prefix}.tglf', 'w') as f:
        f.write(g.writeTglf())
    with open(f'{prefix}.svg', 'w') as f:
        f.write(g.writeSvg())


def set_hola_opts(opts):
    # opts.useACAforLinks = False
    return opts


class HolaPatcher(Patcher):

    def reposition(self):

        g = Graph()

        # add nodes
        nodes = {}
        for i, box in enumerate(self.boxes):
            x, y, h, w = box.patching_rect
            node = DialectNode.allocate(x, y, h, w)
            nodes[box.id] = node
            g.addNode(node)
            # assert i == node.id

        for line in self.lines:
            g.addEdge(nodes[line.src], nodes[line.dst])

        dump(g, './outputs/test_layout_hola_3_before')

        opts = HolaOpts()

        # change opts
        opts = set_hola_opts(opts)

        # orthogonal layout
        doHOLA(g, opts)

        dump(g, './outputs/test_layout_hola_3_after')

        # scale = self.rect[2]
        scale = 1
        repos = []
        for key, node in nodes.items():
            p = node.getCentre()
            repos.append((p.x*scale, p.y*scale))

        _boxes = []
        for box, xy in zip(self.boxes, repos):
            x, y, h, w = box.patching_rect
            newx, newy = xy
            box.patching_rect = newx, newy, h, w
            _boxes.append(box)
        self.boxes = _boxes


@pytest.mark.skipif(not HAS_ADAPTAGRAMS, reason="requires adaptagrams")
def test_graph():
    p = HolaPatcher(path='outputs/test_layout_hola_3.maxpat')

    fbox = p.add_floatbox
    ibox = p.add_intbox
    tbox = p.add_box
    link = p.add_line

    # objects
    freq1 = fbox()
    freq2 = fbox()
    phase = fbox()
    osc1 = tbox('cycle~')
    osc2 = tbox('cycle~')
    amp1 = fbox()
    amp2 = fbox()
    mul1 = tbox('*~')
    mul2 = tbox('*~')
    add1 = tbox('+~')
    dac = tbox('ezdac~')
    scop = tbox('scope~')
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

