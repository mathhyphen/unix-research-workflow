#!/usr/bin/env python3
"""Create new research experiment directories with git worktree support."""

import argparse
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from scripts.utils import safe_path, validate_experiment_name

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent


def create_experiment(name: str) -> Optional[Path]:
    """Create a new experiment directory structure.

    Args:
        name: Experiment name (used for directory and branch names).

    Returns:
        Path to created experiment directory, or None if failed.

    Raises:
        SystemExit: If experiment already exists.
    """
    print(f"Creating experiment '{name}'...")

    workspace = BASE_DIR / "workspace"
    exp_dir = safe_path(workspace, name)

    if exp_dir.exists():
        logger.error(f"Experiment '{name}' already exists at {exp_dir}")
        sys.exit(1)

    exp_dir.mkdir(parents=True)
    (exp_dir / "logs").mkdir()
    (exp_dir / "findings").mkdir()
    print("  [OK] Created directory structure")

    copy_intent_template(exp_dir, name)
    print("  [OK] Copied intent template")

    git_worktree_created = setup_git_worktree(exp_dir, name)
    if git_worktree_created:
        print("  [OK] Git worktree: created")
    else:
        print("  [SKIP] Git worktree: skipped (not a git repository)")

    logger.info(f"Experiment '{name}' initialized at {exp_dir}")
    print(f"Done: {exp_dir}")
    return exp_dir


def copy_intent_template(exp_dir: Path, name: str) -> None:
    """Copy and populate the intent.yaml template.

    Args:
        exp_dir: Experiment directory path.
        name: Experiment name for template substitution.
    """
    src = BASE_DIR / "templates" / "intent.yaml"
    dest = exp_dir / "intent.yaml"
    shutil.copy(src, dest)

    content = dest.read_text()
    content = content.replace("experiment: <name>", f"experiment: {name}")
    content = content.replace("branch: expl/<name>", f"branch: expl/{name}")
    dest.write_text(content)


def setup_git_worktree(exp_dir: Path, name: str) -> bool:
    """Create git worktree for experiment branch.

    Args:
        exp_dir: Experiment directory path.
        name: Branch name suffix.

    Returns:
        True if worktree was created successfully, False otherwise.
    """
    branch_name = f"expl/{name}"
    try:
        subprocess.run(
            ["git", "-C", str(BASE_DIR), "worktree", "add", str(exp_dir), "-b", branch_name],
            check=True,
            capture_output=True,
            text=True,
        )
        logger.info(f"Git worktree created for branch '{branch_name}'")
        return True
    except subprocess.CalledProcessError as e:
        logger.warning(f"Failed to create git worktree: {e.stderr.strip() if e.stderr else 'unknown error'}")
        return False
    except FileNotFoundError:
        logger.warning("Git not found - skipping worktree creation")
        return False


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Create a new research experiment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example: python new_exp.py --name ablation-study"
    )
    parser.add_argument(
        "--name", "-n",
        required=True,
        type=validate_experiment_name,
        help="Experiment name (alphanumeric with hyphens)"
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
    create_experiment(args.name)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s"
    )
    main()
