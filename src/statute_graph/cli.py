"""CLI for statute-graph analysis."""

import json
import random
from pathlib import Path

import click

from . import from_xml


@click.group()
@click.version_option()
def cli():
    """Analyze statutory cross-references for optimal encoding order."""
    pass


@cli.command()
@click.argument("xml_path", type=click.Path(exists=True, path_type=Path))
@click.option("-o", "--output", type=click.Path(path_type=Path), help="Output file path")
@click.option("--format", "fmt", type=click.Choice(["json", "csv"]), default="json", help="Output format")
def sequence(xml_path: Path, output: Path | None, fmt: str):
    """Generate optimal encoding sequence from USC XML.

    XML_PATH is the path to a US Code XML file (USLM format).
    """
    click.echo(f"Loading {xml_path}...", err=True)
    graph = from_xml(xml_path)

    click.echo(f"Computing encoding sequence for {graph.num_nodes} sections...", err=True)
    seq = graph.get_encoding_sequence()

    # Add section shorthand
    for item in seq:
        item["section"] = item["citation_path"].split("/")[-1]

    if fmt == "json":
        content = json.dumps(seq, indent=2)
    else:  # csv
        import csv
        from io import StringIO

        buffer = StringIO()
        writer = csv.DictWriter(buffer, fieldnames=["order", "section", "citation_path", "dependencies", "dependents", "scc_size"])
        writer.writeheader()
        writer.writerows(seq)
        content = buffer.getvalue()

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content)
        click.echo(f"Wrote {len(seq)} sections to {output}", err=True)
    else:
        click.echo(content)


@cli.command()
@click.argument("xml_path", type=click.Path(exists=True, path_type=Path))
def stats(xml_path: Path):
    """Print graph statistics.

    XML_PATH is the path to a US Code XML file (USLM format).
    """
    graph = from_xml(xml_path)
    seq = graph.get_encoding_sequence()
    sccs = graph.get_sccs()

    click.echo("=" * 50)
    click.echo("STATUTE GRAPH STATISTICS")
    click.echo("=" * 50)
    click.echo(f"Sections (nodes):        {graph.num_nodes:,}")
    click.echo(f"Cross-references (edges): {graph.num_edges:,}")
    click.echo(f"Graph density:           {graph.num_edges / (graph.num_nodes * (graph.num_nodes - 1)):.4f}")
    click.echo(f"Avg dependencies:        {sum(s['dependencies'] for s in seq) / len(seq):.1f}")
    click.echo(f"SCCs:                    {len(sccs)}")
    click.echo(f"Multi-node SCCs (cycles): {sum(1 for s in sccs if len(s) > 1)}")

    click.echo("\nTop 5 Hubs:")
    for path, count in graph.get_hubs(top_k=5):
        section = path.split("/")[-1]
        click.echo(f"  §{section}: {count} dependents")


@cli.command()
@click.argument("xml_path", type=click.Path(exists=True, path_type=Path))
@click.option("-o", "--output", type=click.Path(path_type=Path), help="Output JSON file")
def compare(xml_path: Path, output: Path | None):
    """Compare encoding orderings by forward reference count.

    XML_PATH is the path to a US Code XML file (USLM format).
    """
    graph = from_xml(xml_path)

    def calculate_forward_refs(order):
        """Count forward references for an ordering."""
        encoded = set()
        total = 0
        clean = 0
        for node in order:
            deps = set(graph._graph.successors(node))
            unmet = len(deps - encoded)
            total += unmet
            if unmet == 0:
                clean += 1
            encoded.add(node)
        return {"total_forward_refs": total, "pct_clean": clean / len(order) * 100}

    # Get orderings
    optimal = graph.topological_sort(allow_cycles=True)
    nodes = list(graph._graph.nodes())

    def section_num(path):
        sec = path.split("/")[-1]
        num = "".join(c for c in sec if c.isdigit())
        return int(num) if num else float("inf")

    numerical = sorted(nodes, key=section_num)

    random.seed(42)
    random_order = nodes.copy()
    random.shuffle(random_order)

    reverse_optimal = list(reversed(optimal))

    results = {
        "Optimal (topological)": calculate_forward_refs(optimal),
        "Numerical (§1, §2, ...)": calculate_forward_refs(numerical),
        "Random": calculate_forward_refs(random_order),
        "Reverse optimal": calculate_forward_refs(reverse_optimal),
    }

    click.echo("=" * 60)
    click.echo("ENCODING ORDER COMPARISON")
    click.echo("=" * 60)
    click.echo(f"{'Order':<25} {'Forward Refs':<15} {'% Clean':<10}")
    click.echo("-" * 60)
    for name, metrics in results.items():
        click.echo(f"{name:<25} {metrics['total_forward_refs']:<15,} {metrics['pct_clean']:.1f}%")

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(results, indent=2))
        click.echo(f"\nSaved to {output}", err=True)


@cli.command()
@click.argument("xml_path", type=click.Path(exists=True, path_type=Path))
@click.option("-o", "--output-dir", type=click.Path(path_type=Path), default="paper/_static", help="Output directory")
def generate(xml_path: Path, output_dir: Path):
    """Generate all paper data files.

    XML_PATH is the path to a US Code XML file (USLM format).

    Creates:
    - data/encoding_sequence.json
    - data/ordering_comparison.json
    - figures/*.png (if matplotlib available)
    """
    output_dir = Path(output_dir)
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    click.echo(f"Loading {xml_path}...", err=True)
    graph = from_xml(xml_path)
    click.echo(f"Loaded {graph.num_nodes} sections, {graph.num_edges} edges", err=True)

    # Generate encoding sequence
    seq = graph.get_encoding_sequence()
    for item in seq:
        item["section"] = item["citation_path"].split("/")[-1]
    seq_path = data_dir / "encoding_sequence.json"
    seq_path.write_text(json.dumps(seq, indent=2))
    click.echo(f"Wrote {seq_path}", err=True)

    # Generate ordering comparison
    def calculate_forward_refs(order):
        encoded = set()
        total = 0
        clean = 0
        max_blocked = 0
        for node in order:
            deps = set(graph._graph.successors(node))
            unmet = len(deps - encoded)
            total += unmet
            max_blocked = max(max_blocked, unmet)
            if unmet == 0:
                clean += 1
            encoded.add(node)
        return {
            "total_forward_refs": total,
            "max_blocked": max_blocked,
            "avg_blocked": total / len(order),
            "pct_zero_blocked": clean / len(order) * 100,
        }

    optimal = graph.topological_sort(allow_cycles=True)
    nodes = list(graph._graph.nodes())

    def section_num(path):
        sec = path.split("/")[-1]
        num = "".join(c for c in sec if c.isdigit())
        return int(num) if num else float("inf")

    numerical = sorted(nodes, key=section_num)
    random.seed(42)
    random_order = nodes.copy()
    random.shuffle(random_order)

    comparison = {
        "Optimal (topological)": calculate_forward_refs(optimal),
        "Numerical (§1, §2, ...)": calculate_forward_refs(numerical),
        "Random": calculate_forward_refs(random_order),
        "Reverse optimal": calculate_forward_refs(list(reversed(optimal))),
    }
    comp_path = data_dir / "ordering_comparison.json"
    comp_path.write_text(json.dumps(comparison, indent=2))
    click.echo(f"Wrote {comp_path}", err=True)

    click.echo("Done!", err=True)


if __name__ == "__main__":
    cli()
