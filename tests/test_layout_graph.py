"""Unit tests for the shared PatchGraph model (L5).

Four layout managers now build their connection graph through PatchGraph, so its
contract -- edge ordering, duplicate handling, node-key seeding, and the DFS
traversals -- is pinned here directly.
"""

from py2max.core.patchline import Patchline
from py2max.layout.graph import PatchGraph


def _line(src, dst):
    return Patchline(source=[src, 0], destination=[dst, 0])


def test_none_endpoints_are_dropped():
    g = PatchGraph([_line("a", "b"), _line(None, "b"), _line("a", None)])
    assert g.edges == [("a", "b")]
    assert set(g.nodes) == {"a", "b"}


def test_node_keys_first_appearance_order_when_unseeded():
    # flow-manager behaviour: keys are edge endpoints in first-seen order.
    g = PatchGraph([_line("x", "y"), _line("y", "z")])
    assert g.nodes == ["x", "y", "z"]


def test_seeded_nodes_include_isolated_and_restrict_edges():
    # grid/matrix behaviour: all objects seeded; edges to unknown nodes dropped.
    g = PatchGraph([_line("a", "b"), _line("a", "ghost")], nodes=["a", "b", "c"])
    assert g.nodes == ["a", "b", "c"]  # 'c' isolated but present
    assert g.edges == [("a", "b")]  # edge to un-seeded 'ghost' dropped


def test_directed_views_preserve_order_and_duplicates():
    # a doubled wire a->b must appear twice (parallel patchlines).
    g = PatchGraph([_line("a", "b"), _line("a", "b"), _line("a", "c")])
    io = g.io_lists()
    assert io["a"]["outputs"] == ["b", "b", "c"]
    assert io["b"]["inputs"] == ["a", "a"]
    assert g.out_lists()["a"] == ["b", "b", "c"]
    assert g.in_lists()["b"] == ["a", "a"]


def test_undirected_and_neighbors():
    g = PatchGraph([_line("a", "b"), _line("b", "c")])
    assert g.undirected_sets()["b"] == {"a", "c"}
    assert g.neighbors_of({"b"}) == {"a", "c"}
    assert g.neighbors_of({"a"}) == {"b"}


def test_connected_components():
    g = PatchGraph(
        [_line("a", "b"), _line("d", "e")],
        nodes=["a", "b", "c", "d", "e"],
    )
    comps = g.connected_components()
    assert {"a", "b"} in comps
    assert {"d", "e"} in comps
    assert {"c"} in comps
    assert len(comps) == 3


def test_topological_order_is_post_order_from_sources():
    # Post-order DFS from the source without reversal: a node's successors are
    # emitted before the node, so the sink comes first (this is the exact
    # ordering the matrix column-sort has always produced).
    g = PatchGraph([_line("a", "b"), _line("b", "c")], nodes=["c", "b", "a"])
    assert g.topological_order() == ["c", "b", "a"]


def test_topological_order_disconnected_appended():
    g = PatchGraph([_line("a", "b")], nodes=["a", "b", "z"])
    order = g.topological_order()
    # successor 'b' is emitted before its predecessor 'a'
    assert order.index("b") < order.index("a")
    assert "z" in order
