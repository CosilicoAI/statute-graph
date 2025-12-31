"""Core graph data structure for statutory cross-references."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import networkx as nx


class StatuteGraph:
    """Directed graph of statutory cross-references.

    Nodes are statute sections (citation paths like 'us/statute/26/32').
    Edges represent cross-references (section A references section B).

    The graph direction follows dependency semantics:
    - Edge A -> B means "A depends on B" (A references B)
    - To encode A, you must first encode B
    """

    def __init__(self):
        """Create an empty statute graph."""
        self._graph = nx.DiGraph()
        self._encoded: set[str] = set()

    def __contains__(self, node: str) -> bool:
        """Check if a node exists in the graph."""
        return node in self._graph

    @property
    def num_nodes(self) -> int:
        """Number of nodes in the graph."""
        return self._graph.number_of_nodes()

    @property
    def num_edges(self) -> int:
        """Number of edges in the graph."""
        return self._graph.number_of_edges()

    @property
    def density(self) -> float:
        """Graph density (edges / possible edges)."""
        return nx.density(self._graph)

    def add_node(self, citation_path: str, **attrs: Any) -> None:
        """Add a statute section node.

        Args:
            citation_path: Unique identifier like 'us/statute/26/32'
            **attrs: Additional attributes (level, heading, etc.)
        """
        self._graph.add_node(citation_path, **attrs)

    def add_edge(
        self, from_node: str, to_node: str, ref_type: str = "unknown", **attrs: Any
    ) -> None:
        """Add a cross-reference edge.

        Args:
            from_node: Source node (the section making the reference)
            to_node: Target node (the section being referenced)
            ref_type: Type of reference (internal_section, external_title, etc.)
            **attrs: Additional attributes
        """
        self._graph.add_edge(from_node, to_node, ref_type=ref_type, **attrs)

    def get_dependencies(self, node: str) -> list[str]:
        """Get all nodes that this node depends on (references)."""
        return list(self._graph.successors(node))

    def get_dependents(self, node: str) -> list[str]:
        """Get all nodes that depend on (reference) this node."""
        return list(self._graph.predecessors(node))

    def in_degree(self, node: str) -> int:
        """Number of dependencies (outgoing edges in our semantics)."""
        return self._graph.out_degree(node)

    def out_degree(self, node: str) -> int:
        """Number of dependents (incoming edges in our semantics)."""
        return self._graph.in_degree(node)

    def topological_sort(self) -> list[str]:
        """Return nodes in dependency order (dependencies before dependents).

        Raises:
            ValueError: If the graph contains cycles.
        """
        try:
            # Reverse because we want dependencies first
            return list(reversed(list(nx.topological_sort(self._graph))))
        except nx.NetworkXUnfeasible:
            cycles = list(nx.simple_cycles(self._graph))
            raise ValueError(f"Graph contains cycle(s): {cycles[:3]}...")

    def get_ready_nodes(self) -> list[str]:
        """Get nodes that are ready to encode (all dependencies encoded)."""
        ready = []
        for node in self._graph.nodes():
            if node in self._encoded:
                continue
            deps = self.get_dependencies(node)
            if all(dep in self._encoded for dep in deps):
                ready.append(node)
        return sorted(ready)

    def get_blocked_by(self, node: str) -> list[str]:
        """Get unencoded dependencies blocking this node."""
        deps = self.get_dependencies(node)
        return [dep for dep in deps if dep not in self._encoded]

    def mark_encoded(self, node: str) -> None:
        """Mark a node as encoded."""
        self._encoded.add(node)

    def get_progress(self) -> dict[str, int]:
        """Get encoding progress statistics."""
        total = self.num_nodes
        encoded = len(self._encoded)
        ready = len(self.get_ready_nodes())
        blocked = total - encoded - ready
        return {
            "total": total,
            "encoded": encoded,
            "ready": ready,
            "blocked": blocked,
        }

    def get_hubs(self, top_k: int = 10) -> list[tuple[str, int]]:
        """Get nodes with the most dependents (highest out-degree).

        These are "hub" sections that many other sections reference.
        """
        degrees = [(node, self.out_degree(node)) for node in self._graph.nodes()]
        degrees.sort(key=lambda x: x[1], reverse=True)
        return degrees[:top_k]

    def depth(self, node: str) -> int:
        """Compute the longest path from this node to a root (no dependencies).

        Roots have depth 0. A node depending only on roots has depth 1, etc.
        """
        deps = self.get_dependencies(node)
        if not deps:
            return 0
        return 1 + max(self.depth(dep) for dep in deps)

    @property
    def max_depth(self) -> int:
        """Maximum depth in the graph."""
        if self.num_nodes == 0:
            return 0
        return max(self.depth(node) for node in self._graph.nodes())

    @property
    def avg_in_degree(self) -> float:
        """Average number of dependencies per node."""
        if self.num_nodes == 0:
            return 0.0
        total = sum(self.in_degree(node) for node in self._graph.nodes())
        return total / self.num_nodes

    @property
    def num_scc(self) -> int:
        """Number of strongly connected components."""
        return nx.number_strongly_connected_components(self._graph)

    def subgraph(self, nodes: list[str]) -> "StatuteGraph":
        """Create a subgraph containing only the specified nodes."""
        sg = StatuteGraph()
        sg._graph = self._graph.subgraph(nodes).copy()
        sg._encoded = self._encoded.intersection(nodes)
        return sg

    def get_ancestors(self, node: str, max_depth: int | None = None) -> set[str]:
        """Get all nodes that this node transitively depends on."""
        if max_depth == 0:
            return set()
        ancestors = set()
        for dep in self.get_dependencies(node):
            ancestors.add(dep)
            if max_depth is None or max_depth > 1:
                next_depth = None if max_depth is None else max_depth - 1
                ancestors.update(self.get_ancestors(dep, next_depth))
        return ancestors

    def get_descendants(self, node: str, max_depth: int | None = None) -> set[str]:
        """Get all nodes that transitively depend on this node."""
        if max_depth == 0:
            return set()
        descendants = set()
        for dep in self.get_dependents(node):
            descendants.add(dep)
            if max_depth is None or max_depth > 1:
                next_depth = None if max_depth is None else max_depth - 1
                descendants.update(self.get_descendants(dep, next_depth))
        return descendants
