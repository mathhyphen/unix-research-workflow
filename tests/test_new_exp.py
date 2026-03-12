#!/usr/bin/env python3
"""Tests for new_exp module."""

import shutil
import subprocess
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

from scripts.new_exp import copy_intent_template, create_experiment


class TestCreateExperiment:
    """Test suite for create_experiment function."""

    @pytest.fixture
    def mock_base_dir(self, tmp_path: Path) -> Path:
        """Create a mock base directory structure."""
        base = tmp_path / "workflow"
        base.mkdir()
        (base / "templates").mkdir()
        (base / "workspace").mkdir()

        # Create intent template
        intent_template = base / "templates" / "intent.yaml"
        intent_template.write_text("""experiment: <name>
branch: expl/<name>
objective: |
  Describe what you want to achieve (min 20 chars).
hypothesis: |
  Describe what you expect to happen (min 20 chars).
""")
        return base

    def test_create_experiment_creates_directory_structure(
        self, mock_base_dir: Path
    ) -> None:
        """Test that create_experiment creates proper directory structure."""
        with patch("scripts.new_exp.BASE_DIR", mock_base_dir):
            exp_path = create_experiment("test-exp")

            assert exp_path is not None
            assert exp_path.exists()
            assert (exp_path / "logs").exists()
            assert (exp_path / "findings").exists()

    def test_create_experiment_creates_intent_file(
        self, mock_base_dir: Path
    ) -> None:
        """Test that create_experiment creates intent.yaml with correct name."""
        with patch("scripts.new_exp.BASE_DIR", mock_base_dir):
            exp_path = create_experiment("my-experiment")

            intent_file = exp_path / "intent.yaml"
            assert intent_file.exists()

            content = intent_file.read_text()
            assert "experiment: my-experiment" in content
            assert "branch: expl/my-experiment" in content

    def test_create_experiment_handles_existing_experiment(
        self, mock_base_dir: Path
    ) -> None:
        """Test that create_experiment exits when experiment already exists."""
        # Create existing experiment
        existing_exp = mock_base_dir / "workspace" / "existing-exp"
        existing_exp.mkdir()

        with patch("scripts.new_exp.BASE_DIR", mock_base_dir):
            with pytest.raises(SystemExit) as exc_info:
                create_experiment("existing-exp")

            assert exc_info.value.code == 1

    def test_create_experiment_returns_correct_path(
        self, mock_base_dir: Path
    ) -> None:
        """Test that create_experiment returns the correct path."""
        with patch("scripts.new_exp.BASE_DIR", mock_base_dir):
            exp_path = create_experiment("new-exp")

            expected_path = mock_base_dir / "workspace" / "new-exp"
            assert exp_path == expected_path

    def test_create_experiment_with_git_worktree(
        self, mock_base_dir: Path
    ) -> None:
        """Test that create_experiment attempts to create git worktree."""
        with patch("scripts.new_exp.BASE_DIR", mock_base_dir):
            with patch("scripts.new_exp.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                create_experiment("git-exp")

                # Verify git worktree command was called
                mock_run.assert_called()
                call_args = mock_run.call_args
                assert "worktree" in call_args[0][0]
                assert "expl/git-exp" in str(call_args)

    def test_create_experiment_handles_git_failure(
        self, mock_base_dir: Path
    ) -> None:
        """Test that create_experiment handles git worktree failure gracefully."""
        with patch("scripts.new_exp.BASE_DIR", mock_base_dir):
            with patch("scripts.new_exp.subprocess.run") as mock_run:
                # Simulate git failure
                mock_run.side_effect = subprocess.CalledProcessError(
                    1, "git", stderr="fatal: already exists"
                )
                # Should not raise, just log warning
                exp_path = create_experiment("git-fail-exp")

                # Directory should still be created
                assert exp_path.exists()

    def test_create_experiment_handles_no_git(
        self, mock_base_dir: Path
    ) -> None:
        """Test that create_experiment handles missing git gracefully."""
        with patch("scripts.new_exp.BASE_DIR", mock_base_dir):
            with patch("scripts.new_exp.subprocess.run") as mock_run:
                # Simulate git not found
                mock_run.side_effect = FileNotFoundError()
                # Should not raise
                exp_path = create_experiment("no-git-exp")

                assert exp_path.exists()


class TestCopyIntentTemplate:
    """Test suite for copy_intent_template function."""

    @pytest.fixture
    def mock_base_dir(self, tmp_path: Path) -> Path:
        """Create a mock base directory with template."""
        base = tmp_path / "workflow"
        base.mkdir()
        (base / "templates").mkdir()

        intent_template = base / "templates" / "intent.yaml"
        intent_template.write_text("""experiment: <name>
branch: expl/<name>
objective: |
  Test objective.
""")
        return base

    def test_copy_intent_template_creates_file(
        self, mock_base_dir: Path
    ) -> None:
        """Test that copy_intent_template creates intent.yaml."""
        exp_dir = mock_base_dir / "workspace" / "test-exp"
        exp_dir.mkdir(parents=True)

        with patch("scripts.new_exp.BASE_DIR", mock_base_dir):
            copy_intent_template(exp_dir, "test-exp")

            intent_file = exp_dir / "intent.yaml"
            assert intent_file.exists()

    def test_copy_intent_template_substitutes_name(
        self, mock_base_dir: Path
    ) -> None:
        """Test that copy_intent_template substitutes experiment name."""
        exp_dir = mock_base_dir / "workspace" / "my-exp"
        exp_dir.mkdir(parents=True)

        with patch("scripts.new_exp.BASE_DIR", mock_base_dir):
            copy_intent_template(exp_dir, "my-exp")

            content = (exp_dir / "intent.yaml").read_text()
            assert "experiment: my-exp" in content
            assert "branch: expl/my-exp" in content
            assert "<name>" not in content


class TestCreateExperimentNames:
    """Test various experiment name formats."""

    @pytest.fixture
    def mock_base_dir(self, tmp_path: Path) -> Path:
        """Create a mock base directory structure."""
        base = tmp_path / "workflow"
        base.mkdir()
        (base / "templates").mkdir()
        (base / "workspace").mkdir()

        intent_template = base / "templates" / "intent.yaml"
        intent_template.write_text("""experiment: <name>
branch: expl/<name>
objective: |
  Test objective for experiment.
hypothesis: |
  Test hypothesis for experiment.
""")
        return base

    def test_simple_name(self, mock_base_dir: Path) -> None:
        """Test simple alphanumeric name."""
        with patch("scripts.new_exp.BASE_DIR", mock_base_dir):
            exp_path = create_experiment("experiment1")
            assert exp_path.name == "experiment1"

    def test_name_with_hyphens(self, mock_base_dir: Path) -> None:
        """Test name with hyphens."""
        with patch("scripts.new_exp.BASE_DIR", mock_base_dir):
            exp_path = create_experiment("my-ablation-study")
            assert exp_path.name == "my-ablation-study"

    def test_name_with_underscores(self, mock_base_dir: Path) -> None:
        """Test name with underscores."""
        with patch("scripts.new_exp.BASE_DIR", mock_base_dir):
            exp_path = create_experiment("exp_v2_final")
            assert exp_path.name == "exp_v2_final"