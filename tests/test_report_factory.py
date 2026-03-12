#!/usr/bin/env python3
"""Tests for the ReportFactory and report format classes."""

from pathlib import Path
from typing import Any, Dict

import pytest

from scripts.report_factory import (
    ReportFactory,
    ReportFormat,
    MarkdownReport,
    JSONReport,
    HTMLReport,
)


class TestMarkdownReport:
    """Test suite for MarkdownReport class."""

    def test_generate_basic_report(self) -> None:
        """Test MarkdownReport generates basic report."""
        report = MarkdownReport()
        summary = {"loss": 0.5, "accuracy": 0.9}

        content = report.generate("test-exp", summary)

        assert "# Experiment Report: test-exp" in content
        assert "## Summary Metrics" in content
        assert "loss" in content
        assert "accuracy" in content

    def test_generate_formats_values(self) -> None:
        """Test that values are formatted to 4 decimal places."""
        report = MarkdownReport()
        summary = {"loss": 0.123456789}

        content = report.generate("test-exp", summary)

        assert "0.1235" in content  # Rounded

    def test_generate_sorted_keys(self) -> None:
        """Test that metrics are sorted alphabetically."""
        report = MarkdownReport()
        summary = {"z_metric": 0.1, "a_metric": 0.2, "m_metric": 0.3}

        content = report.generate("test-exp", summary)

        lines = content.split("\n")
        metric_lines = [l for l in lines if l.startswith("- **")]

        assert len(metric_lines) == 3
        assert "a_metric" in metric_lines[0]
        assert "m_metric" in metric_lines[1]
        assert "z_metric" in metric_lines[2]

    def test_generate_with_metadata(self) -> None:
        """Test MarkdownReport includes metadata."""
        report = MarkdownReport()
        summary = {"loss": 0.5}
        metadata = {"python_version": "3.9", "platform": "linux"}

        content = report.generate("test-exp", summary, metadata)

        assert "## Metadata" in content
        assert "python_version" in content
        assert "3.9" in content

    def test_generate_empty_summary(self) -> None:
        """Test MarkdownReport handles empty summary."""
        report = MarkdownReport()
        summary: Dict[str, float] = {}

        content = report.generate("test-exp", summary)

        assert "# Experiment Report: test-exp" in content
        assert "## Summary Metrics" in content

    def test_extension(self) -> None:
        """Test MarkdownReport returns correct extension."""
        report = MarkdownReport()
        assert report.extension() == ".md"


class TestJSONReport:
    """Test suite for JSONReport class."""

    def test_generate_basic_report(self) -> None:
        """Test JSONReport generates basic report."""
        report = JSONReport()
        summary = {"loss": 0.5, "accuracy": 0.9}

        content = report.generate("test-exp", summary)

        assert '"experiment": "test-exp"' in content
        assert '"summary"' in content
        assert '"loss": 0.5' in content

    def test_generate_valid_json(self) -> None:
        """Test that JSONReport generates valid JSON."""
        import json

        report = JSONReport()
        summary = {"loss": 0.5, "accuracy": 0.9}

        content = report.generate("test-exp", summary)
        data = json.loads(content)

        assert data["experiment"] == "test-exp"
        assert data["summary"]["loss"] == 0.5

    def test_generate_with_metadata(self) -> None:
        """Test JSONReport includes metadata."""
        report = JSONReport()
        summary = {"loss": 0.5}
        metadata = {"python_version": "3.9"}

        content = report.generate("test-exp", summary, metadata)
        import json
        data = json.loads(content)

        assert data["metadata"]["python_version"] == "3.9"

    def test_extension(self) -> None:
        """Test JSONReport returns correct extension."""
        report = JSONReport()
        assert report.extension() == ".json"


class TestHTMLReport:
    """Test suite for HTMLReport class."""

    def test_generate_basic_report(self) -> None:
        """Test HTMLReport generates basic report."""
        report = HTMLReport()
        summary = {"loss": 0.5, "accuracy": 0.9}

        content = report.generate("test-exp", summary)

        assert "<!DOCTYPE html>" in content
        assert "<h1>Experiment Report: test-exp</h1>" in content
        assert "<table>" in content
        assert "loss" in content
        assert "accuracy" in content

    def test_generate_valid_html(self) -> None:
        """Test that HTMLReport generates valid HTML structure."""
        report = HTMLReport()
        summary = {"loss": 0.5}

        content = report.generate("test-exp", summary)

        assert "<!DOCTYPE html>" in content
        assert "</html>" in content
        assert "<html>" in content

    def test_generate_with_metadata(self) -> None:
        """Test HTMLReport includes metadata table."""
        report = HTMLReport()
        summary = {"loss": 0.5}
        metadata = {"python_version": "3.9"}

        content = report.generate("test-exp", summary, metadata)

        assert "<h2>Metadata</h2>" in content
        assert "python_version" in content

    def test_extension(self) -> None:
        """Test HTMLReport returns correct extension."""
        report = HTMLReport()
        assert report.extension() == ".html"


