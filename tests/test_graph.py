"""Tests for statute graph analysis."""

import pytest
from statute_graph import StatuteGraph


class TestStatuteGraph:
    """Test StatuteGraph construction and basic operations."""

    def test_create_empty_graph(self):
        """Can create an empty graph."""
        g = StatuteGraph()
        assert g.num_nodes == 0
        assert g.num_edges == 0

    def test_add_node(self):
        """Can add nodes with citation paths."""
        g = StatuteGraph()
        g.add_node("us/statute/26/32", level=0, heading="Earned income")
        assert g.num_nodes == 1
        assert "us/statute/26/32" in g

    def test_add_edge(self):
        """Can add edges (cross-references) between nodes."""
        g = StatuteGraph()
        g.add_node("us/statute/26/32")
        g.add_node("us/statute/26/151")
        g.add_edge("us/statute/26/32", "us/statute/26/151", ref_type="internal_section")
        assert g.num_edges == 1

    def test_get_dependencies(self):
        """Can get all dependencies for a node."""
        g = StatuteGraph()
        g.add_node("us/statute/26/32")
        g.add_node("us/statute/26/151")
        g.add_node("us/statute/26/152")
        g.add_edge("us/statute/26/32", "us/statute/26/151")
        g.add_edge("us/statute/26/32", "us/statute/26/152")

        deps = g.get_dependencies("us/statute/26/32")
        assert len(deps) == 2
        assert "us/statute/26/151" in deps
        assert "us/statute/26/152" in deps

    def test_get_dependents(self):
        """Can get all nodes that depend on a given node."""
        g = StatuteGraph()
        g.add_node("us/statute/26/32")
        g.add_node("us/statute/26/151")
        g.add_edge("us/statute/26/32", "us/statute/26/151")

        dependents = g.get_dependents("us/statute/26/151")
        assert len(dependents) == 1
        assert "us/statute/26/32" in dependents


class TestTopologicalSort:
    """Test topological sorting for optimal encoding order."""

    def test_simple_chain(self):
        """A -> B -> C should sort to [C, B, A]."""
        g = StatuteGraph()
        g.add_node("A")
        g.add_node("B")
        g.add_node("C")
        g.add_edge("A", "B")  # A depends on B
        g.add_edge("B", "C")  # B depends on C

        order = g.topological_sort()
        assert order.index("C") < order.index("B") < order.index("A")

    def test_diamond_dependency(self):
        """Diamond: A -> B, A -> C, B -> D, C -> D."""
        g = StatuteGraph()
        for node in ["A", "B", "C", "D"]:
            g.add_node(node)
        g.add_edge("A", "B")
        g.add_edge("A", "C")
        g.add_edge("B", "D")
        g.add_edge("C", "D")

        order = g.topological_sort()
        # D must come before B and C, which must come before A
        assert order.index("D") < order.index("B")
        assert order.index("D") < order.index("C")
        assert order.index("B") < order.index("A")
        assert order.index("C") < order.index("A")

    def test_no_dependencies(self):
        """Nodes with no dependencies are all ready."""
        g = StatuteGraph()
        g.add_node("A")
        g.add_node("B")
        g.add_node("C")

        ready = g.get_ready_nodes()
        assert len(ready) == 3

    def test_cycle_detection(self):
        """Cycles should be detected and reported."""
        g = StatuteGraph()
        g.add_node("A")
        g.add_node("B")
        g.add_edge("A", "B")
        g.add_edge("B", "A")  # Creates cycle

        with pytest.raises(ValueError, match="cycle"):
            g.topological_sort()


class TestEncodingOrder:
    """Test encoding order with status tracking."""

    def test_mark_encoded(self):
        """Marking a node as encoded updates ready list."""
        g = StatuteGraph()
        g.add_node("A")
        g.add_node("B")
        g.add_edge("A", "B")  # A depends on B

        # Initially only B is ready (no dependencies)
        ready = g.get_ready_nodes()
        assert ready == ["B"]

        # Mark B as encoded
        g.mark_encoded("B")

        # Now A is ready
        ready = g.get_ready_nodes()
        assert ready == ["A"]

    def test_get_blocked_by(self):
        """Can see what's blocking a node."""
        g = StatuteGraph()
        g.add_node("A")
        g.add_node("B")
        g.add_node("C")
        g.add_edge("A", "B")
        g.add_edge("A", "C")

        blocked_by = g.get_blocked_by("A")
        assert len(blocked_by) == 2
        assert "B" in blocked_by
        assert "C" in blocked_by

    def test_encoding_progress(self):
        """Can track encoding progress."""
        g = StatuteGraph()
        g.add_node("A")
        g.add_node("B")
        g.add_node("C")
        g.add_edge("A", "B")

        progress = g.get_progress()
        assert progress["total"] == 3
        assert progress["encoded"] == 0
        assert progress["ready"] == 2  # B and C have no deps
        assert progress["blocked"] == 1  # A blocked by B

        g.mark_encoded("B")
        progress = g.get_progress()
        assert progress["encoded"] == 1
        assert progress["ready"] == 2  # Now A and C are ready


