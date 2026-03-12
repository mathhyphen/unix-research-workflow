#!/usr/bin/env python3
"""Show detailed information about a specific experiment."""

import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

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


def load_intent(intent_path: Path) -> Optional[Dict[str, Any]]:
    """Load and parse intent.yaml (simple parser)."""
    if not intent_path.exists():
        return None

    content = intent_path.read_text()
    result = {}
    current_key = None
    current_value = []

    for line in content.split("\n"):
        if not line.strip():
            continue

        # Check for key: value or key: |
        if ":" in line and not line.startswith(" "):
            if current_key and current_value:
                result[current_key] = "\n".join(current_value).strip()
            parts = line.split(":", 1)
            current_key = parts[0].strip()
            value = parts[1].strip() if len(parts) > 1 else ""
            if value == "|":
                current_value = []
            else:
                result[current_key] = value
                current_key = None
                current_value = []
        elif line.startswith("  ") and current_key:
            current_value.append(line.strip())

    if current_key and current_value:
        result[current_key] = "\n".join(current_value).strip()

    return result


def count_metrics(metrics_path: Path) -> int:
    """Count number of metric entries."""
    if not metrics_path.exists():
        return 0

    count = 0
    with open(metrics_path, "r") as f:
        for line in f:
            if line.strip():
                count += 1
    return count


def show_experiment(name: str) -> int:
    """Show detailed information about an experiment.

    Args:
        name: Experiment name.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    workspace = BASE_DIR / "workspace"
    exp_dir = safe_path(workspace, name)

    if not exp_dir.exists():
        logger.error(format_error(
            f"Experiment '{name}' not found",
            "Use 'list_exp.py' to see available experiments"
        ))
        return 1

    logger.info(f"\n{'='*50}")
    logger.info(f"Experiment: {name}")
    logger.info(f"{'='*50}\n")

    # Intent
    intent_path = exp_dir / "intent.yaml"
    if intent_path.exists():
        intent = load_intent(intent_path)
        print("Intent:")
        if intent:
            print(f"  Branch: {intent.get('branch', 'N/A')}")
            objective = intent.get('objective', 'N/A')
            if len(objective) > 60:
                objective = objective[:57] + "..."
            print(f"  Objective: {objective}")
        print()

    # Status
    logs_path = exp_dir / "logs"
    findings_path = exp_dir / "findings"
    metrics_path = logs_path / "metrics.jsonl"
    report_path = findings_path / "report.md"

    print("Status:")
    metric_count = count_metrics(metrics_path)
    print(f"  Metrics logged: {metric_count}")
    print(f"  Report generated: {'Yes' if report_path.exists() else 'No'}")

    # Git branch
    try:
        result = subprocess.run(
            ["git", "-C", str(exp_dir), "branch", "--show-current"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            print(f"  Git branch: {result.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        logger.warning(f"  Git branch: Error checking - {e}")
    except FileNotFoundError:
        print("  Git branch: Git not found")

    print()
    return 0


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Show detailed information about an experiment"
    )
    parser.add_argument(
        "name",
        type=validate_experiment_name,
        help="Experiment name"
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
    return show_experiment(args.name)


if __name__ == "__main__":
    sys.exit(main())
