#!/usr/bin/env python3
"""Tests for show_exp module."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.show_exp import count_metrics, load_intent, show_experiment


class TestLoadIntent:
    """Test suite for load_intent function."""

    def test_load_intent_success(self, tmp_path: Path) -> None:
        """Test loading a valid intent.yaml file."""
        intent_path = tmp_path / "intent.yaml"
        intent_path.write_text("""experiment: test-exp
branch: expl/test-exp
objective: |
  This is a test objective.
  It has multiple lines.
hypothesis: |
  This is a test hypothesis.
""")

        result = load_intent(intent_path)
        assert result is not None
        assert result["experiment"] == "test-exp"
        assert result["branch"] == "expl/test-exp"
        assert "test objective" in result["objective"]
        assert "test hypothesis" in result["hypothesis"]

    def test_load_intent_missing_file(self, tmp_path: Path) -> None:
        """Test loading non-existent intent file."""
        intent_path = tmp_path / "intent.yaml"
        result = load_intent(intent_path)
        assert result is None

    def test_load_intent_simple_format(self, tmp_path: Path) -> None:
        """Test loading intent with simple key-value pairs."""
        intent_path = tmp_path / "intent.yaml"
        intent_path.write_text("""experiment: simple-exp
branch: main
""")

        result = load_intent(intent_path)
        assert result is not None
        assert result["experiment"] == "simple-exp"
        assert result["branch"] == "main"


class TestCountMetrics:
    """Test suite for count_metrics function."""

    def test_count_metrics_success(self, tmp_path: Path) -> None:
        """Test counting metrics in a valid file."""
        metrics_path = tmp_path / "metrics.jsonl"
        metrics_path.write_text(
            '{"epoch": 1, "loss": 0.5}\n'
            '{"epoch": 2, "loss": 0.4}\n'
            '{"epoch": 3, "loss": 0.3}\n'
        )

        count = count_metrics(metrics_path)
        assert count == 3

    def test_count_metrics_empty_file(self, tmp_path: Path) -> None:
        """Test counting metrics in an empty file."""
        metrics_path = tmp_path / "metrics.jsonl"
        metrics_path.write_text("")

        count = count_metrics(metrics_path)
        assert count == 0

    def test_count_metrics_missing_file(self, tmp_path: Path) -> None:
        """Test counting metrics when file doesn't exist."""
        metrics_path = tmp_path / "metrics.jsonl"
        count = count_metrics(metrics_path)
        assert count == 0

    def test_count_metrics_ignores_empty_lines(self, tmp_path: Path) -> None:
        """Test that empty lines are ignored."""
        metrics_path = tmp_path / "metrics.jsonl"
        metrics_path.write_text(
            '{"epoch": 1}\n'
            '\n'
            '{"epoch": 2}\n'
            '\n'
            '\n'
        )

        count = count_metrics(metrics_path)
        assert count == 2


class TestShowExperiment:
    """Test suite for show_experiment function."""

    def test_show_experiment_success(self, tmp_path: Path, caplog) -> None:
        """Test showing a valid experiment."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        exp_dir = workspace / "test-exp"
        exp_dir.mkdir()
        (exp_dir / "logs").mkdir()
        (exp_dir / "findings").mkdir()

        # Create intent.yaml
        intent_path = exp_dir / "intent.yaml"
        intent_path.write_text("""experiment: test-exp
branch: expl/test-exp
objective: |
  Test objective for the experiment.
hypothesis: |
  Test hypothesis.
""")

        # Create metrics
        metrics_path = exp_dir / "logs" / "metrics.jsonl"
        metrics_path.write_text('{"epoch": 1, "loss": 0.5}\n')

        with patch("scripts.show_exp.BASE_DIR", tmp_path):
            with patch("scripts.show_exp.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0, stdout="expl/test-exp\n"
                )
                result = show_experiment("test-exp")
                assert result == 0

    def test_show_experiment_not_found(self, tmp_path: Path) -> None:
        """Test showing non-existent experiment."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        with patch("scripts.show_exp.BASE_DIR", tmp_path):
            result = show_experiment("non-existent")
            assert result == 1

    def test_show_experiment_invalid_name(self, tmp_path: Path) -> None:
        """Test that invalid experiment names are rejected."""
        from scripts.utils import validate_experiment_name
        import argparse

        with pytest.raises(argparse.ArgumentTypeError):
            validate_experiment_name("invalid/name/with/slashes")

    def test_show_experiment_no_intent(self, tmp_path: Path, caplog) -> None:
        """Test showing experiment without intent.yaml."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        exp_dir = workspace / "test-exp"
        exp_dir.mkdir()
        (exp_dir / "logs").mkdir()
        (exp_dir / "findings").mkdir()

        with patch("scripts.show_exp.BASE_DIR", tmp_path):
            with patch("scripts.show_exp.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0, stdout="expl/test-exp\n"
                )
                result = show_experiment("test-exp")
                assert result == 0

    def test_show_experiment_no_metrics(self, tmp_path: Path, caplog) -> None:
        """Test showing experiment without metrics."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        exp_dir = workspace / "test-exp"
        exp_dir.mkdir()
        (exp_dir / "logs").mkdir()
        (exp_dir / "findings").mkdir()

        # Create intent.yaml
        intent_path = exp_dir / "intent.yaml"
        intent_path.write_text("""experiment: test-exp
branch: expl/test-exp
objective: |
  Test objective.
""")

        with patch("scripts.show_exp.BASE_DIR", tmp_path):
            result = show_experiment("test-exp")
            assert result == 0

    def test_show_experiment_git_not_found(self, tmp_path: Path, caplog) -> None:
        """Test showing experiment when git is not available."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        exp_dir = workspace / "test-exp"
        exp_dir.mkdir()
        (exp_dir / "logs").mkdir()
        (exp_dir / "findings").mkdir()

        with patch("scripts.show_exp.BASE_DIR", tmp_path):
            with patch("scripts.show_exp.subprocess.run") as mock_run:
                mock_run.side_effect = FileNotFoundError()
                result = show_experiment("test-exp")
                assert result == 0

    def test_show_experiment_git_error(self, tmp_path: Path, caplog) -> None:
        """Test showing experiment when git command fails."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        exp_dir = workspace / "test-exp"
        exp_dir.mkdir()
        (exp_dir / "logs").mkdir()
        (exp_dir / "findings").mkdir()

        with patch("scripts.show_exp.BASE_DIR", tmp_path):
            with patch("scripts.show_exp.subprocess.run") as mock_run:
                mock_run.side_effect = subprocess.CalledProcessError(
                    1, "git", stderr="fatal: not a git repository"
                )
                result = show_experiment("test-exp")
                assert result == 0
