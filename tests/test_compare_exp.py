#!/usr/bin/env python3
"""Tests for compare_exp module."""

import argparse
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.compare_exp import compare_experiments, load_final_metrics


class TestLoadFinalMetrics:
    """Test suite for load_final_metrics function."""

    def test_load_final_metrics_success(self, tmp_path: Path) -> None:
        """Test loading final metrics from file."""
        metrics_path = tmp_path / "metrics.jsonl"
        metrics_path.write_text(
            '{"type": "environment", "python_version": "3.9"}\n'
            '{"epoch": 1, "val_loss": 0.5}\n'
            '{"epoch": 2, "val_loss": 0.4}\n'
            '{"epoch": 3, "val_loss": 0.3}\n'
        )

        result = load_final_metrics(metrics_path)
        assert result is not None
        assert result["epoch"] == 3
        assert result["val_loss"] == 0.3

    def test_load_final_metrics_empty_file(self, tmp_path: Path) -> None:
        """Test loading from empty file."""
        metrics_path = tmp_path / "metrics.jsonl"
        metrics_path.write_text("")

        result = load_final_metrics(metrics_path)
        assert result is None

    def test_load_final_metrics_missing_file(self, tmp_path: Path) -> None:
        """Test loading from non-existent file."""
        metrics_path = tmp_path / "metrics.jsonl"
        result = load_final_metrics(metrics_path)
        assert result is None

    def test_load_final_metrics_skips_environment(self, tmp_path: Path) -> None:
        """Test that environment entries are skipped."""
        metrics_path = tmp_path / "metrics.jsonl"
        metrics_path.write_text(
            '{"type": "environment", "python_version": "3.9"}\n'
            '{"type": "environment", "platform": "linux"}\n'
            '{"epoch": 1, "val_loss": 0.5}\n'
        )

        result = load_final_metrics(metrics_path)
        assert result is not None
        assert result["epoch"] == 1
        assert "type" not in result or result.get("type") != "environment"

    def test_load_final_metrics_only_environment(self, tmp_path: Path) -> None:
        """Test when only environment entries exist."""
        metrics_path = tmp_path / "metrics.jsonl"
        metrics_path.write_text(
            '{"type": "environment", "python_version": "3.9"}\n'
            '{"type": "environment", "platform": "linux"}\n'
        )

        result = load_final_metrics(metrics_path)
        assert result is None


