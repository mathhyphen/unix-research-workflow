#!/usr/bin/env python3
"""Tests for list_exp module."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.list_exp import (
    determine_experiment_status,
    get_workspace_path,
    list_experiments,
    print_experiments,
    ExperimentStatus,
)


class TestDetermineExperimentStatus:
    """Test suite for determine_experiment_status function."""

    def test_determine_experiment_status_I(self, tmp_path: Path) -> None:
        """Test status is INITIALIZED when only directories exist."""
        exp_dir = tmp_path / "test-exp"
        exp_dir.mkdir()
        (exp_dir / "logs").mkdir()
        (exp_dir / "findings").mkdir()

        status = determine_experiment_status(exp_dir)
        assert status == ExperimentStatus.INITIALIZED

    def test_determine_experiment_status_M(self, tmp_path: Path) -> None:
        """Test status is HAS_METRICS when metrics.jsonl exists."""
        exp_dir = tmp_path / "test-exp"
        exp_dir.mkdir()
        logs_dir = exp_dir / "logs"
        logs_dir.mkdir(parents=True)
        (logs_dir / "metrics.jsonl").write_text('{"test": 1}\n')

        status = determine_experiment_status(exp_dir)
        assert status == ExperimentStatus.HAS_METRICS

    def test_determine_experiment_status_R(self, tmp_path: Path) -> None:
        """Test status is REPORT_READY when report.md exists."""
        exp_dir = tmp_path / "test-exp"
        exp_dir.mkdir()
        findings_dir = exp_dir / "findings"
        findings_dir.mkdir(parents=True)
        (findings_dir / "report.md").write_text("# Report")

        status = determine_experiment_status(exp_dir)
        assert status == ExperimentStatus.REPORT_READY

    def test_determine_experiment_status_R_overrides_M(self, tmp_path: Path) -> None:
        """Test that REPORT_READY takes precedence over HAS_METRICS."""
        exp_dir = tmp_path / "test-exp"
        exp_dir.mkdir()
        logs_dir = exp_dir / "logs"
        logs_dir.mkdir(parents=True)
        findings_dir = exp_dir / "findings"
        findings_dir.mkdir(parents=True)
        (logs_dir / "metrics.jsonl").write_text('{"test": 1}\n')
        (findings_dir / "report.md").write_text("# Report")

        status = determine_experiment_status(exp_dir)
        assert status == ExperimentStatus.REPORT_READY


class TestListExperiments:
    """Test suite for list_experiments function."""

    def test_list_experiments_empty_workspace(self, tmp_path: Path) -> None:
        """Test listing experiments in empty workspace."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        with patch("scripts.list_exp.get_workspace_path", return_value=workspace):
            experiments = list_experiments()
            assert experiments == []

    def test_list_experiments_with_initialized_experiment(self, tmp_path: Path) -> None:
        """Test listing initialized experiments."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        exp_dir = workspace / "test-exp"
        exp_dir.mkdir()
        (exp_dir / "logs").mkdir()
        (exp_dir / "findings").mkdir()

        with patch("scripts.list_exp.get_workspace_path", return_value=workspace):
            experiments = list_experiments()
            assert len(experiments) == 1
            assert experiments[0][0] == "test-exp"
            assert experiments[0][1] == ExperimentStatus.INITIALIZED

    def test_list_experiments_with_metrics(self, tmp_path: Path) -> None:
        """Test listing experiments with metrics."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        exp_dir = workspace / "test-exp"
        exp_dir.mkdir()
        logs_dir = exp_dir / "logs"
        logs_dir.mkdir(parents=True)
        (logs_dir / "metrics.jsonl").write_text('{"accuracy": 0.95}\n')

        with patch("scripts.list_exp.get_workspace_path", return_value=workspace):
            experiments = list_experiments()
            assert len(experiments) == 1
            assert experiments[0][0] == "test-exp"
            assert experiments[0][1] == ExperimentStatus.HAS_METRICS

    def test_list_experiments_with_report(self, tmp_path: Path) -> None:
        """Test listing experiments with reports."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        exp_dir = workspace / "test-exp"
        exp_dir.mkdir()
        findings_dir = exp_dir / "findings"
        findings_dir.mkdir(parents=True)
        (findings_dir / "report.md").write_text("# Experiment Report")

        with patch("scripts.list_exp.get_workspace_path", return_value=workspace):
            experiments = list_experiments()
            assert len(experiments) == 1
            assert experiments[0][0] == "test-exp"
            assert experiments[0][1] == ExperimentStatus.REPORT_READY

    def test_list_experiments_multiple(self, tmp_path: Path) -> None:
        """Test listing multiple experiments sorted alphabetically."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        # Create experiments in non-alphabetical order
        for name in ["z-exp", "a-exp", "m-exp"]:
            exp_dir = workspace / name
            exp_dir.mkdir()

        with patch("scripts.list_exp.get_workspace_path", return_value=workspace):
            experiments = list_experiments()
            assert len(experiments) == 3
            # Should be sorted alphabetically
            assert experiments[0][0] == "a-exp"
            assert experiments[1][0] == "m-exp"
            assert experiments[2][0] == "z-exp"

    def test_list_experiments_ignores_files(self, tmp_path: Path) -> None:
        """Test that files in workspace are ignored."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        (workspace / "some-file.txt").write_text("test")

        with patch("scripts.list_exp.get_workspace_path", return_value=workspace):
            experiments = list_experiments()
            assert experiments == []


class TestPrintExperiments:
    """Test suite for print_experiments function."""

    def test_print_experiments_empty(self, capsys) -> None:
        """Test printing empty experiment list."""
        print_experiments([])
        captured = capsys.readouterr()
        assert "No experiments found" in captured.out

    def test_print_experiments_format(self, capsys) -> None:
        """Test printing experiments with proper formatting."""
        experiments = [
            ("exp-1", ExperimentStatus.INITIALIZED),
            ("exp-2", ExperimentStatus.HAS_METRICS),
            ("exp-3", ExperimentStatus.REPORT_READY),
        ]
        print_experiments(experiments)
        captured = capsys.readouterr()

        assert "Experiment" in captured.out
        assert "Status" in captured.out
        assert "exp-1" in captured.out
        assert "exp-2" in captured.out
        assert "exp-3" in captured.out
        assert "I" in captured.out
        assert "M" in captured.out
        assert "R" in captured.out


class TestGetWorkspacePath:
    """Test suite for get_workspace_path function."""

    def test_get_workspace_path_returns_path(self) -> None:
        """Test that get_workspace_path returns a Path."""
        path = get_workspace_path()
        assert isinstance(path, Path)
        assert path.name == "workspace"
