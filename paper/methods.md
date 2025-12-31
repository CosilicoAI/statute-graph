---
kernelspec:
  name: python3
  display_name: Python 3
---

# Methods

## Data Source

We use the official US Code XML from the Office of the Law Revision Counsel (OLRC) {cite:p}`uscode2025`, available at [uscode.house.gov](https://uscode.house.gov/download/download.shtml). The XML uses the United States Legislative Markup (USLM) schema and includes structured cross-reference tags:

```xml
<ref href="/us/usc/t26/s151">section 151 of this title</ref>
```

These tags provide precise citation paths, avoiding the ambiguity of regex-based extraction from plain text.

## Graph Construction

We model the statute as a directed graph $G = (V, E)$ where:

- **Nodes** $V$: Statute sections (e.g., `us/usc/26/32`)
- **Edges** $E$: Cross-references, where edge $(u, v)$ means section $u$ references section $v$

Edge direction follows **dependency semantics**: if $A \to B$, then $A$ depends on $B$ and $B$ should be encoded before $A$.

```{code-cell} python
:tags: [remove-output]

from statute_graph import from_xml
from pathlib import Path

# Load Title 26 (Internal Revenue Code)
# Note: Requires USC XML file from uscode.house.gov
try:
    xml_path = Path("../data/usc26.xml")
    if not xml_path.exists():
        xml_path = Path("/Users/maxghenis/CosilicoAI/arch/data/uscode/usc26.xml")
    g = from_xml(xml_path)
    print(f"Loaded {g.num_nodes:,} sections with {g.num_edges:,} cross-references")
except FileNotFoundError:
    print("USC XML not found. Download from uscode.house.gov")
    g = None
```

## Strongly Connected Components

A **strongly connected component** (SCC) is a maximal set of nodes where every node is reachable from every other node. In statutory terms, an SCC represents a group of sections that mutually reference each other, either directly or through intermediaries.

For such groups, there is no valid linear ordering where all dependencies come first. We handle this by:

1. **Condensing** each SCC into a single "super-node"
2. **Topologically sorting** the resulting DAG
3. **Expanding** each super-node, ordering internal nodes by importance (out-degree)

This approach follows Tarjan's algorithm {cite:p}`tarjan1972` for SCC detection.

```{code-cell} python
if g:
    sccs = g.get_sccs()

    # Analyze SCC sizes
    scc_sizes = [len(scc) for scc in sccs]
    single_node_sccs = sum(1 for s in scc_sizes if s == 1)
    multi_node_sccs = sum(1 for s in scc_sizes if s > 1)
    largest_scc = max(scc_sizes)

    print(f"Total SCCs: {len(sccs):,}")
    print(f"Single-node SCCs (no cycles): {single_node_sccs:,}")
    print(f"Multi-node SCCs (cycles): {multi_node_sccs:,}")
    print(f"Largest SCC size: {largest_scc:,}")
```

## Optimal Encoding Sequence

The algorithm proceeds as follows:

1. Compute all SCCs using Tarjan's algorithm: $O(V + E)$
2. Build condensation graph where each SCC is a node
3. Topologically sort the condensation (guaranteed to be a DAG)
4. For each SCC in order:
   - If single node: add directly to sequence
   - If multi-node: sort by out-degree (most-referenced first) and add

This produces a sequence where:
- All acyclic dependencies are satisfied (dependency comes before dependent)
- Within cycles, hub nodes (most referenced) come first

```{code-cell} python
if g:
    # Get optimal encoding sequence
    sequence = g.get_encoding_sequence()

    print(f"Generated sequence of {len(sequence):,} sections")
    print("\nFirst 10 sections to encode:")
    for item in sequence[:10]:
        section = item['citation_path'].split('/')[-1]
        cycle_note = f" (in cycle of {item['scc_size']})" if item['scc_size'] > 1 else ""
        print(f"  {item['order']:4d}. Section {section:6s} - {item['dependents']} dependents{cycle_note}")
```