class TestSubgraph:
    """Tests for subgraph extraction."""

    def test_subgraph_filters_nodes(self):
        """Subgraph only includes nodes matching prefix."""
        g = StatuteGraph()
        g.add_node("us/statute/26/1")
        g.add_node("us/statute/26/2")
        g.add_node("us/statute/26/A/32")
        g.add_node("us/statute/26/A/24")
        g.add_node("us/statute/26/B/100")

        sub = g.subgraph("26/A")
        assert sub.num_nodes == 2
        assert "us/statute/26/A/32" in sub
        assert "us/statute/26/A/24" in sub
        assert "us/statute/26/1" not in sub

    def test_subgraph_includes_internal_edges(self):
        """Subgraph keeps edges between included nodes."""
        g = StatuteGraph()
        g.add_node("us/statute/26/A/32")
        g.add_node("us/statute/26/A/24")
        g.add_node("us/statute/26/1")
        g.add_edge("us/statute/26/A/32", "us/statute/26/A/24")  # internal
        g.add_edge("us/statute/26/A/32", "us/statute/26/1")  # external

        sub = g.subgraph("26/A")
        assert sub.num_edges == 1  # only internal edge
        assert "us/statute/26/A/24" in sub.get_dependencies("us/statute/26/A/32")

    def test_subgraph_sequence_differs_from_filtered(self):
        """Subgraph encoding sequence may differ from filtering full sequence."""
        g = StatuteGraph()
        # Create structure where order depends on external deps
        g.add_node("us/statute/26/A/1")
        g.add_node("us/statute/26/A/2")
        g.add_node("us/statute/26/B/100")  # external
        g.add_edge("us/statute/26/A/1", "us/statute/26/B/100")  # A/1 deps on external
        g.add_edge("us/statute/26/A/2", "us/statute/26/A/1")  # A/2 deps on A/1

        # Full sequence: B/100 -> A/1 -> A/2
        full_seq = g.get_encoding_sequence()
        full_order = [s["citation_path"] for s in full_seq]
        assert full_order.index("us/statute/26/A/1") < full_order.index("us/statute/26/A/2")

        # Subgraph: without B/100, A/1 has 0 deps so may come in different position
        sub = g.subgraph("26/A")
        sub_seq = sub.get_encoding_sequence()
        assert len(sub_seq) == 2
        # A/1 now has 0 deps in subgraph (external dep removed)
        a1_item = next(s for s in sub_seq if s["citation_path"] == "us/statute/26/A/1")
        assert a1_item["dependencies"] == 0


class TestGraphMetrics:
    """Test graph complexity metrics."""

    def test_in_degree(self):
        """In-degree = number of dependencies."""
        g = StatuteGraph()
        g.add_node("A")
        g.add_node("B")
        g.add_node("C")
        g.add_edge("A", "B")
        g.add_edge("A", "C")

        assert g.in_degree("A") == 2
        assert g.in_degree("B") == 0
        assert g.in_degree("C") == 0

    def test_out_degree(self):
        """Out-degree = number of dependents."""
        g = StatuteGraph()
        g.add_node("A")
        g.add_node("B")
        g.add_edge("A", "B")

        assert g.out_degree("B") == 1  # A depends on B
        assert g.out_degree("A") == 0

    def test_get_hubs(self):
        """Hubs are nodes with highest out-degree (most dependents)."""
        g = StatuteGraph()
        for node in ["A", "B", "C", "D", "E"]:
            g.add_node(node)
        # Many nodes depend on D
        g.add_edge("A", "D")
        g.add_edge("B", "D")
        g.add_edge("C", "D")
        g.add_edge("E", "D")

        hubs = g.get_hubs(top_k=1)
        assert hubs[0][0] == "D"
        assert hubs[0][1] == 4  # 4 nodes depend on D

    def test_depth_to_root(self):
        """Depth = longest path to a node with no dependencies."""
        g = StatuteGraph()
        g.add_node("A")
        g.add_node("B")
        g.add_node("C")
        g.add_node("D")
        g.add_edge("A", "B")  # A -> B
        g.add_edge("B", "C")  # B -> C
        g.add_edge("C", "D")  # C -> D

        assert g.depth("D") == 0  # Root
        assert g.depth("C") == 1
        assert g.depth("B") == 2
        assert g.depth("A") == 3
