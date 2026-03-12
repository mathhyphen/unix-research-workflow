#!/usr/bin/env python3
"""Tests for summarize module."""

import json
from pathlib import Path
from typing import Any, Dict

import pytest

from scripts.report_factory import ReportFactory
from scripts.summarize import (
    compute_summary,
    load_metrics,
)


class TestLoadMetrics:
    """Test suite for load_metrics function."""

    def test_load_metrics_reads_jsonl(self, tmp_path: Path) -> None:
        """Test that load_metrics reads JSONL file correctly."""
        metrics_file = tmp_path / "metrics.jsonl"
        with open(metrics_file, "w") as f:
            f.write(json.dumps({"loss": 0.5, "accuracy": 0.9}) + "\n")
            f.write(json.dumps({"loss": 0.3, "accuracy": 0.95}) + "\n")

        metrics = load_metrics(metrics_file)

        assert len(metrics) == 2
        assert metrics[0]["loss"] == 0.5
        assert metrics[1]["accuracy"] == 0.95

    def test_load_metrics_handles_empty_lines(self, tmp_path: Path) -> None:
        """Test that load_metrics handles empty lines gracefully."""
        metrics_file = tmp_path / "metrics.jsonl"
        with open(metrics_file, "w") as f:
            f.write(json.dumps({"loss": 0.5}) + "\n")
            f.write("\n")  # Empty line
            f.write(json.dumps({"loss": 0.3}) + "\n")

        metrics = load_metrics(metrics_file)

        assert len(metrics) == 2

    def test_load_metrics_empty_file(self, tmp_path: Path) -> None:
        """Test that load_metrics returns empty list for empty file."""
        metrics_file = tmp_path / "metrics.jsonl"
        metrics_file.touch()

        metrics = load_metrics(metrics_file)

        assert metrics == []


class TestComputeSummary:
    """Test suite for compute_summary function."""

    def test_compute_summary_empty_metrics(self) -> None:
        """Test that compute_summary returns empty dict for empty metrics."""
        summary = compute_summary([])
        assert summary == {}

    def test_compute_summary_single_metric(self) -> None:
        """Test compute_summary with single metric entry."""
        metrics = [{"loss": 0.5, "accuracy": 0.9}]
        summary = compute_summary(metrics)

        assert summary["loss"] == 0.5
        assert summary["accuracy"] == 0.9

    def test_compute_summary_multiple_metrics(self) -> None:
        """Test compute_summary computes mean correctly."""
        metrics = [
            {"loss": 0.6, "accuracy": 0.8},
            {"loss": 0.4, "accuracy": 1.0},
        ]
        summary = compute_summary(metrics)

        assert summary["loss"] == pytest.approx(0.5)
        assert summary["accuracy"] == pytest.approx(0.9)

    def test_compute_summary_excludes_timestamp(self) -> None:
        """Test that _timestamp is excluded from summary."""
        metrics = [
            {"loss": 0.5, "_timestamp": "2024-01-01T00:00:00"},
        ]
        summary = compute_summary(metrics)

        assert "_timestamp" not in summary
        assert "loss" in summary

    def test_compute_summary_handles_different_numeric_types(self) -> None:
        """Test that compute_summary handles int and float."""
        metrics = [
            {"int_metric": 10, "float_metric": 0.5},
            {"int_metric": 20, "float_metric": 0.7},
        ]
        summary = compute_summary(metrics)

        assert summary["int_metric"] == pytest.approx(15.0)
        assert summary["float_metric"] == pytest.approx(0.6)

    def test_compute_summary_ignores_non_numeric(self) -> None:
        """Test that non-numeric values are ignored (note: bool is int subclass in Python)."""
        metrics = [
            {"loss": 0.5, "name": "experiment_1"},
        ]
        summary = compute_summary(metrics)

        assert "loss" in summary
        assert "name" not in summary


