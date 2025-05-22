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
    from adaptagrams import Graph, DialectNode
    from adaptagrams import buildGraphFromTglfFile, HolaOpts, doHOLA

    HAS_ADAPTAGRAMS = True
except ImportError:
    HAS_ADAPTAGRAMS = False


def dump(g, prefix):
    with open(f"{prefix}.tglf", "w") as f:
        f.write(g.writeTglf())
    with open(f"{prefix}.svg", "w") as f:
        f.write(g.writeSvg())


@pytest.mark.skipif(not HAS_ADAPTAGRAMS, reason="requires adaptagrams")
def test_build_graph():
    g = Graph()

    # dimenstions
    # n = DialectNode.allocate(10, 2)

    # r = Rectangle(9.0, 10.0, 9.0, 10.0)

    # coordinates and dimensions
    # Node (double cx, double cy, double w, double h)
    a = DialectNode.allocate(10.5, 2.2, 5.3, 5.3)
    b = DialectNode.allocate(5.1, 10.0, 5.0, 5.0)

    g.addNode(a)
    assert a.id() == 0

    g.addNode(b)
    assert b.id() == 1

    assert g.getNumNodes() == 2

    e = g.addEdge(a, b)

    assert g.getNumEdges() == 1

    dump(g, "./outputs/test_layout_hola_1_before")


@pytest.mark.skipif(not HAS_ADAPTAGRAMS, reason="requires adaptagrams")
def test_hola_from_random_graph():
    g = buildGraphFromTglfFile("tests/graphs/random/v30e33.tglf")
    assert g.getNumNodes() == 30
    assert g.getNumEdges() == 33

    # get one node (2) from original graph
    n = g.getNode(2)
    p = n.getCentre()  # get coordinates
    assert p.x == 44.0
    assert p.y == 258.0

    b = n.getBoundingBox()
    assert b.x == 29.0
    assert b.X == 59.0
    assert b.X - b.x == 30.0

    assert b.y == 243.0
    assert b.Y == 273.0
    assert b.Y - b.y == 30.0

    dump(g, "./outputs/test_layout_hola_random_1_before")

    # configure and execute Hola transform
    opts = HolaOpts()
    doHOLA(g, opts)

    n = g.getNode(2)
    p = n.getCentre()  # get coordinates

    assert int(p.x) == int(221.328125)
    assert int(p.y) == int(247.50000000000006)

    b = n.getBoundingBox()
    assert int(b.x) == int(206.328125)
    assert int(b.X) == int(236.328125)
    assert int(b.X - b.x) == int(30.0)

    assert int(b.y) == int(232.50000000000006)
    assert int(b.Y) == int(262.50000000000006)
    assert int(b.Y - b.y) == int(30.0)

    # assert p.x == 221.328125
    # assert p.y == 247.50000000000006

    # b = n.getBoundingBox()
    # assert b.x == 206.328125
    # assert b.X == 236.328125
    # assert b.X - b.x == 30.0

    # assert b.y == 232.50000000000006
    # assert b.Y == 262.50000000000006
    # assert b.Y - b.y == 30.0

    dump(g, "./outputs/test_layout_hola_random_1_after")
