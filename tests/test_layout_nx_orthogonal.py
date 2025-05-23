import pytest

try:
    import networkx as nx
    import matplotlib.pyplot as plt

    from orthogonal.topologyShapeMetric.Orthogonalization import Orthogonalization
    from orthogonal.topologyShapeMetric.Planarization import Planarization
    from orthogonal.topologyShapeMetric.Compaction import Compaction

    def generate(G, pos=None):
        planar = Planarization(G, pos)
        orthogonal = Orthogonalization(planar)
        compact = Compaction(orthogonal)
        return compact

    HAS_REQS = True

except ImportError:
    HAS_REQS = False

    def generate(G, pos=None):
        """no-op"""


from py2max import Patcher


@pytest.mark.skipif(not HAS_REQS, reason="requires networksx,matplotlib,orthogonal")
def test_graph():
    class OrthogonalPatcher(Patcher):
        def reposition(self):
            G = nx.Graph()

            # add nodes
            nodes = {}
            for i, box in enumerate(self._boxes):
                # if box.maxclass == 'comment':
                #     continue
                nodes[box.id] = i
                G.add_node(i)

            # edd edges
            for line in self._lines:
                G.add_edge(nodes[line.src], nodes[line.dst])

            # layout
            if HAS_REQS:
                scale = self.rect[2] / 4  # specifically has_orthogonal
                # scale = self.rect[2]/8
            else:
                scale = self.rect[2] / 35

            # pos = nx.circular_layout(G, scale=scale)
            # pos = nx.kamada_kawai_layout(G, scale=scale)
            # pos = nx.planar_layout(G, scale=scale)
            # pos = nx.shell_layout(G, scale=scale)
            # pos = nx.spectral_layout(G, scale=scale)
            pos = nx.spring_layout(G, scale=scale)

            if HAS_REQS:
                compact = generate(G, pos)
                compact.draw()
                plt.savefig("outputs/test_layout_nx_orthogonal.png")
                pos = compact.pos

            repos = []
            for p in pos.items():
                _, coord = p
                x, y = coord
                repos.append((x * scale, y * scale))

            _boxes = []
            for box, xy in zip(self._boxes, repos):
                x, y, h, w = box.patching_rect
                newx, newy = xy
                box.patching_rect = newx, newy, h, w
                _boxes.append(box)
            self.boxes = _boxes

    p = OrthogonalPatcher("outputs/test_layout_nx_orthogonal.maxpat")

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
    p.save()
