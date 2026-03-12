#!/usr/bin/env python3
"""Export experiment metrics to CSV format."""

import argparse
import csv
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

from scripts.utils import safe_path, validate_experiment_name, format_error

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    """Configure logging for the script."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        stream=sys.stderr,
    )

BASE_DIR = Path(__file__).resolve().parent.parent


def load_metrics(metrics_path: Path) -> List[Dict[str, Any]]:
    """Load metrics from JSONL file."""
    metrics = []
    with open(metrics_path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                metrics.append(json.loads(line))
    return metrics


def export_to_csv(name: str, output_path: Path) -> Path:
    """Export experiment metrics to CSV.

    Args:
        name: Experiment name.
        output_path: Output CSV file path.

    Returns:
        Path to exported CSV file.
    """
    workspace = BASE_DIR / "workspace"
    exp_dir = safe_path(workspace, name)
    metrics_path = exp_dir / "logs" / "metrics.jsonl"

    if not metrics_path.exists():
        raise FileNotFoundError(f"No metrics found for '{name}'")

    metrics = load_metrics(metrics_path)

    if not metrics:
        raise ValueError("No data in metrics file")

    # Collect all keys
    all_keys = set()
    for metric in metrics:
        all_keys.update(metric.keys())

    # Sort keys, put _timestamp first
    keys = sorted(all_keys - {"_timestamp"})
    if "_timestamp" in all_keys:
        keys = ["_timestamp"] + keys

    # Write CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        for metric in metrics:
            writer.writerow(metric)

    print(f"Exported {len(metrics)} rows to {output_path}")
    return output_path


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Export experiment metrics to CSV"
    )
    parser.add_argument(
        "name",
        type=validate_experiment_name,
        help="Experiment name"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Output CSV file path (default: workspace/<name>/metrics.csv)"
    )
    parser.add_argument(
        "--version", "-V",
        action="version",
        version="%(prog)s 1.0.0"
    )
    return parser.parse_args()


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

    workspace = BASE_DIR / "workspace"
    output_path = args.output or (workspace / args.name / "metrics.csv")

    # Validate that output path is within allowed directories using safe_path
    try:
        # If user provided custom path, validate it's safe
        if args.output:
            # Use safe_path for consistent validation
            safe_path(workspace, str(output_path.relative_to(workspace)))
        # output_path is within workspace, proceed
    except (ValueError, TypeError):
        # Path might be outside workspace, reject it
        logger.error(format_error(
            f"Output path '{output_path}' is outside workspace",
            "Use a path within the workspace directory or omit --output for default"
        ))
        return 1

    try:
        export_to_csv(args.name, output_path)
    except (FileNotFoundError, ValueError) as e:
        logger.error(format_error(str(e)))
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
