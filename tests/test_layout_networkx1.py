import pytest

try:
    import networkx as nx
    import matplotlib.pyplot as plt

    HAS_REQS = True
except ImportError:
    HAS_REQS = False


from py2max import Patcher


@pytest.mark.skipif(not HAS_REQS, reason="requires networkx, matplotlib")
def test_graph():
    class GraphPatcher(Patcher):
        def reposition(self):
            G = nx.DiGraph()

            # add nodes
            for box in self._boxes:
                if box.maxclass == "comment":
                    continue
                G.add_node(box.id)

            # edd edges
            for line in self._lines:
                G.add_edge(line.src, line.dst)

            # layout
            scale = self.rect[2]
            # pos = nx.circular_layout(G, scale=scale)
            # pos = nx.kamada_kawai_layout(G, scale=scale)
            # pos = nx.planar_layout(G, scale=scale)
            # pos = nx.shell_layout(G, scale=scale)
            # pos = nx.spectral_layout(G, scale=scale)
            # pos = nx.spiral_layout(G. scale=scale)
            pos = nx.spring_layout(G, scale=scale)

            repos = []
            for p in pos.items():
                _, coord = p
                x, y = coord
                repos.append((x + scale, y + scale))

            _boxes = []
            for box, xy in zip(self._boxes, repos):
                x, y, h, w = box.patching_rect
                newx, newy = xy
                box.patching_rect = newx, newy, h, w
                _boxes.append(box)
            self.boxes = _boxes

        def graph(self):
            G = nx.DiGraph()

            # make labels
            # labels = {b.id: b.label for b in self._boxes}

            # add nodes
            for box in self._boxes:
                if box.maxclass == "comment":
                    continue
                G.add_node(box.id)

            # edd edges
            for line in self._lines:
                G.add_edge(line.src, line.dst)

            # layout
            pos = nx.spring_layout(G)
            # pos = nx.circular_layout(G)
            # pos = nx.kamada_kawai_layout(G)
            # pos = nx.planar_layout(G)
            # pos = nx.shell_layout(G)
            # pos = nx.spectral_layout(G)
            # pos = nx.spiral_layout(G)
            # pos = nx.kamada_kawai_layout(G)

            # G = nx.convert_node_labels_to_integers(G)
            # G = nx.relabel_nodes(G, labels)
            # nx.draw(G, with_labels=True)
            nx.draw(G, pos=pos, with_labels=True)
            # nx.draw(G, pos=pos, with_labels=False)
            plt.show()

    p = GraphPatcher("outputs/test_layout_networkx1.maxpat")

    fparam = p.add_floatparam
    iparam = p.add_intparam
    tbox = p.add_textbox
    link = p.add_line

    # objects
    freq1 = fparam("frequency1", 230, 0, 1000)
    freq2 = fparam("frequency2", 341, 0, 1000)
    phase = fparam("phase_offset", 0.39)
    osc1 = tbox("cycle~")
    osc2 = tbox("cycle~")
    amp1 = fparam("amp1", 0.51)
    amp2 = fparam("amp2", 0.46)
    mul1 = tbox("*~")
    mul2 = tbox("*~")
    add1 = tbox("+~")
    dac = tbox("ezdac~")
    scop = tbox("scope~")
    scp1 = iparam("buffer_pixel", 40)
    scp2 = iparam("samples_buffer", 8)

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
