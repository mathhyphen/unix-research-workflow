"""Tests for log_hook module."""

import json
import tempfile
from pathlib import Path

from scripts.log_hook import LogHook


class TestLogHook:
    """Test cases for LogHook class."""

    def test_init_creates_log_dir(self) -> None:
        """Test that LogHook creates the log directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            log = LogHook(workspace)
            assert log.log_dir.exists()
            assert log.log_file.exists() is False  # Not created until first log

    def test_log_single_metric(self) -> None:
        """Test logging a single metric."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            log = LogHook(workspace)
            log.log({"loss": 0.5})

            content = log.log_file.read_text()
            lines = content.strip().split("\n")
            assert len(lines) == 1
            data = json.loads(lines[0])
            assert "loss" in data
            assert data["loss"] == 0.5
            assert "_timestamp" in data

    def test_log_multiple_metrics(self) -> None:
        """Test logging multiple metrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            log = LogHook(workspace)
            log.log({"loss": 0.5, "accuracy": 0.8})
            log.log({"loss": 0.3, "accuracy": 0.9})

            content = log.log_file.read_text()
            lines = content.strip().split("\n")
            assert len(lines) == 2

    def test_log_epoch(self) -> None:
        """Test logging epoch metrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            log = LogHook(workspace)
            log.log_epoch(0, {"loss": 0.5}, phase="train")

            content = log.log_file.read_text()
            data = json.loads(content.strip())
            assert data["epoch"] == 0
            assert data["phase"] == "train"
            assert data["loss"] == 0.5

    def test_log_environment(self) -> None:
        """Test logging environment info."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            log = LogHook(workspace)
            log.log_environment()

            content = log.log_file.read_text()
            data = json.loads(content.strip())
            assert data["type"] == "environment"
            assert "python_version" in data
            assert "platform" in data

    def test_log_with_nested_metrics(self) -> None:
        """Test logging with nested metrics structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            log = LogHook(workspace)
            log.log({"epoch": 0, "metrics": {"loss": 0.5, "dice": 0.7}})

            content = log.log_file.read_text()
            data = json.loads(content.strip())
            assert "metrics" in data
            assert data["metrics"]["loss"] == 0.5

    def test_log_does_not_mutate_input(self) -> None:
        """Test that logging does not mutate the caller payload."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            log = LogHook(workspace)
            payload = {"loss": 0.5}

            log.log(payload)

            assert "_timestamp" not in payload
