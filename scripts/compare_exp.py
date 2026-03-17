#!/usr/bin/env python3
"""Compare metrics across multiple experiments."""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from scripts.utils import safe_path, validate_experiment_name, format_error, get_workspace_paths

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    """Configure logging for the script."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        stream=sys.stderr,
    )


def find_experiment(name: str) -> Optional[Path]:
    """Find experiment directory across all workspaces.

    Args:
        name: Experiment name.

    Returns:
        Path to experiment directory, or None if not found.
    """
    for workspace in get_workspace_paths():
        if not workspace.exists():
            continue
        exp_dir = safe_path(workspace, name)
        if exp_dir.exists():
            return exp_dir
    return None


def load_final_metrics(metrics_path: Path) -> Optional[Dict[str, Any]]:
    """Load the last non-environment metric entry and flatten nested metrics."""
    if not metrics_path.exists():
        return None

    last_metric = None
    with open(metrics_path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                metric = json.loads(line)
                if metric.get("type") != "environment":
                    last_metric = metric

    if last_metric is None:
        return None

    # Flatten nested metrics structure from log_hook
    result = {}
    if "metrics" in last_metric and isinstance(last_metric["metrics"], dict):
        result.update(last_metric["metrics"])
    # Also include top-level keys (except nested metrics dict)
    for key, value in last_metric.items():
        if key != "metrics":
            result[key] = value

    return result


def compare_experiments(names: List[str], metric_key: str) -> int:
    """Compare a specific metric across experiments.

    Args:
        names: List of experiment names.
        metric_key: The metric key to compare (e.g., 'val_loss').

    Returns:
        Exit code (0 for success, 1 if validation fails, 2 if no comparable data).
    """
    # Validate all experiment names first, fail fast on invalid names
    validated_names: List[str] = []
    for name in names:
        try:
            validate_experiment_name(name)
            validated_names.append(name)
        except argparse.ArgumentTypeError as e:
            logger.error(format_error(
                f"Invalid experiment name '{name}'",
                str(e)
            ))
            return 1

    results: List[Dict[str, Any]] = []
    for name in validated_names:
        exp_dir = find_experiment(name)
        if exp_dir is None:
            logger.warning(f"Warning: Experiment '{name}' not found")
            continue
        metrics_path = exp_dir / "logs" / "metrics.jsonl"
        metric = load_final_metrics(metrics_path)

        if metric is None:
            logger.warning(f"Warning: No metrics found for '{name}'")
            continue

        value = metric.get(metric_key)
        if value is None:
            logger.warning(f"Warning: No '{metric_key}' found for '{name}'")
            continue

        results.append({
            "name": name,
            "value": value,
            "full_metric": metric,
        })

    if not results:
        logger.error(format_error(
            "No comparable data found.",
            "Check experiment names and ensure metrics have been logged"
        ))
        return 2

    # Sort by value (lower is better for most metrics)
    results.sort(key=lambda x: x["value"] if isinstance(x["value"], (int, float)) else 0)

    # Print comparison table
    print(f"\nComparison by '{metric_key}' (sorted best to worst):\n")
    print(f"{'Rank':<6} | {'Experiment':<25} | {'Value':<15}")
    print("-" * 52)

    for i, result in enumerate(results, 1):
        marker = " *" if i == 1 else ""
        print(f"{i:<6} | {result['name']:<25} | {result['value']:.4f}{marker}")

    print()
    return 0


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Compare metrics across multiple experiments"
    )
    parser.add_argument(
        "names",
        nargs="+",
        help="Experiment names to compare"
    )
    parser.add_argument(
        "--metric", "-m",
        default="val_loss",
        help="Metric key to compare (default: val_loss)"
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
    return compare_experiments(args.names, args.metric)


if __name__ == "__main__":
    sys.exit(main())
