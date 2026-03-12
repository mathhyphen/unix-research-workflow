#!/usr/bin/env python3
"""Tests for LogHook class."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from scripts.log_hook import LogHook


class TestLogHook:
    """Test suite for LogHook class."""

    def test_log_hook_creates_logs_directory(self, tmp_path: Path) -> None:
        """Test that LogHook creates the logs directory."""
        log = LogHook(tmp_path)

        logs_dir = tmp_path / "logs"
        assert logs_dir.exists()
        assert logs_dir.is_dir()

    def test_log_hook_creates_metrics_jsonl(self, tmp_path: Path) -> None:
        """Test that LogHook creates metrics.jsonl file on first log."""
        log = LogHook(tmp_path)
        log.log({"test": 1.0})

        metrics_file = tmp_path / "logs" / "metrics.jsonl"
        assert metrics_file.exists()

    def test_log_adds_timestamp(self, tmp_path: Path) -> None:
        """Test that log() adds _timestamp field automatically."""
        log = LogHook(tmp_path)
        log.log({"metric": 0.5})

        metrics_file = tmp_path / "logs" / "metrics.jsonl"
        with open(metrics_file, "r") as f:
            data = json.loads(f.readline())

        assert "_timestamp" in data
        # Verify timestamp is valid ISO format
        datetime.fromisoformat(data["_timestamp"])

    def test_log_preserves_data(self, tmp_path: Path) -> None:
        """Test that log() preserves original data."""
        log = LogHook(tmp_path)
        log.log({"loss": 0.5, "accuracy": 0.95})

        metrics_file = tmp_path / "logs" / "metrics.jsonl"
        with open(metrics_file, "r") as f:
            data = json.loads(f.readline())

        assert data["loss"] == 0.5
        assert data["accuracy"] == 0.95

    def test_log_appends_multiple_entries(self, tmp_path: Path) -> None:
        """Test that multiple log calls append to file."""
        log = LogHook(tmp_path)
        log.log({"epoch": 1, "loss": 1.0})
        log.log({"epoch": 2, "loss": 0.5})
        log.log({"epoch": 3, "loss": 0.25})

        metrics_file = tmp_path / "logs" / "metrics.jsonl"
        with open(metrics_file, "r") as f:
            lines = f.readlines()

        assert len(lines) == 3

    def test_log_environment_records_system_info(self, tmp_path: Path) -> None:
        """Test that log_environment() records system information."""
        import platform
        import sys

        log = LogHook(tmp_path)
        log.log_environment()

        metrics_file = tmp_path / "logs" / "metrics.jsonl"
        with open(metrics_file, "r") as f:
            data = json.loads(f.readline())

        assert data["type"] == "environment"
        assert data["python_version"] == sys.version.split()[0]
        assert data["platform"] == platform.platform()
        assert "hostname" in data
        assert "_timestamp" in data

    def test_log_epoch_formats_correctly(self, tmp_path: Path) -> None:
        """Test that log_epoch() formats metrics with epoch and phase."""
        log = LogHook(tmp_path)
        log.log_epoch(epoch=1, metrics={"loss": 0.5, "accuracy": 0.9})

        metrics_file = tmp_path / "logs" / "metrics.jsonl"
        with open(metrics_file, "r") as f:
            data = json.loads(f.readline())

        assert data["epoch"] == 1
        assert data["phase"] == "train"  # default phase
        assert data["loss"] == 0.5
        assert data["accuracy"] == 0.9
        assert "_timestamp" in data

    def test_log_epoch_with_custom_phase(self, tmp_path: Path) -> None:
        """Test that log_epoch() accepts custom phase."""
        log = LogHook(tmp_path)
        log.log_epoch(epoch=5, metrics={"val_loss": 0.3}, phase="val")

        metrics_file = tmp_path / "logs" / "metrics.jsonl"
        with open(metrics_file, "r") as f:
            data = json.loads(f.readline())

        assert data["epoch"] == 5
        assert data["phase"] == "val"
        assert data["val_loss"] == 0.3

    def test_log_epoch_with_test_phase(self, tmp_path: Path) -> None:
        """Test that log_epoch() accepts test phase."""
        log = LogHook(tmp_path)
        log.log_epoch(epoch=10, metrics={"test_accuracy": 0.92}, phase="test")

        metrics_file = tmp_path / "logs" / "metrics.jsonl"
        with open(metrics_file, "r") as f:
            data = json.loads(f.readline())

        assert data["phase"] == "test"

    def test_log_handles_nested_dict(self, tmp_path: Path) -> None:
        """Test that log() can handle nested dictionaries."""
        log = LogHook(tmp_path)
        log.log({"model": {"layers": 3, "hidden_dim": 128}})

        metrics_file = tmp_path / "logs" / "metrics.jsonl"
        with open(metrics_file, "r") as f:
            data = json.loads(f.readline())

        assert data["model"]["layers"] == 3
        assert data["model"]["hidden_dim"] == 128