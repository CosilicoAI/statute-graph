"""Loaders for building StatuteGraph from various sources."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterator

from .graph import StatuteGraph


def parse_usc_href(href: str) -> tuple[str, str, str] | None:
    """Parse /us/usc/t26/s151 into (jurisdiction, title, section).

    Returns None if not a valid USC reference.
    """
    match = re.match(r"/us/usc/t(\d+)/s(\d+[A-Za-z]?)(?:/(.+))?", href)
    if match:
        title = match.group(1)
        section = match.group(2)
        subsection = match.group(3)
        if subsection:
            return ("us", title, f"{section}/{subsection}")
        return ("us", title, section)
    return None


def build_citation_path(jurisdiction: str, title: str, section: str) -> str:
    """Build citation_path in standard format: us/statute/26/32."""
    return f"{jurisdiction}/statute/{title}/{section}"


class USCodeLoader:
    """Load US Code XML files into a StatuteGraph."""

    def __init__(self, data_dir: Path | str):
        """Initialize with directory containing usc*.xml files."""
        self.data_dir = Path(data_dir)

    def load_title(self, title: int) -> StatuteGraph:
        """Load a single title (e.g., Title 26 = Internal Revenue Code)."""
        xml_path = self.data_dir / f"usc{title}.xml"
        if not xml_path.exists():
            raise FileNotFoundError(f"USC XML not found: {xml_path}")

        return self._parse_xml(xml_path, str(title))

    def load_all(self) -> StatuteGraph:
        """Load all available titles into a single graph."""
        g = StatuteGraph()
        for xml_path in sorted(self.data_dir.glob("usc*.xml")):
            # Extract title number from filename
            match = re.match(r"usc(\d+)\.xml", xml_path.name)
            if match:
                title = match.group(1)
                self._parse_into_graph(xml_path, title, g)
        return g

    def _parse_xml(self, xml_path: Path, title: str) -> StatuteGraph:
        """Parse a single XML file into a new graph."""
        g = StatuteGraph()
        self._parse_into_graph(xml_path, title, g)
        return g

    def _parse_into_graph(
        self, xml_path: Path, title: str, graph: StatuteGraph
    ) -> None:
        """Parse XML and add nodes/edges to existing graph."""
        tree = ET.parse(xml_path)
        root = tree.getroot()

        ns = {"uslm": "http://xml.house.gov/schemas/uslm/1.0"}

        # First pass: add all section nodes
        for section in root.iter("{http://xml.house.gov/schemas/uslm/1.0}section"):
            identifier = section.get("identifier", "")
            if not identifier:
                continue

            parsed = parse_usc_href(identifier)
            if not parsed:
                continue

            jurisdiction, sec_title, sec_num = parsed
            citation_path = build_citation_path(jurisdiction, sec_title, sec_num)

            # Get heading
            heading_elem = section.find("uslm:heading", ns)
            heading = heading_elem.text if heading_elem is not None else ""

            graph.add_node(citation_path, title=sec_title, heading=heading)

        # Second pass: add edges from cross-references
        for section in root.iter("{http://xml.house.gov/schemas/uslm/1.0}section"):
            identifier = section.get("identifier", "")
            if not identifier:
                continue

            from_parsed = parse_usc_href(identifier)
            if not from_parsed:
                continue

            from_path = build_citation_path(*from_parsed)

            # Find all <ref> elements in this section
            for ref in section.iter("{http://xml.house.gov/schemas/uslm/1.0}ref"):
                href = ref.get("href", "")
                if not href:
                    continue

                to_parsed = parse_usc_href(href)
                if not to_parsed:
                    continue

                to_path = build_citation_path(*to_parsed)
                ref_text = "".join(ref.itertext()).strip()

                # Determine reference type
                if to_parsed[1] == from_parsed[1]:  # Same title
                    ref_type = "internal_section"
                else:
                    ref_type = "external_title"

                # Only add edge if target node exists or is in same title
                if to_path in graph or to_parsed[1] == from_parsed[1]:
                    if to_path not in graph:
                        graph.add_node(to_path, title=to_parsed[1])
                    graph.add_edge(from_path, to_path, ref_type=ref_type, text=ref_text)


def from_xml(xml_path: Path | str) -> StatuteGraph:
    """Convenience function to load a single USC XML file."""
    xml_path = Path(xml_path)
    match = re.match(r"usc(\d+)\.xml", xml_path.name)
    title = match.group(1) if match else "0"

    loader = USCodeLoader(xml_path.parent)
    return loader._parse_xml(xml_path, title)
