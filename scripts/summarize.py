#!/usr/bin/env python3
"""Generate summary reports from experiment metrics with multiple format support."""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from scripts.report_factory import ReportFactory
from scripts.utils import (
    find_experiment_path,
    format_error,
    validate_experiment_name,
)

logger = logging.getLogger(__name__)
CONTROL_KEYS = {"_timestamp", "epoch", "metrics", "phase", "seed", "step", "type"}


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
    return find_experiment_path(name)


def load_metrics(metrics_path: Path) -> List[Dict[str, Any]]:
    """Load metrics from JSONL file.

    Args:
        metrics_path: Path to metrics.jsonl file.

    Returns:
        List of metric dictionaries.

    Raises:
        json.JSONDecodeError: If a line contains invalid JSON.
    """
    metrics: List[Dict[str, Any]] = []
    with open(metrics_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line:
                try:
                    metrics.append(json.loads(line))
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping invalid JSON on line {line_num}: {e}")
    return metrics


def compute_summary(metrics: List[Dict[str, Any]]) -> Dict[str, float]:
    """Compute summary statistics for each metric key.

    Args:
        metrics: List of metric dictionaries.

    Returns:
        Dictionary of metric name -> derived summary value.
    """
    if not metrics:
        return {}

    stats: Dict[str, Dict[str, float]] = {}

    for metric in metrics:
        phase = metric.get("phase")
        prefix = f"{phase}." if isinstance(phase, str) and phase else ""

        if isinstance(metric.get("metrics"), dict):
            metric_values = metric["metrics"]
        else:
            metric_values = {
                key: value
                for key, value in metric.items()
                if key not in CONTROL_KEYS
            }

        for key, value in metric_values.items():
            if not isinstance(value, (int, float)):
                continue

            summary_key = f"{prefix}{key}"
            numeric_value = float(value)
            current = stats.get(summary_key)
            if current is None:
                stats[summary_key] = {
                    "count": 1,
                    "sum": numeric_value,
                    "min": numeric_value,
                    "max": numeric_value,
                    "last": numeric_value,
                }
                continue

            current["count"] += 1
            current["sum"] += numeric_value
            current["min"] = min(current["min"], numeric_value)
            current["max"] = max(current["max"], numeric_value)
            current["last"] = numeric_value

    summary: Dict[str, float] = {}
    for key in sorted(stats):
        current = stats[key]
        mean = current["sum"] / current["count"]
        summary[f"{key}.last"] = current["last"]
        summary[f"{key}.mean"] = mean
        summary[f"{key}.min"] = current["min"]
        summary[f"{key}.max"] = current["max"]

    return summary


def summarize(
    name: str,
    format_name: str = "markdown",
    output_path: Optional[Path] = None,
) -> Optional[Path]:
    """Generate summary report for an experiment.

    Args:
        name: Experiment name.
        format_name: Report format (markdown, json, html).
        output_path: Optional custom output path.

    Returns:
        Path to generated report, or None if failed.
    """
    exp_dir = find_experiment(name)

    if exp_dir is None:
        logger.error(
            format_error(
                f"Experiment '{name}' not found",
                "Check experiment name or create it first with: python scripts/new_exp.py --name " + name,
            )
        )
        return None

    metrics_path = exp_dir / "logs" / "metrics.jsonl"

    # Determine output path based on format
    if output_path is None:
        formatter = ReportFactory.get_format(format_name)
        output_path = exp_dir / "findings" / f"report{formatter.extension()}"

    if not metrics_path.exists():
        logger.error(
            format_error(
                f"No metrics.jsonl found for '{name}'",
                "Run metrics logging first or check experiment name",
            )
        )
        return None

    metrics = load_metrics(metrics_path)

    if not metrics:
        logger.error("No data in metrics file.")
        return None

    summary = compute_summary(metrics)

    # Extract metadata from first environment log if present
    metadata: Dict[str, Any] = {}
    for metric in metrics:
        if metric.get("type") == "environment":
            metadata["python_version"] = metric.get("python_version", "unknown")
            metadata["platform"] = metric.get("platform", "unknown")
            break

    ReportFactory.generate_report(
        format_name=format_name,
        experiment_name=name,
        summary=summary,
        output_path=output_path,
        metadata=metadata,
    )

    logger.info(f"Report generated at {output_path}")
    return output_path


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate summary report from experiment metrics"
    )
    parser.add_argument(
        "name",
        type=validate_experiment_name,
        help="Experiment name",
    )
    parser.add_argument(
        "--format",
        "-F",
        choices=ReportFactory.list_formats(),
        default="markdown",
        help="Report output format (default: markdown)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Custom output path for report",
    )
    parser.add_argument(
        "--version",
        "-V",
        action="version",
        version="%(prog)s 1.1.0",
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
    result = summarize(args.name, args.format, args.output)
    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())
