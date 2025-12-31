#!/usr/bin/env python3
"""Generate figures for the statute-graph paper."""

from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Try to load real data, fall back to example data
try:
    from statute_graph import from_xml
    xml_path = Path("/Users/maxghenis/CosilicoAI/arch/data/uscode/usc26.xml")
    if xml_path.exists():
        g = from_xml(xml_path)
        USE_REAL_DATA = True
    else:
        USE_REAL_DATA = False
except Exception:
    USE_REAL_DATA = False

OUTPUT_DIR = Path(__file__).parent.parent / "paper" / "_static" / "figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Style settings
plt.style.use('seaborn-v0_8-whitegrid')
COLORS = {
    'primary': '#2563eb',  # Blue
    'secondary': '#059669',  # Green
    'accent': '#dc2626',  # Red
    'gray': '#6b7280',
}


def fig1_hub_sections():
    """Figure 1: Most-referenced sections (hub analysis)."""
    if USE_REAL_DATA:
        hubs = g.get_hubs(top_k=12)
        sections = [p.split('/')[-1] for p, _ in hubs]
        counts = [c for _, c in hubs]
    else:
        # Example data based on actual analysis
        sections = ['1', '401', '2', '48', '152', '414', '501', '7701', '42', '351', '162', '453']
        counts = [563, 238, 170, 168, 156, 142, 138, 125, 118, 112, 108, 102]

    fig, ax = plt.subplots(figsize=(8, 5))
    y_pos = np.arange(len(sections))

    bars = ax.barh(y_pos, counts, color=COLORS['primary'], edgecolor='white', linewidth=0.5)

    # Highlight Section 1
    bars[0].set_color(COLORS['accent'])

    ax.set_yticks(y_pos)
    ax.set_yticklabels([f'§{s}' for s in sections])
    ax.invert_yaxis()
    ax.set_xlabel('Number of Dependent Sections', fontsize=11)
    ax.set_title('Most-Referenced Sections in Title 26 (IRC)', fontsize=12, fontweight='bold')

    # Add value labels
    for i, (bar, count) in enumerate(zip(bars, counts)):
        ax.text(count + 8, bar.get_y() + bar.get_height()/2, str(count),
                va='center', fontsize=9, color=COLORS['gray'])

    ax.set_xlim(0, max(counts) * 1.15)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'hub_sections.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved {OUTPUT_DIR / 'hub_sections.png'}")


def fig2_scc_distribution():
    """Figure 2: Distribution of strongly connected component sizes."""
    if USE_REAL_DATA:
        sccs = g.get_sccs()
        scc_sizes = [len(scc) for scc in sccs]
    else:
        # Example data: most are size 1, few larger
        scc_sizes = [1] * 1400 + [2] * 30 + [3] * 8 + [4] * 4 + [5] * 2

    # Count by size
    from collections import Counter
    size_counts = Counter(scc_sizes)
    sizes = sorted(size_counts.keys())
    counts = [size_counts[s] for s in sizes]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

    # Left: All SCCs (log scale)
    ax1.bar(sizes[:10], counts[:10], color=COLORS['primary'], edgecolor='white')
    ax1.set_xlabel('SCC Size (number of sections)', fontsize=10)
    ax1.set_ylabel('Count', fontsize=10)
    ax1.set_title('Distribution of SCC Sizes', fontsize=11, fontweight='bold')
    ax1.set_yscale('log')
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)

    # Right: Pie chart of cyclic vs acyclic
    cyclic = sum(1 for s in scc_sizes if s > 1)
    acyclic = sum(1 for s in scc_sizes if s == 1)

    wedges, texts, autotexts = ax2.pie(
        [acyclic, cyclic],
        labels=['No cycles\n(can order)', 'In cycles\n(mutual refs)'],
        autopct='%1.1f%%',
        colors=[COLORS['secondary'], COLORS['accent']],
        explode=(0, 0.05),
        startangle=90
    )
    ax2.set_title('Sections by Cycle Status', fontsize=11, fontweight='bold')

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'scc_distribution.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved {OUTPUT_DIR / 'scc_distribution.png'}")