class TestGenerateReport:
    """Test suite for ReportFactory.generate_report."""

    def test_generate_report_creates_file(self, tmp_path: Path) -> None:
        """Test that generate_report creates report.md file."""
        report_path = tmp_path / "findings" / "report.md"
        summary = {"loss": 0.25, "accuracy": 0.95}

        ReportFactory.generate_report("markdown", "test-exp", summary, report_path)

        assert report_path.exists()

    def test_generate_report_contains_experiment_name(self, tmp_path: Path) -> None:
        """Test that report contains experiment name in header."""
        report_path = tmp_path / "findings" / "report.md"
        summary = {"loss": 0.25}

        ReportFactory.generate_report("markdown", "my-experiment", summary, report_path)

        content = report_path.read_text()
        assert "# Experiment Report: my-experiment" in content

    def test_generate_report_contains_metrics(self, tmp_path: Path) -> None:
        """Test that report contains all metrics."""
        report_path = tmp_path / "findings" / "report.md"
        summary = {"loss": 0.25, "accuracy": 0.95, "f1_score": 0.88}

        ReportFactory.generate_report("markdown", "test-exp", summary, report_path)

        content = report_path.read_text()
        assert "loss" in content
        assert "accuracy" in content
        assert "f1_score" in content

    def test_generate_report_formats_values(self, tmp_path: Path) -> None:
        """Test that metric values are formatted to 4 decimal places."""
        report_path = tmp_path / "findings" / "report.md"
        summary = {"loss": 0.123456789}

        ReportFactory.generate_report("markdown", "test-exp", summary, report_path)

        content = report_path.read_text()
        assert "0.1235" in content  # Rounded to 4 decimal places

    def test_generate_report_creates_parent_directories(self, tmp_path: Path) -> None:
        """Test that generate_report creates parent directories."""
        report_path = tmp_path / "deep" / "nested" / "findings" / "report.md"
        summary = {"loss": 0.25}

        ReportFactory.generate_report("markdown", "test-exp", summary, report_path)

        assert report_path.parent.exists()

    def test_generate_report_empty_summary(self, tmp_path: Path) -> None:
        """Test that generate_report handles empty summary."""
        report_path = tmp_path / "findings" / "report.md"
        summary: Dict[str, float] = {}

        ReportFactory.generate_report("markdown", "test-exp", summary, report_path)

        content = report_path.read_text()
        assert "# Experiment Report: test-exp" in content
        assert "## Summary Metrics" in content

    def test_generate_report_sorted_keys(self, tmp_path: Path) -> None:
        """Test that metrics are sorted alphabetically in report."""
        report_path = tmp_path / "findings" / "report.md"
        summary = {"z_metric": 0.1, "a_metric": 0.2, "m_metric": 0.3}

        ReportFactory.generate_report("markdown", "test-exp", summary, report_path)

        content = report_path.read_text()
        lines = content.split("\n")

        # Find metric lines (those starting with "- **")
        metric_lines = [l for l in lines if l.startswith("- **")]
        assert len(metric_lines) == 3
        # Check they're in alphabetical order
        assert "a_metric" in metric_lines[0]
        assert "m_metric" in metric_lines[1]
        assert "z_metric" in metric_lines[2]


class TestSummarizeIntegration:
    """Integration tests for summarize module."""

    def test_full_workflow(self, tmp_path: Path) -> None:
        """Test the full workflow from metrics to report."""
        # Create metrics file
        metrics_file = tmp_path / "metrics.jsonl"
        with open(metrics_file, "w") as f:
            f.write(json.dumps({"epoch": 1, "loss": 0.6, "accuracy": 0.8}) + "\n")
            f.write(json.dumps({"epoch": 2, "loss": 0.4, "accuracy": 0.9}) + "\n")
            f.write(json.dumps({"epoch": 3, "loss": 0.2, "accuracy": 0.95}) + "\n")

        # Load and compute
        metrics = load_metrics(metrics_file)
        summary = compute_summary(metrics)

        # Generate report
        report_path = tmp_path / "report.md"
        ReportFactory.generate_report("markdown", "integration-test", summary, report_path)

        # Verify
        content = report_path.read_text()
        assert "integration-test" in content
        # Mean loss: (0.6 + 0.4 + 0.2) / 3 = 0.4
        assert "0.4000" in content
        # Mean accuracy: (0.8 + 0.9 + 0.95) / 3 = 0.8833...
        assert "0.8833" in content