"""adaptagrams.org HOLA algorithm

This test is using the HOLA algorithm referenced in the paper
HOLA: Human-like Orthogonal Network Layout 
by Steve Kieffer, Tim Dwyer, Kim Marriott, and Michael Wybrow
see: https://ialab.it.monash.edu/~dwyer/papers/hola2015.pdf

The algorithm is implemented in c++ and wrapped by SWIG to produce 
a python extension of the API.

"""

from adaptagrams import Graph, DialectNode, HolaOpts, doHOLA


from .. import Patcher


def dump(g, prefix):
    with open(f'{prefix}.tglf', 'w') as f:
        f.write(g.writeTglf())
    with open(f'{prefix}.svg', 'w') as f:
        f.write(g.writeSvg())

class HolaPatcher(Patcher):

    def reposition(self):

        g = Graph()

        # add nodes
        nodes = {}
        for i, box in enumerate(self._boxes):            
            x, y, h, w = box.patching_rect
            node = DialectNode.allocate(x, y, h, w)
            nodes[box.id] = node
            g.addNode(node)
            # assert i == node.id

        for line in self._lines:
            g.addEdge(nodes[line.src], nodes[line.dst])

        dump(g, './outputs/test_hola_graph2_before')
        
        opts = HolaOpts()
        
        # orthogonal layout
        doHOLA(g, opts)

        dump(g, './outputs/test_hola_graph2_after')


def test_graph():
    p = HolaPatcher('outputs/test_hola_graph2.maxpat')

    fbox = p.add_floatbox
    ibox = p.add_intbox
    tbox = p.add_textbox
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


if __name__ == '__main__':
    test_graph()

