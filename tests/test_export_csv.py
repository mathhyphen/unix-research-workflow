#!/usr/bin/env python3
"""Tests for export_csv module."""

import csv
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.export_csv import export_to_csv, load_metrics


class TestLoadMetrics:
    """Test suite for load_metrics function."""

    def test_load_metrics_success(self, tmp_path: Path) -> None:
        """Test loading metrics from JSONL file."""
        metrics_path = tmp_path / "metrics.jsonl"
        metrics_path.write_text(
            '{"_timestamp": "2024-01-01T00:00:00", "epoch": 1, "loss": 0.5}\n'
            '{"_timestamp": "2024-01-01T00:01:00", "epoch": 2, "loss": 0.4}\n'
        )

        metrics = load_metrics(metrics_path)
        assert len(metrics) == 2
        assert metrics[0]["epoch"] == 1
        assert metrics[0]["loss"] == 0.5
        assert metrics[1]["epoch"] == 2
        assert metrics[1]["loss"] == 0.4

    def test_load_metrics_empty_file(self, tmp_path: Path) -> None:
        """Test loading from empty file."""
        metrics_path = tmp_path / "metrics.jsonl"
        metrics_path.write_text("")

        metrics = load_metrics(metrics_path)
        assert metrics == []

    def test_load_metrics_ignores_empty_lines(self, tmp_path: Path) -> None:
        """Test that empty lines are ignored."""
        metrics_path = tmp_path / "metrics.jsonl"
        metrics_path.write_text(
            '{"epoch": 1}\n'
            '\n'
            '{"epoch": 2}\n'
        )

        metrics = load_metrics(metrics_path)
        assert len(metrics) == 2


class TestExportToCsv:
    """Test suite for export_to_csv function."""

    def test_export_to_csv_success(self, tmp_path: Path) -> None:
        """Test successful export to CSV."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        exp_dir = workspace / "test-exp"
        exp_dir.mkdir()
        logs_dir = exp_dir / "logs"
        logs_dir.mkdir(parents=True)

        metrics_path = logs_dir / "metrics.jsonl"
        metrics_path.write_text(
            '{"_timestamp": "2024-01-01T00:00:00", "epoch": 1, "loss": 0.5}\n'
            '{"_timestamp": "2024-01-01T00:01:00", "epoch": 2, "loss": 0.4}\n'
        )

        output_path = tmp_path / "output.csv"

        with patch("scripts.export_csv.BASE_DIR", tmp_path):
            result_path = export_to_csv("test-exp", output_path)
            assert result_path == output_path
            assert output_path.exists()

            # Verify CSV content
            with open(output_path, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                assert rows[0]["epoch"] == "1"
                assert rows[0]["loss"] == "0.5"
                assert rows[1]["epoch"] == "2"
                assert rows[1]["loss"] == "0.4"

    def test_export_to_csv_no_metrics(self, tmp_path: Path) -> None:
        """Test export when metrics file doesn't exist."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        exp_dir = workspace / "test-exp"
        exp_dir.mkdir()
        (exp_dir / "logs").mkdir()

        output_path = tmp_path / "output.csv"

        with patch("scripts.export_csv.BASE_DIR", tmp_path):
            with pytest.raises(FileNotFoundError):
                export_to_csv("test-exp", output_path)

    def test_export_to_csv_custom_output_path(self, tmp_path: Path) -> None:
        """Test export to custom output path."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        exp_dir = workspace / "test-exp"
        exp_dir.mkdir()
        logs_dir = exp_dir / "logs"
        logs_dir.mkdir(parents=True)

        metrics_path = logs_dir / "metrics.jsonl"
        metrics_path.write_text('{"epoch": 1, "accuracy": 0.95}\n')

        # Custom output directory
        custom_dir = tmp_path / "custom" / "output"
        custom_dir.mkdir(parents=True)
        output_path = custom_dir / "results.csv"

        with patch("scripts.export_csv.BASE_DIR", tmp_path):
            result_path = export_to_csv("test-exp", output_path)
            assert result_path == output_path
            assert output_path.exists()

    def test_export_to_csv_path_traversal_blocked(self, tmp_path: Path) -> None:
        """Test that path traversal attempts are blocked."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        with patch("scripts.export_csv.BASE_DIR", tmp_path):
            from scripts.utils import safe_path
            # Path traversal should be caught
            with pytest.raises(ValueError):
                safe_path(workspace, "../outside")

    def test_export_to_csv_timestamp_first_column(self, tmp_path: Path) -> None:
        """Test that _timestamp is first column in CSV."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        exp_dir = workspace / "test-exp"
        exp_dir.mkdir()
        logs_dir = exp_dir / "logs"
        logs_dir.mkdir(parents=True)

        metrics_path = logs_dir / "metrics.jsonl"
        metrics_path.write_text(
            '{"_timestamp": "2024-01-01T00:00:00", "z_key": 1, "a_key": 2}\n'
        )

        output_path = tmp_path / "output.csv"

        with patch("scripts.export_csv.BASE_DIR", tmp_path):
            export_to_csv("test-exp", output_path)

            with open(output_path, "r") as f:
                reader = csv.reader(f)
                headers = next(reader)
                assert headers[0] == "_timestamp"

    def test_export_to_csv_empty_metrics(self, tmp_path: Path) -> None:
        """Test export with empty metrics file."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        exp_dir = workspace / "test-exp"
        exp_dir.mkdir()
        logs_dir = exp_dir / "logs"
        logs_dir.mkdir(parents=True)

        metrics_path = logs_dir / "metrics.jsonl"
        metrics_path.write_text("")  # Empty file

        output_path = tmp_path / "output.csv"

        with patch("scripts.export_csv.BASE_DIR", tmp_path):
            with pytest.raises(ValueError, match="No data in metrics file"):
                export_to_csv("test-exp", output_path)
