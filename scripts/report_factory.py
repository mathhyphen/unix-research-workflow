#!/usr/bin/env python3
"""Report generation factory supporting multiple output formats."""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List


class ReportFormat(ABC):
    """Abstract base class for report formats."""

    @abstractmethod
    def generate(self, name: str, summary: Dict[str, float], metadata: Dict[str, Any] = None) -> str:
        """Generate report content.

        Args:
            name: Experiment name.
            summary: Dictionary of metric summaries.
            metadata: Optional metadata dictionary.

        Returns:
            Report content as string.
        """
        pass

    @abstractmethod
    def extension(self) -> str:
        """Return file extension."""
        pass


class MarkdownReport(ReportFormat):
    """Markdown format report."""

    def generate(self, name: str, summary: Dict[str, float], metadata: Dict[str, Any] = None) -> str:
        lines: List[str] = [
            f"# Experiment Report: {name}",
            "",
            "## Summary Metrics",
            "",
        ]

        for key, value in sorted(summary.items()):
            lines.append(f"- **{key}**: {value:.4f}")

        if metadata:
            lines.extend(["", "## Metadata", ""])
            for key, value in sorted(metadata.items()):
                lines.append(f"- **{key}**: {value}")

        lines.append("")
        return "\n".join(lines)

    def extension(self) -> str:
        return ".md"


class JSONReport(ReportFormat):
    """JSON format report."""

    def generate(self, name: str, summary: Dict[str, float], metadata: Dict[str, Any] = None) -> str:
        report_data: Dict[str, Any] = {
            "experiment": name,
            "summary": summary,
        }
        if metadata:
            report_data["metadata"] = metadata
        return json.dumps(report_data, indent=2)

    def extension(self) -> str:
        return ".json"


class HTMLReport(ReportFormat):
    """HTML format report."""

    def generate(self, name: str, summary: Dict[str, float], metadata: Dict[str, Any] = None) -> str:
        lines: List[str] = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            f"  <title>Experiment Report: {name}</title>",
            "  <style>",
            "    body { font-family: sans-serif; max-width: 800px; margin: 2em auto; padding: 0 1em; }",
            "    h1 { color: #333; }",
            "    table { border-collapse: collapse; width: 100%; }",
            "    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
            "    th { background-color: #4CAF50; color: white; }",
            "  </style>",
            "</head>",
            "<body>",
            f"  <h1>Experiment Report: {name}</h1>",
            "  <h2>Summary Metrics</h2>",
            "  <table>",
            "    <tr><th>Metric</th><th>Value</th></tr>",
        ]

        for key, value in sorted(summary.items()):
            lines.append(f"    <tr><td>{key}</td><td>{value:.4f}</td></tr>")

        lines.append("  </table>")

        if metadata:
            lines.extend([
                "  <h2>Metadata</h2>",
                "  <table>",
                "    <tr><th>Key</th><th>Value</th></tr>",
            ])
            for key, value in sorted(metadata.items()):
                lines.append(f"    <tr><td>{key}</td><td>{value}</td></tr>")
            lines.append("  </table>")

        lines.extend(["</body>", "</html>"])
        return "\n".join(lines)

    def extension(self) -> str:
        return ".html"


class ReportFactory:
    """Factory for creating report generators."""

    _formats: Dict[str, ReportFormat] = {
        "markdown": MarkdownReport(),
        "md": MarkdownReport(),
        "json": JSONReport(),
        "html": HTMLReport(),
    }

    @classmethod
    def get_format(cls, name: str) -> ReportFormat:
        """Get report format by name."""
        name_lower = name.lower()
        if name_lower not in cls._formats:
            available = ", ".join(sorted(set(cls._formats.keys())))
            raise ValueError(f"Unknown report format: '{name}'. Available: {available}")
        return cls._formats[name_lower]

    @classmethod
    def list_formats(cls) -> List[str]:
        """List available format names."""
        return sorted(set(cls._formats.keys()))

    @classmethod
    def register_format(cls, name: str, formatter: ReportFormat) -> None:
        """Register a new report format."""
        cls._formats[name.lower()] = formatter

    @classmethod
    def generate_report(
        cls,
        format_name: str,
        experiment_name: str,
        summary: Dict[str, float],
        output_path: Path,
        metadata: Dict[str, Any] = None,
    ) -> Path:
        """Generate and save a report."""
        formatter = cls.get_format(format_name)
        content = formatter.generate(experiment_name, summary, metadata)

        if not str(output_path).endswith(formatter.extension()):
            output_path = output_path.with_suffix(formatter.extension())

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")

        return output_path
