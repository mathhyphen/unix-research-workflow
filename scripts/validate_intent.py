#!/usr/bin/env python3
"""Validate intent.yaml files for research experiments."""

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from scripts.utils import resolve_workspace_path

VALID_DIRECTIONS = {"lower_is_better", "higher_is_better"}


def validate_intent(intent_path: Path) -> Optional[List[str]]:
    """Validate an intent.yaml file.

    Args:
        intent_path: Path to intent.yaml file.

    Returns:
        List of validation errors, or None if valid.
    """
    if not intent_path.exists():
        return [f"File not found: {intent_path}"]

    errors: List[str] = []

    try:
        content = intent_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return [f"Unable to read intent file: {e}"]

    try:
        data: Dict[str, Any] = yaml.safe_load(content)
    except yaml.YAMLError as e:
        return [f"Invalid YAML syntax: {e}"]

    if data is None:
        return ["Empty YAML file"]

    # Check branch pattern: expl/<name>
    branch = data.get("branch", "")
    if not branch or not re.match(r"^expl/[a-zA-Z0-9_-]+$", branch):
        errors.append("Branch pattern must be 'expl/<name>'")

    # Check objective exists and has minimum length
    objective = data.get("objective", "")
    if not objective or not isinstance(objective, str):
        errors.append("Objective field is required and must be a string")
    elif len(objective.strip()) < 20:
        errors.append("Objective must be at least 20 characters")

    # Check hypothesis exists and has minimum length
    hypothesis = data.get("hypothesis", "")
    if not hypothesis or not isinstance(hypothesis, str):
        errors.append("Hypothesis field is required and must be a string")
    elif len(hypothesis.strip()) < 20:
        errors.append("Hypothesis must be at least 20 characters")

    success_criteria = data.get("success_criteria")
    if not isinstance(success_criteria, dict):
        errors.append("success_criteria field is required and must be a mapping")
    else:
        metrics = success_criteria.get("metrics")
        if not isinstance(metrics, list) or not metrics:
            errors.append("success_criteria.metrics must be a non-empty list")
        else:
            for index, metric in enumerate(metrics, start=1):
                prefix = f"success_criteria.metrics[{index}]"
                if not isinstance(metric, dict):
                    errors.append(f"{prefix} must be a mapping")
                    continue

                name = metric.get("name")
                if not name or not isinstance(name, str):
                    errors.append(f"{prefix}.name is required and must be a string")

                threshold = metric.get("threshold")
                if not isinstance(threshold, (int, float)):
                    errors.append(
                        f"{prefix}.threshold is required and must be numeric"
                    )

                direction = metric.get("direction")
                if direction not in VALID_DIRECTIONS:
                    valid = ", ".join(sorted(VALID_DIRECTIONS))
                    errors.append(
                        f"{prefix}.direction must be one of: {valid}"
                    )

    return errors if errors else None


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Validate intent.yaml file for research experiment"
    )
    parser.add_argument(
        "intent_file",
        type=Path,
        help="Path to intent.yaml file"
    )
    parser.add_argument(
        "--version", "-V",
        action="version",
        version="%(prog)s 1.0.0"
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point."""
    args = parse_args()

    try:
        intent_file = resolve_workspace_path(args.intent_file)
    except ValueError as e:
        print(f"Error: Invalid path - {e}")
        sys.exit(1)

    errors = validate_intent(intent_file)

    if errors:
        print("Validation FAILED:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

    print("Intent is valid.")
    sys.exit(0)


if __name__ == "__main__":
    main()