def fig3_dependency_flow():
    """Figure 3: Conceptual diagram of encoding order."""
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)
    ax.axis('off')

    # Levels
    levels = [
        ('Level 0: Foundations', ['§1 Tax Rates', '§2 Tax Tables', '§7701 Definitions'], 6, COLORS['accent']),
        ('Level 1: Core Concepts', ['§152 Dependent', '§151 Exemptions', '§61 Gross Income'], 4.5, COLORS['primary']),
        ('Level 2: Deductions', ['§162 Business', '§163 Interest', '§164 Taxes'], 3, COLORS['primary']),
        ('Level 3: Credits', ['§32 EITC', '§24 CTC', '§36B Premium'], 1.5, COLORS['secondary']),
    ]

    for label, sections, y, color in levels:
        # Level label
        ax.text(0.3, y, label, fontsize=10, fontweight='bold', va='center')

        # Section boxes
        x_start = 3.5
        for i, sec in enumerate(sections):
            rect = mpatches.FancyBboxPatch(
                (x_start + i * 2.2, y - 0.35), 1.8, 0.7,
                boxstyle="round,pad=0.05,rounding_size=0.1",
                facecolor=color, edgecolor='white', alpha=0.8
            )
            ax.add_patch(rect)
            ax.text(x_start + i * 2.2 + 0.9, y, sec, fontsize=8,
                    ha='center', va='center', color='white', fontweight='bold')

    # Arrows showing dependency direction
    arrow_style = dict(arrowstyle='->', color=COLORS['gray'], lw=1.5)
    for y_from, y_to in [(6, 4.5), (4.5, 3), (3, 1.5)]:
        ax.annotate('', xy=(5, y_to + 0.5), xytext=(5, y_from - 0.5),
                    arrowprops=arrow_style)

    ax.text(5, 0.5, 'Encode top-down: foundations first, then dependents',
            ha='center', fontsize=10, style='italic', color=COLORS['gray'])

    ax.set_title('Optimal Encoding Order: Dependency Levels', fontsize=12, fontweight='bold', y=1.02)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'dependency_flow.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved {OUTPUT_DIR / 'dependency_flow.png'}")


def fig4_degree_distribution():
    """Figure 4: In-degree and out-degree distributions."""
    if USE_REAL_DATA:
        sequence = g.get_encoding_sequence()
        in_degrees = [item['dependencies'] for item in sequence]
        out_degrees = [item['dependents'] for item in sequence]
    else:
        # Example power-law-ish distributions
        np.random.seed(42)
        in_degrees = np.random.exponential(5, 2448).astype(int)
        out_degrees = np.random.exponential(3, 2448).astype(int)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

    # In-degree (dependencies) - use integer-aligned bins
    max_in = max(in_degrees)
    ax1.hist(in_degrees, bins=range(0, max_in + 2), color=COLORS['primary'], edgecolor='white', alpha=0.8)
    ax1.axvline(np.mean(in_degrees), color=COLORS['accent'], linestyle='--',
                label=f'Mean: {np.mean(in_degrees):.1f}')
    ax1.set_xlabel('Number of Dependencies (in-degree)', fontsize=10)
    ax1.set_ylabel('Number of Sections', fontsize=10)
    ax1.set_title('Dependencies per Section', fontsize=11, fontweight='bold')
    ax1.legend()
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)

    # Out-degree (dependents) - use integer-aligned bins
    max_out = max(out_degrees)
    ax2.hist(out_degrees, bins=range(0, max_out + 2), color=COLORS['secondary'], edgecolor='white', alpha=0.8)
    ax2.axvline(np.mean(out_degrees), color=COLORS['accent'], linestyle='--',
                label=f'Mean: {np.mean(out_degrees):.1f}')
    ax2.set_xlabel('Number of Dependents (out-degree)', fontsize=10)
    ax2.set_ylabel('Number of Sections', fontsize=10)
    ax2.set_title('Dependents per Section', fontsize=11, fontweight='bold')
    ax2.legend()
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'degree_distribution.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved {OUTPUT_DIR / 'degree_distribution.png'}")


