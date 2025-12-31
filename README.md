# statute-graph

Graph analysis of statutory cross-references for optimal encoding order.

## Motivation

Tax statutes form a complex web of cross-references. Section 32 (EITC) references section 151 (dependency exemption), which references section 152 (definition of dependent), and so on. This creates a dependency graph that determines the optimal order for encoding statutes into executable rules.

## Key Findings

From US Internal Revenue Code (Title 26):
- **6,680** statutory subsections
- **~109,000** cross-references extracted from XML
- **565** sections ready to encode (no dependencies)
- **6,115** sections blocked (waiting on dependencies)

## Research Questions

1. What is the topological structure of the tax code?
2. Which sections are "hubs" that block many others?
3. What is the minimum encoding sequence?
4. How does complexity correlate with dependency depth?

## Installation

```bash
pip install statute-graph
```

## Quick Start

```python
from statute_graph import USCodeGraph

# Load Title 26 (Internal Revenue Code)
g = USCodeGraph.from_xml("usc26.xml")

# Find optimal encoding order
sequence = g.topological_sort()

# Get sections ready to encode (no unmet dependencies)
ready = g.get_ready_nodes()

# Find hub sections (most dependencies)
hubs = g.get_hubs(top_k=10)

# Visualize section 32 and its dependencies
g.plot_subgraph("us/statute/26/32", depth=2)
```

## Graph Metrics

```python
# Basic stats
print(f"Nodes: {g.num_nodes}")
print(f"Edges: {g.num_edges}")
print(f"Density: {g.density:.4f}")

# Complexity metrics
print(f"Max depth: {g.max_depth}")
print(f"Avg in-degree: {g.avg_in_degree:.2f}")
print(f"Strongly connected components: {g.num_scc}")
```

## Data Sources

- **US Code XML**: [uscode.house.gov](https://uscode.house.gov/download/download.shtml)
- Cross-references extracted from `<ref href="/us/usc/t26/s151">` tags

## Related Work

- [Network Analysis and Law](https://computationallegalstudies.com/network-analysis-and-law-tutorial/) - Case law citation networks
- [CaseGNN](https://arxiv.org/abs/2403.11823) - Graph neural networks for legal case retrieval
- [Legal Knowledge Graphs](https://arxiv.org/html/2502.20364v2) - RAG with legal knowledge graphs

## Citation

```bibtex
@software{statute_graph,
  title = {statute-graph: Graph Analysis of Statutory Cross-References},
  author = {Cosilico},
  year = {2025},
  url = {https://github.com/CosilicoAI/statute-graph}
}
```

## License

MIT
