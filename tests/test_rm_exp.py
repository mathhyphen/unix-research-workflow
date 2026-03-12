#!/usr/bin/env python3
"""Tests for rm_exp module."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.rm_exp import remove_experiment


class TestRemoveExperiment:
    """Test suite for remove_experiment function."""

    def test_remove_experiment_success(self, tmp_path: Path) -> None:
        """Test successful removal of experiment."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        exp_dir = workspace / "test-exp"
        exp_dir.mkdir()
        (exp_dir / "logs").mkdir()

        with patch("scripts.rm_exp.BASE_DIR", tmp_path):
            with patch("scripts.rm_exp.Path") as mock_path:
                # Mock BASE_DIR / "workspace" to return our workspace
                def mock_path_constructor(*args, **kwargs):
                    if args == (tmp_path, "workspace"):
                        return workspace
                    return Path(*args, **kwargs)
                mock_path.side_effect = mock_path_constructor
                mock_path.__truediv__ = lambda self, other: workspace if other == "workspace" else Path(self) / other

                result = remove_experiment("test-exp")
                assert result is True
                assert not exp_dir.exists()

    def test_remove_experiment_not_found(self, tmp_path: Path) -> None:
        """Test removal of non-existent experiment."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        with patch("scripts.rm_exp.BASE_DIR", tmp_path):
            with patch("scripts.rm_exp.Path") as mock_path:
                def mock_path_constructor(*args, **kwargs):
                    if args == (tmp_path, "workspace"):
                        return workspace
                    return Path(*args, **kwargs)
                mock_path.side_effect = mock_path_constructor

                result = remove_experiment("non-existent")
                assert result is False

    def test_remove_experiment_with_report_requires_force(self, tmp_path: Path) -> None:
        """Test that experiment with report requires --force to remove."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        exp_dir = workspace / "test-exp"
        exp_dir.mkdir()
        findings_dir = exp_dir / "findings"
        findings_dir.mkdir(parents=True)
        (findings_dir / "report.md").write_text("# Report")

        with patch("scripts.rm_exp.BASE_DIR", tmp_path):
            result = remove_experiment("test-exp", force=False)
            assert result is False
            assert exp_dir.exists()  # Should not be removed

    def test_remove_experiment_with_force_success(self, tmp_path: Path) -> None:
        """Test forced removal of experiment with report."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        exp_dir = workspace / "test-exp"
        exp_dir.mkdir()
        findings_dir = exp_dir / "findings"
        findings_dir.mkdir(parents=True)
        (findings_dir / "report.md").write_text("# Report")

        with patch("scripts.rm_exp.BASE_DIR", tmp_path):
            result = remove_experiment("test-exp", force=True)
            assert result is True
            assert not exp_dir.exists()

    def test_remove_experiment_path_traversal_blocked(self, tmp_path: Path) -> None:
        """Test that path traversal attempts are blocked."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        # Create a directory outside workspace
        other_dir = tmp_path / "other"
        other_dir.mkdir()

        with patch("scripts.rm_exp.BASE_DIR", tmp_path):
            # Path traversal should raise ValueError from safe_path
            with pytest.raises(ValueError, match="Path traversal detected"):
                remove_experiment("../other")

    def test_remove_experiment_invalid_name(self, tmp_path: Path) -> None:
        """Test that invalid experiment names are rejected."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        with patch("scripts.rm_exp.BASE_DIR", tmp_path):
            # Invalid names should fail validation
            from scripts.utils import validate_experiment_name
            import argparse

            with pytest.raises(argparse.ArgumentTypeError):
                validate_experiment_name("invalid/name")

    def test_remove_experiment_removes_git_worktree(self, tmp_path: Path) -> None:
        """Test that git worktree is removed if present."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        exp_dir = workspace / "test-exp"
        exp_dir.mkdir()
        (exp_dir / ".git").mkdir()

        with patch("scripts.rm_exp.BASE_DIR", tmp_path):
            with patch("scripts.rm_exp.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                result = remove_experiment("test-exp")
                assert result is True

                # Verify git worktree remove was called
                mock_run.assert_called_once()
                call_args = mock_run.call_args[0][0]
                assert "worktree" in call_args
                assert "remove" in call_args

    def test_remove_experiment_handles_git_failure(self, tmp_path: Path) -> None:
        """Test that git failure doesn't prevent removal."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        exp_dir = workspace / "test-exp"
        exp_dir.mkdir()
        (exp_dir / ".git").mkdir()

        with patch("scripts.rm_exp.BASE_DIR", tmp_path):
            with patch("scripts.rm_exp.subprocess.run") as mock_run:
                mock_run.side_effect = subprocess.CalledProcessError(
                    1, "git", stderr="fatal: not a git repository"
                )
                result = remove_experiment("test-exp")
                assert result is True
                assert not exp_dir.exists()

    def test_remove_experiment_handles_no_git(self, tmp_path: Path) -> None:
        """Test that missing git doesn't prevent removal."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        exp_dir = workspace / "test-exp"
        exp_dir.mkdir()
        (exp_dir / ".git").mkdir()

        with patch("scripts.rm_exp.BASE_DIR", tmp_path):
            with patch("scripts.rm_exp.subprocess.run") as mock_run:
                mock_run.side_effect = FileNotFoundError()
                result = remove_experiment("test-exp")
                assert result is True
                assert not exp_dir.exists()