def fig5_network_sample():
    """Figure 5: Sample network visualization around EITC (§32)."""
    try:
        import networkx as nx
    except ImportError:
        print("networkx required for network visualization")
        return

    # Create example subgraph around Section 32 (EITC)
    G = nx.DiGraph()

    # EITC and its direct dependencies
    eitc_deps = [
        ('32', '1'),      # tax rates
        ('32', '2'),      # tax tables
        ('32', '152'),    # dependent definition
        ('32', '151'),    # exemptions
        ('32', '911'),    # foreign income
        ('32', '7703'),   # marital status
        ('32', '6213'),   # deficiency procedures
    ]

    # Some of those have their own deps
    other_deps = [
        ('152', '151'),
        ('152', '7703'),
        ('1', '7701'),
        ('2', '1'),
        ('151', '7703'),
    ]

    G.add_edges_from(eitc_deps + other_deps)

    fig, ax = plt.subplots(figsize=(8, 6))

    # Position nodes in layers
    pos = {
        '32': (0.5, 0),
        '1': (0, 1), '2': (0.3, 1), '152': (0.5, 1), '151': (0.7, 1), '911': (0.85, 1), '7703': (1, 1),
        '6213': (0.15, 1),
        '7701': (0, 2),
    }

    # Node colors by type
    node_colors = []
    for node in G.nodes():
        if node == '32':
            node_colors.append(COLORS['accent'])
        elif node in ['1', '2', '7701']:
            node_colors.append(COLORS['primary'])
        else:
            node_colors.append(COLORS['secondary'])

    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors,
                           node_size=1500, alpha=0.9)
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=9, font_weight='bold',
                            labels={n: f'§{n}' for n in G.nodes()})
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color=COLORS['gray'],
                           arrows=True, arrowsize=15, alpha=0.6,
                           connectionstyle="arc3,rad=0.1")

    ax.set_title('Cross-Reference Network: §32 (EITC) Dependencies',
                 fontsize=12, fontweight='bold')
    ax.text(0.5, -0.15, 'Arrows point from dependent → dependency (encoding order is reversed)',
            ha='center', transform=ax.transAxes, fontsize=9, style='italic', color=COLORS['gray'])

    # Legend
    legend_elements = [
        mpatches.Patch(facecolor=COLORS['accent'], label='Target (§32 EITC)'),
        mpatches.Patch(facecolor=COLORS['primary'], label='Foundation sections'),
        mpatches.Patch(facecolor=COLORS['secondary'], label='Intermediate deps'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=8)

    ax.axis('off')
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'network_sample.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved {OUTPUT_DIR / 'network_sample.png'}")


def fig6_ordering_comparison():
    """Figure 6: Compare encoding orderings by forward reference count."""
    import random

    if not USE_REAL_DATA:
        print("Skipping ordering comparison (requires real data)")
        return

    def calculate_forward_refs(order):
        """Count forward references for an ordering."""
        encoded = set()
        forward_refs = []
        cumulative = 0

        for node in order:
            deps = set(g._graph.successors(node))
            unmet = len(deps - encoded)
            cumulative += unmet
            forward_refs.append(cumulative)
            encoded.add(node)

        return forward_refs

    # Get orderings
    optimal = g.topological_sort(allow_cycles=True)
    nodes = list(g._graph.nodes())

    # Numerical order
    def section_num(path):
        sec = path.split('/')[-1]
        num = ''.join(c for c in sec if c.isdigit())
        return int(num) if num else float('inf')
    numerical = sorted(nodes, key=section_num)

    # Random
    random.seed(42)
    random_order = nodes.copy()
    random.shuffle(random_order)

    # Calculate cumulative forward refs
    opt_refs = calculate_forward_refs(optimal)
    num_refs = calculate_forward_refs(numerical)
    rand_refs = calculate_forward_refs(random_order)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))

    # Left: Cumulative forward references
    x = np.arange(len(optimal))
    ax1.plot(x, opt_refs, color=COLORS['secondary'], label='Optimal (topological)', linewidth=2)
    ax1.plot(x, num_refs, color=COLORS['primary'], label='Numerical (§1, §2, ...)', linewidth=1.5, alpha=0.8)
    ax1.plot(x, rand_refs, color=COLORS['gray'], label='Random', linewidth=1.5, alpha=0.8)
    ax1.set_xlabel('Sections Encoded', fontsize=10)
    ax1.set_ylabel('Cumulative Forward References', fontsize=10)
    ax1.set_title('Forward References During Encoding', fontsize=11, fontweight='bold')
    ax1.legend(fontsize=8)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)

    # Right: Bar chart of totals
    orderings = ['Optimal', 'Numerical', 'Random', 'Reverse\nOptimal']
    totals = [opt_refs[-1], num_refs[-1], rand_refs[-1],
              calculate_forward_refs(list(reversed(optimal)))[-1]]
    colors = [COLORS['secondary'], COLORS['primary'], COLORS['gray'], COLORS['accent']]

    bars = ax2.bar(orderings, totals, color=colors, edgecolor='white')
    ax2.set_ylabel('Total Forward References', fontsize=10)
    ax2.set_title('Encoding Order Comparison', fontsize=11, fontweight='bold')
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)

    # Add value labels
    for bar, total in zip(bars, totals):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 100,
                f'{total:,}', ha='center', fontsize=9, color=COLORS['gray'])

    # Add improvement annotation
    improvement = (1 - opt_refs[-1] / totals[-1]) * 100
    ax2.annotate(f'{improvement:.0f}% reduction\nvs worst case',
                xy=(0, opt_refs[-1]), xytext=(1.5, opt_refs[-1] + 1500),
                fontsize=9, color=COLORS['secondary'],
                arrowprops=dict(arrowstyle='->', color=COLORS['secondary'], lw=1.5))

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'ordering_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved {OUTPUT_DIR / 'ordering_comparison.png'}")


if __name__ == '__main__':
    print(f"Using real data: {USE_REAL_DATA}")
    fig1_hub_sections()
    fig2_scc_distribution()
    fig3_dependency_flow()
    fig4_degree_distribution()
    fig5_network_sample()
    fig6_ordering_comparison()
    print("Done generating figures!")
