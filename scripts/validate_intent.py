#!/usr/bin/env python3
"""Validate intent.yaml files for research experiments."""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Optional

from scripts.utils import safe_path

BASE_DIR = Path(__file__).resolve().parent.parent


def validate_intent(intent_path: Path) -> Optional[List[str]]:
    """Validate an intent.yaml file.

    Args:
        intent_path: Path to intent.yaml file.

    Returns:
        List of validation errors, or None if valid.
    """
    if not intent_path.exists():
        return [f"File not found: {intent_path}"]

    content = intent_path.read_text()
    errors: List[str] = []

    # Check branch pattern: expl/<name>
    if not re.search(r"branch:\s+expl/[a-zA-Z0-9_-]+", content):
        errors.append("Branch pattern must be 'expl/<name>'")

    # Check objective length (min 20 chars)
    obj_match = re.search(r"objective:\s*\|\n\s+(.*)", content, re.DOTALL)
    if not obj_match or len(obj_match.group(1).strip()) < 20:
        errors.append("Objective must be at least 20 characters")

    # Check hypothesis length (min 20 chars)
    hyp_match = re.search(r"hypothesis:\s*\|\n\s+(.*)", content, re.DOTALL)
    if not hyp_match or len(hyp_match.group(1).strip()) < 20:
        errors.append("Hypothesis must be at least 20 characters")

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

    # Validate the intent file path is within allowed directories
    try:
        intent_file = safe_path(BASE_DIR, str(args.intent_file))
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