class TestReportFactory:
    """Test suite for ReportFactory class."""

    def test_get_format_markdown(self) -> None:
        """Test ReportFactory.get_format for markdown."""
        formatter = ReportFactory.get_format("markdown")
        assert isinstance(formatter, MarkdownReport)

    def test_get_format_md_shortcut(self) -> None:
        """Test ReportFactory.get_format for md shortcut."""
        formatter = ReportFactory.get_format("md")
        assert isinstance(formatter, MarkdownReport)

    def test_get_format_json(self) -> None:
        """Test ReportFactory.get_format for json."""
        formatter = ReportFactory.get_format("json")
        assert isinstance(formatter, JSONReport)

    def test_get_format_html(self) -> None:
        """Test ReportFactory.get_format for html."""
        formatter = ReportFactory.get_format("html")
        assert isinstance(formatter, HTMLReport)

    def test_get_format_case_insensitive(self) -> None:
        """Test that format lookup is case insensitive."""
        formatter1 = ReportFactory.get_format("MARKDOWN")
        formatter2 = ReportFactory.get_format("Markdown")
        formatter3 = ReportFactory.get_format("markdown")

        assert type(formatter1) == type(formatter2) == type(formatter3)

    def test_get_format_invalid(self) -> None:
        """Test ReportFactory.get_format with invalid format."""
        with pytest.raises(ValueError, match="Unknown report format"):
            ReportFactory.get_format("invalid_format")

    def test_list_formats(self) -> None:
        """Test ReportFactory.list_formats."""
        formats = ReportFactory.list_formats()

        assert "markdown" in formats
        assert "md" in formats
        assert "json" in formats
        assert "html" in formats
        assert isinstance(formats, list)

    def test_generate_report_markdown(self, tmp_path: Path) -> None:
        """Test ReportFactory.generate_report with markdown."""
        summary = {"loss": 0.5}
        output_path = tmp_path / "report.md"

        result = ReportFactory.generate_report(
            "markdown", "test-exp", summary, output_path
        )

        assert result.exists()
        content = result.read_text()
        assert "# Experiment Report: test-exp" in content

    def test_generate_report_json(self, tmp_path: Path) -> None:
        """Test ReportFactory.generate_report with json."""
        summary = {"loss": 0.5}
        output_path = tmp_path / "report.json"

        result = ReportFactory.generate_report(
            "json", "test-exp", summary, output_path
        )

        assert result.exists()
        content = result.read_text()
        assert '"experiment": "test-exp"' in content

    def test_generate_report_html(self, tmp_path: Path) -> None:
        """Test ReportFactory.generate_report with html."""
        summary = {"loss": 0.5}
        output_path = tmp_path / "report.html"

        result = ReportFactory.generate_report(
            "html", "test-exp", summary, output_path
        )

        assert result.exists()
        content = result.read_text()
        assert "<!DOCTYPE html>" in content

    def test_generate_report_creates_directories(
        self, tmp_path: Path
    ) -> None:
        """Test that generate_report creates parent directories."""
        summary = {"loss": 0.5}
        output_path = tmp_path / "nested" / "path" / "report.md"

        result = ReportFactory.generate_report(
            "markdown", "test-exp", summary, output_path
        )

        assert result.parent.exists()

    def test_generate_report_fixes_extension(self, tmp_path: Path) -> None:
        """Test that generate_report uses correct extension."""
        summary = {"loss": 0.5}
        # Wrong extension
        output_path = tmp_path / "report.txt"

        result = ReportFactory.generate_report(
            "json", "test-exp", summary, output_path
        )

        assert result.suffix == ".json"

    def test_register_format(self) -> None:
        """Test registering a custom format."""

        class CustomFormat(ReportFormat):
            def generate(
                self,
                name: str,
                summary: Dict[str, float],
                metadata: Dict[str, Any] = None,
            ) -> str:
                return f"Custom: {name}"

            def extension(self) -> str:
                return ".custom"

        # Register
        ReportFactory.register_format("custom", CustomFormat())

        # Should be able to get it
        formatter = ReportFactory.get_format("custom")
        assert isinstance(formatter, CustomFormat)

        # Clean up - remove from registry
        del ReportFactory._formats["custom"]
