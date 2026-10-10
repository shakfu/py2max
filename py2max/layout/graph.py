"""Shared connection-graph model for the layout managers.

Every layout manager needs the patcher's connection graph in some form -- flow
wants per-node input/output lists, grid wants an undirected adjacency plus
connected components, matrix wants directed adjacency lists and a per-column
topological order, and the base manager wants the neighbours of a set. Before
this module each manager rebuilt that graph from ``parent._lines`` with its own
near-identical loop (the construction was duplicated ~6x, and the DFS component
and DFS topological-sort passes were reimplemented separately).

``PatchGraph`` centralises the construction once and exposes each view the
managers need, preserving the exact ordering and duplicate semantics the old
inline loops had:

- directed views keep parallel edges (a doubled wire appears twice), matching
  the old ``list.append`` construction;
- undirected views collapse duplicates into sets, as before;
- node/key ordering follows first-appearance (or the caller-supplied node
  order), so downstream tie-breaks are unchanged.
"""

import heapq
from typing import Dict, Iterable, List, Optional, Set

from py2max.core.abstract import AbstractPatchline


class PatchGraph:
    """A directed graph built from a patcher's boxes and patchlines.

    Args:
        lines: the patchlines (each exposing ``.src`` / ``.dst`` ids).
        nodes: optional explicit node ids to include as keys (isolated nodes
            kept). When given, edges are restricted to those whose endpoints are
            both in this set -- matching the ``if src in objects and dst in
            objects`` guard the managers used. When ``None``, the node set is the
            edge endpoints in first-appearance order (the flow-manager
            behaviour, which does not pre-seed disconnected boxes).
    """

    def __init__(
        self,
        lines: Iterable[AbstractPatchline],
        nodes: Optional[Iterable[str]] = None,
    ) -> None:
        edges: List[tuple[str, str]] = [
            (pl.src, pl.dst)
            for pl in lines
            if pl.src is not None and pl.dst is not None
        ]

        if nodes is not None:
            ordered_nodes = list(nodes)
            node_set = set(ordered_nodes)
            edges = [(s, d) for (s, d) in edges if s in node_set and d in node_set]
            self.nodes: List[str] = ordered_nodes
        else:
            seen: Dict[str, None] = {}
            for s, d in edges:
                seen.setdefault(s, None)
                seen.setdefault(d, None)
            self.nodes = list(seen)

        self.edges = edges

    # -- directed views -----------------------------------------------------

    def out_lists(self) -> Dict[str, List[str]]:
        """``{node: [successor, ...]}`` preserving edge order and duplicates."""
        out: Dict[str, List[str]] = {n: [] for n in self.nodes}
        for s, d in self.edges:
            out[s].append(d)
        return out

    def in_lists(self) -> Dict[str, List[str]]:
        """``{node: [predecessor, ...]}`` preserving edge order and duplicates."""
        inc: Dict[str, List[str]] = {n: [] for n in self.nodes}
        for s, d in self.edges:
            inc[d].append(s)
        return inc

    def io_lists(self) -> Dict[str, Dict[str, List[str]]]:
        """``{node: {'inputs': [...], 'outputs': [...]}}`` (flow manager shape)."""
        io: Dict[str, Dict[str, List[str]]] = {
            n: {"inputs": [], "outputs": []} for n in self.nodes
        }
        for s, d in self.edges:
            io[s]["outputs"].append(d)
            io[d]["inputs"].append(s)
        return io

    # -- undirected views ---------------------------------------------------

    def undirected_sets(self) -> Dict[str, Set[str]]:
        """``{node: {neighbour, ...}}`` (both directions, duplicates collapsed)."""
        adj: Dict[str, Set[str]] = {n: set() for n in self.nodes}
        for s, d in self.edges:
            adj[s].add(d)
            adj[d].add(s)
        return adj

    def neighbors_of(self, obj_ids: Iterable[str]) -> Set[str]:
        """All nodes directly connected (either direction) to any of ``obj_ids``."""
        targets = set(obj_ids)
        connected: Set[str] = set()
        for s, d in self.edges:
            if s in targets:
                connected.add(d)
            if d in targets:
                connected.add(s)
        return connected

    # -- traversals ---------------------------------------------------------

    def connected_components(self) -> List[Set[str]]:
        """Undirected connected components, via depth-first search."""
        adj = self.undirected_sets()
        visited: Set[str] = set()
        components: List[Set[str]] = []

        def dfs(start: str, component: Set[str]) -> None:
            stack = [start]
            while stack:
                node = stack.pop()
                if node in visited:
                    continue
                visited.add(node)
                component.add(node)
                for neighbour in adj.get(node, ()):
                    if neighbour not in visited:
                        stack.append(neighbour)

        for node in self.nodes:
            if node not in visited:
                component: Set[str] = set()
                dfs(node, component)
                if component:
                    components.append(component)
        return components

    def signal_order(self) -> List[str]:
        """Nodes in signal order (sources first), ties broken by node order.

        If node order is already a signal order it is returned unchanged. A
        feedback loop is placed as a unit, its nodes in node order.
        """
        index = {n: i for i, n in enumerate(self.nodes)}
        out = {
            n: [d for d in succ if d in index] for n, succ in self.out_lists().items()
        }
        rev: Dict[str, List[str]] = {n: [] for n in self.nodes}
        for s, d in self.edges:
            rev[d].append(s)

        # Kosaraju: finish order on the graph, then components on its reverse
        finished: List[str] = []
        seen: Set[str] = set()
        for root in self.nodes:
            if root in seen:
                continue
            seen.add(root)
            stack = [(root, iter(out.get(root, [])))]
            while stack:
                node, it = stack[-1]
                nxt = next((d for d in it if d not in seen), None)
                if nxt is None:
                    stack.pop()
                    finished.append(node)
                else:
                    seen.add(nxt)
                    stack.append((nxt, iter(out.get(nxt, []))))
        comp: Dict[str, int] = {}
        members: List[List[str]] = []
        for root in reversed(finished):
            if root in comp:
                continue
            comp[root] = len(members)
            group, todo = [root], [root]
            while todo:
                for s in rev[todo.pop()]:
                    if s not in comp:
                        comp[s] = comp[root]
                        group.append(s)
                        todo.append(s)
            members.append(sorted(group, key=index.__getitem__))

        # Kahn on the components, lowest node index first
        indegree = [0] * len(members)
        succs: List[Set[int]] = [set() for _ in members]
        for s, d in self.edges:
            a, b = comp[s], comp[d]
            if a != b and b not in succs[a]:
                succs[a].add(b)
                indegree[b] += 1
        ready = [(index[m[0]], c) for c, m in enumerate(members) if not indegree[c]]
        heapq.heapify(ready)
        result: List[str] = []
        while ready:
            _, c = heapq.heappop(ready)
            result.extend(members[c])
            for b in succs[c]:
                indegree[b] -= 1
                if not indegree[b]:
                    heapq.heappush(ready, (index[members[b][0]], b))
        return result

    def topological_order(self) -> List[str]:
        """Post-order DFS from source nodes, giving a signal-flow ordering.

        Sources (no incoming edge within the graph) are visited first; each
        node's successors (sorted for determinism) are emitted before the node
        itself; any nodes unreached by that pass are appended in node order.
        Mirrors the per-column ordering the matrix manager relied on.
        """
        out = {n: set(succ) for n, succ in self.out_lists().items()}
        indegree_targets: Set[str] = set()
        for succ in out.values():
            indegree_targets |= succ

        visited: Set[str] = set()
        result: List[str] = []

        def dfs(node: str) -> None:
            if node in visited:
                return
            visited.add(node)
            for succ in sorted(out.get(node, set())):
                dfs(succ)
            result.append(node)

        sources = [n for n in self.nodes if n not in indegree_targets]
        if not sources:
            sources = list(self.nodes)
        for source in sources:
            dfs(source)

        for node in self.nodes:
            if node not in result:
                result.append(node)
        return result
