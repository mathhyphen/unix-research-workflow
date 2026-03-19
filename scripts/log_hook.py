#!/usr/bin/env python3
"""Log hook for recording experiment metrics in JSONL format."""

import json
import platform
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


class LogHook:
    """Hook for logging experiment metrics to JSONL format.

    Attributes:
        workspace_path: Path to the experiment workspace.
        log_dir: Directory for log files.
        log_file: Path to the metrics.jsonl file.
    """

    def __init__(self, workspace_path: Path) -> None:
        """Initialize the log hook.

        Args:
            workspace_path: Path to the experiment workspace directory.
        """
        self.workspace_path = workspace_path
        self.log_dir = workspace_path / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "metrics.jsonl"

    def log(self, data: Dict[str, Any]) -> None:
        """Log a metric data point.

        Args:
            data: Dictionary of metrics to log. A timestamp is added automatically.
        """
        payload = dict(data)
        payload["_timestamp"] = datetime.now().isoformat()
        with open(self.log_file, "a") as f:
            f.write(json.dumps(payload) + "\n")

    def log_environment(self) -> None:
        """Log environment information (system, Python, etc.)."""
        env_data = {
            "type": "environment",
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
            "hostname": platform.node(),
        }
        self.log(env_data)

    def log_epoch(
        self,
        epoch: int,
        metrics: Dict[str, float],
        phase: str = "train"
    ) -> None:
        """Log epoch-level metrics.

        Args:
            epoch: Current epoch number.
            metrics: Dictionary of metric name -> value.
            phase: Training phase (train/val/test).
        """
        data = {"epoch": epoch, "phase": phase, **metrics}
        self.log(data)
