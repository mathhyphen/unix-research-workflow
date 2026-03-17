#!/usr/bin/env python3
"""Remove experiment directories with safety checks."""

import argparse
import logging
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from scripts.utils import safe_path, validate_experiment_name, get_workspace_paths

logger = logging.getLogger(__name__)


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


def remove_experiment(name: str, force: bool = False) -> bool:
    """Remove an experiment directory.

    Args:
        name: Experiment name to remove.
        force: If True, remove even if report exists.

    Returns:
        True if removed successfully, False otherwise.
    """
    exp_dir = find_experiment(name)

    if not exp_dir.exists():
        print(f"Error: Experiment '{name}' not found at {exp_dir}")
        return False

    # Safety check: don't remove experiments with reports unless forced
    findings_path = exp_dir / "findings" / "report.md"
    if findings_path.exists() and not force:
        print(f"Experiment '{name}' has a report. Use --force to remove.")
        return False

    # Remove git worktree if it exists
    git_dir = exp_dir / ".git"
    if git_dir.exists():
        try:
            # Remove worktree from git
            subprocess.run(
                ["git", "-C", str(BASE_DIR), "worktree", "remove", str(exp_dir)],
                capture_output=True,
                check=True,
            )
            logger.info(f"Removed git worktree for '{name}'")
        except subprocess.CalledProcessError as e:
            logger.debug(f"Git worktree remove failed: {e}")
        except FileNotFoundError:
            logger.debug("Git not found, skipping worktree removal")

    shutil.rmtree(exp_dir)
    print(f"Removed experiment '{name}'")
    return True


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Remove an experiment directory"
    )
    parser.add_argument(
        "name",
        type=validate_experiment_name,
        help="Experiment name to remove"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force removal even if report exists"
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
    success = remove_experiment(args.name, args.force)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
