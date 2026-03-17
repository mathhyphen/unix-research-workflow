#!/usr/bin/env python3
"""List all research experiments with their current status."""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from enum import Enum

from scripts.utils import get_workspace_paths

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    """Configure logging for the script."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        stream=sys.stderr,
    )

BASE_DIR = Path(__file__).resolve().parent.parent


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="List all research experiments with their status"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)"
    )
    parser.add_argument(
        "--version", "-V",
        action="version",
        version="%(prog)s 1.0.0"
    )
    return parser.parse_args()


class ExperimentStatus(Enum):
    """Experiment lifecycle status codes."""
    INITIALIZED = "I"
    HAS_METRICS = "M"
    REPORT_READY = "R"


def determine_experiment_status(exp_path: Path) -> ExperimentStatus:
    """Determine experiment status based on available files.

    Args:
        exp_path: Path to experiment directory.

    Returns:
        ExperimentStatus enum value.
    """
    logs_path = exp_path / "logs"
    findings_path = exp_path / "findings"

    if (findings_path / "report.md").exists():
        return ExperimentStatus.REPORT_READY
    if (logs_path / "metrics.jsonl").exists():
        return ExperimentStatus.HAS_METRICS
    return ExperimentStatus.INITIALIZED


def list_experiments() -> List[Tuple[str, ExperimentStatus, str]]:
    """List all experiments in workspace.

    Returns:
        List of tuples (experiment_name, status, source_path).
    """
    workspaces = get_workspace_paths()
    experiments = []
    seen_names = set()

    for workspace in workspaces:
        if not workspace.exists():
            continue
        for exp_dir in sorted(workspace.iterdir()):
            if not exp_dir.is_dir():
                continue
            if exp_dir.name in seen_names:
                continue
            seen_names.add(exp_dir.name)
            status = determine_experiment_status(exp_dir)
            experiments.append((exp_dir.name, status, str(exp_dir)))

    return experiments


def print_experiments(experiments: List[Tuple[str, ExperimentStatus, str]], output_format: str = "table") -> None:
    """Print formatted experiment list.

    Args:
        experiments: List of (name, status, path) tuples.
        output_format: Output format ("table" or "json").
    """
    if not experiments:
        print("No experiments found in workspace.")
        print("\nTo create your first experiment:")
        print("  python scripts/new_exp.py --name my-first-experiment")
        return

    if output_format == "json":
        import json
        data = [{"name": name, "status": status.value, "path": path} for name, status, path in experiments]
        print(json.dumps(data, indent=2))
    else:
        print(f"{'Experiment':<25} | {'Status':<10}")
        print("-" * 38)
        for name, status, path in experiments:
            print(f"{name:<25} | {status.value:<10}")


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    configure_logging()

    if sys.version_info < (3, 9):
        logger.error("Error: Python 3.9 or later is required")
        return 1

    args = parse_args()
    experiments = list_experiments()
    print_experiments(experiments, args.format)
    return 0


if __name__ == "__main__":
    sys.exit(main())
