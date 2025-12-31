---
kernelspec:
  name: python3
  display_name: Python 3
---

# Results

We analyze Title 26 of the United States Code (Internal Revenue Code), the primary source of federal tax law.

```{code-cell} python
:tags: [remove-output]

from statute_graph import from_xml
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# Load data
try:
    xml_path = Path("../data/usc26.xml")
    if not xml_path.exists():
        xml_path = Path("/Users/maxghenis/CosilicoAI/arch/data/uscode/usc26.xml")
    g = from_xml(xml_path)
except FileNotFoundError:
    g = None
    print("Data not available")
```

## Graph Statistics

```{code-cell} python
if g:
    stats = {
        "Sections (nodes)": f"{g.num_nodes:,}",
        "Cross-references (edges)": f"{g.num_edges:,}",
        "Graph density": f"{g.density:.6f}",
        "Average dependencies per section": f"{g.avg_in_degree:.2f}",
        "Strongly connected components": f"{g.num_scc:,}",
    }
    pd.DataFrame.from_dict(stats, orient='index', columns=['Value'])
```

## Hub Sections

The most-referenced sections serve as "hubs" in the dependency graph. Encoding these first unblocks the most dependent sections.

```{code-cell} python
if g:
    hubs = g.get_hubs(top_k=15)
    hub_df = pd.DataFrame([
        {"Section": path.split('/')[-1], "Dependents": count}
        for path, count in hubs
    ])

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(hub_df['Section'], hub_df['Dependents'], color='steelblue')
    ax.set_xlabel('Number of Dependent Sections')
    ax.set_ylabel('Section Number')
    ax.set_title('Most-Referenced Sections in Title 26')
    ax.invert_yaxis()
    plt.tight_layout()
    plt.show()

    hub_df
```

## Optimal Encoding Sequence

The complete encoding sequence, respecting dependencies and handling cycles.

```{code-cell} python
if g:
    sequence = g.get_encoding_sequence()
    seq_df = pd.DataFrame(sequence)
    seq_df['section'] = seq_df['citation_path'].apply(lambda x: x.split('/')[-1])

    print(f"Total sections in sequence: {len(seq_df):,}")
    print(f"Sections in cycles: {(seq_df['scc_size'] > 1).sum():,}")
    print(f"Sections without cycles: {(seq_df['scc_size'] == 1).sum():,}")

    # Show first 20
    seq_df[['order', 'section', 'dependents', 'dependencies', 'scc_size']].head(20)
```

## Dependency Distribution

```{code-cell} python
if g:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Dependencies (in-degree)
    deps = seq_df['dependencies']
    axes[0].hist(deps, bins=50, color='steelblue', edgecolor='white')
    axes[0].set_xlabel('Number of Dependencies')
    axes[0].set_ylabel('Number of Sections')
    axes[0].set_title('Distribution of Dependencies')
    axes[0].axvline(deps.mean(), color='red', linestyle='--', label=f'Mean: {deps.mean():.1f}')
    axes[0].legend()

    # Dependents (out-degree)
    dependents = seq_df['dependents']
    axes[1].hist(dependents, bins=50, color='coral', edgecolor='white')
    axes[1].set_xlabel('Number of Dependents')
    axes[1].set_ylabel('Number of Sections')
    axes[1].set_title('Distribution of Dependents')
    axes[1].axvline(dependents.mean(), color='red', linestyle='--', label=f'Mean: {dependents.mean():.1f}')
    axes[1].legend()

    plt.tight_layout()
    plt.show()
```

## Export Sequence

```{code-cell} python
if g:
    # Export to CSV
    output_path = Path("../output/encoding_sequence.csv")
    output_path.parent.mkdir(exist_ok=True)
    seq_df.to_csv(output_path, index=False)
    print(f"Saved encoding sequence to {output_path}")
```