class TestCompareExperiments:
    """Test suite for compare_experiments function."""

    def test_compare_experiments_success(self, tmp_path: Path) -> None:
        """Test successful comparison of experiments."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        # Create exp1
        exp1_dir = workspace / "exp1"
        exp1_dir.mkdir()
        logs1_dir = exp1_dir / "logs"
        logs1_dir.mkdir(parents=True)
        (logs1_dir / "metrics.jsonl").write_text('{"val_loss": 0.5}\n')

        # Create exp2
        exp2_dir = workspace / "exp2"
        exp2_dir.mkdir()
        logs2_dir = exp2_dir / "logs"
        logs2_dir.mkdir(parents=True)
        (logs2_dir / "metrics.jsonl").write_text('{"val_loss": 0.3}\n')

        with patch("scripts.compare_exp.BASE_DIR", tmp_path):
            result = compare_experiments(["exp1", "exp2"], "val_loss")
            assert result == 0

    def test_compare_experiments_no_metrics(self, tmp_path: Path) -> None:
        """Test comparison when no metrics exist."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        with patch("scripts.compare_exp.BASE_DIR", tmp_path):
            result = compare_experiments(["exp1", "exp2"], "val_loss")
            assert result == 2  # Returns 2 when no comparable data found

    def test_compare_experiments_invalid_name(self, tmp_path: Path) -> None:
        """Test that invalid experiment names are handled."""
        from scripts.utils import validate_experiment_name

        with pytest.raises(argparse.ArgumentTypeError):
            validate_experiment_name("invalid/name")

    def test_compare_experiments_single_experiment(self, tmp_path: Path) -> None:
        """Test comparison with single experiment."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        exp_dir = workspace / "exp1"
        exp_dir.mkdir()
        logs_dir = exp_dir / "logs"
        logs_dir.mkdir(parents=True)
        (logs_dir / "metrics.jsonl").write_text('{"val_loss": 0.5}\n')

        with patch("scripts.compare_exp.BASE_DIR", tmp_path):
            result = compare_experiments(["exp1"], "val_loss")
            assert result == 0

    def test_compare_experiments_missing_metric_key(self, tmp_path: Path) -> None:
        """Test comparison when metric key is missing."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        exp_dir = workspace / "exp1"
        exp_dir.mkdir()
        logs_dir = exp_dir / "logs"
        logs_dir.mkdir(parents=True)
        (logs_dir / "metrics.jsonl").write_text('{"other_metric": 0.5}\n')

        with patch("scripts.compare_exp.BASE_DIR", tmp_path):
            result = compare_experiments(["exp1"], "val_loss")
            assert result == 2  # No comparable data

    def test_compare_experiments_sorted_by_value(self, tmp_path: Path, capsys) -> None:
        """Test that results are sorted by metric value."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        # Create exp with higher loss (worse)
        exp1_dir = workspace / "exp-high"
        exp1_dir.mkdir()
        logs1_dir = exp1_dir / "logs"
        logs1_dir.mkdir(parents=True)
        (logs1_dir / "metrics.jsonl").write_text('{"val_loss": 0.8}\n')

        # Create exp with lower loss (better)
        exp2_dir = workspace / "exp-low"
        exp2_dir.mkdir()
        logs2_dir = exp2_dir / "logs"
        logs2_dir.mkdir(parents=True)
        (logs2_dir / "metrics.jsonl").write_text('{"val_loss": 0.2}\n')

        # Create exp with medium loss
        exp3_dir = workspace / "exp-mid"
        exp3_dir.mkdir()
        logs3_dir = exp3_dir / "logs"
        logs3_dir.mkdir(parents=True)
        (logs3_dir / "metrics.jsonl").write_text('{"val_loss": 0.5}\n')

        with patch("scripts.compare_exp.BASE_DIR", tmp_path):
            compare_experiments(["exp-high", "exp-low", "exp-mid"], "val_loss")
            captured = capsys.readouterr()
            # Lower values should appear first (sorted best to worst)
            assert captured.out.index("exp-low") < captured.out.index("exp-mid")
            assert captured.out.index("exp-mid") < captured.out.index("exp-high")

    def test_compare_experiments_custom_metric(self, tmp_path: Path) -> None:
        """Test comparison with custom metric key."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        exp1_dir = workspace / "exp1"
        exp1_dir.mkdir()
        logs1_dir = exp1_dir / "logs"
        logs1_dir.mkdir(parents=True)
        (logs1_dir / "metrics.jsonl").write_text('{"accuracy": 0.95}\n')

        exp2_dir = workspace / "exp2"
        exp2_dir.mkdir()
        logs2_dir = exp2_dir / "logs"
        logs2_dir.mkdir(parents=True)
        (logs2_dir / "metrics.jsonl").write_text('{"accuracy": 0.85}\n')

        with patch("scripts.compare_exp.BASE_DIR", tmp_path):
            result = compare_experiments(["exp1", "exp2"], "accuracy")
            assert result == 0

    def test_compare_experiments_mixed_valid_invalid(self, tmp_path: Path) -> None:
        """Test comparison with mix of valid and invalid experiments."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        # Valid experiment
        exp1_dir = workspace / "exp1"
        exp1_dir.mkdir()
        logs1_dir = exp1_dir / "logs"
        logs1_dir.mkdir(parents=True)
        (logs1_dir / "metrics.jsonl").write_text('{"val_loss": 0.5}\n')

        # Invalid experiment (doesn't exist)

        with patch("scripts.compare_exp.BASE_DIR", tmp_path):
            # Should still succeed with one valid experiment
            result = compare_experiments(["exp1", "nonexistent"], "val_loss")
            assert result == 0
