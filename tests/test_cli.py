"""Tests for CLI commands."""

import json
from pathlib import Path
from click.testing import CliRunner
import pytest

from statute_graph.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def temp_output(tmp_path):
    return tmp_path / "output"


class TestSequenceCommand:
    """Tests for the 'sequence' command."""

    def test_sequence_requires_input(self, runner):
        """Sequence command requires an input file."""
        result = runner.invoke(cli, ["sequence"])
        assert result.exit_code != 0
        assert "Missing argument" in result.output or "Usage:" in result.output

    def test_sequence_json_output(self, runner, tmp_path, sample_xml):
        """Sequence command outputs JSON by default."""
        output = tmp_path / "sequence.json"
        result = runner.invoke(cli, ["sequence", str(sample_xml), "-o", str(output)])
        assert result.exit_code == 0
        assert output.exists()
        data = json.loads(output.read_text())
        assert isinstance(data, list)
        assert len(data) > 0
        assert "citation_path" in data[0]
        assert "order" in data[0]

    def test_sequence_csv_output(self, runner, tmp_path, sample_xml):
        """Sequence command can output CSV."""
        output = tmp_path / "sequence.csv"
        result = runner.invoke(cli, ["sequence", str(sample_xml), "-o", str(output), "--format", "csv"])
        assert result.exit_code == 0
        assert output.exists()
        content = output.read_text()
        assert "citation_path" in content
        assert "order" in content


class TestStatsCommand:
    """Tests for the 'stats' command."""

    def test_stats_output(self, runner, sample_xml):
        """Stats command prints graph statistics."""
        result = runner.invoke(cli, ["stats", str(sample_xml)])
        assert result.exit_code == 0
        assert "nodes" in result.output.lower() or "sections" in result.output.lower()


class TestCompareCommand:
    """Tests for the 'compare' command."""

    def test_compare_output(self, runner, sample_xml):
        """Compare command shows ordering comparison."""
        result = runner.invoke(cli, ["compare", str(sample_xml)])
        assert result.exit_code == 0
        assert "optimal" in result.output.lower()
        assert "forward" in result.output.lower()


class TestGenerateCommand:
    """Tests for the 'generate' command."""

    def test_generate_creates_files(self, runner, tmp_path, sample_xml):
        """Generate command creates data files."""
        output_dir = tmp_path / "output"
        result = runner.invoke(cli, ["generate", str(sample_xml), "-o", str(output_dir)])
        assert result.exit_code == 0

        # Check files exist
        assert (output_dir / "data" / "encoding_sequence.json").exists()
        assert (output_dir / "data" / "ordering_comparison.json").exists()

        # Verify content
        seq = json.loads((output_dir / "data" / "encoding_sequence.json").read_text())
        assert len(seq) == 3  # 3 sections in sample XML


@pytest.fixture
def sample_xml(tmp_path):
    """Create a minimal sample XML for testing (USLM format)."""
    xml_content = """<?xml version="1.0"?>
<usc xmlns="http://xml.house.gov/schemas/uslm/1.0">
  <main>
    <section identifier="/us/usc/t26/s1">
      <heading>Tax imposed</heading>
      <content>
        <p>There is hereby imposed on the taxable income...</p>
      </content>
    </section>
    <section identifier="/us/usc/t26/s2">
      <heading>Definitions</heading>
      <content>
        <p>For purposes of <ref href="/us/usc/t26/s1">section 1</ref>...</p>
      </content>
    </section>
    <section identifier="/us/usc/t26/s32">
      <heading>Earned income credit</heading>
      <content>
        <p>See <ref href="/us/usc/t26/s1">section 1</ref> and
           <ref href="/us/usc/t26/s2">section 2</ref>.</p>
      </content>
    </section>
  </main>
</usc>"""
    xml_path = tmp_path / "usc26.xml"  # Named to match expected pattern
    xml_path.write_text(xml_content)
    return xml_path
