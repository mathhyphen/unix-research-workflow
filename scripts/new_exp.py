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


def is_git_repository() -> bool:
    """Check if BASE_DIR is within a git repository.

    Returns:
        True if git repository, False otherwise.
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(BASE_DIR), "rev-parse", "--git-dir"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def worktree_exists(exp_dir: Path) -> bool:
    """Check if a worktree already exists at the given path.

    Args:
        exp_dir: Path to check.

    Returns:
        True if worktree exists, False otherwise.
    """
    try:
        result = subprocess.run(
            ["git", "worktree", "list"],
            capture_output=True,
            text=True,
            cwd=str(BASE_DIR),
        )
        return str(exp_dir) in result.stdout
    except Exception:
        return False


def branch_exists(branch_name: str) -> bool:
    """Check if a branch already exists.

    Args:
        branch_name: Branch name to check.

    Returns:
        True if branch exists, False otherwise.
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(BASE_DIR), "rev-parse", "--verify", branch_name],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except Exception:
        return False


def create_experiment(name: str) -> Optional[Path]:
    """Create a new experiment directory structure.

    Priority:
    1. If git repo: Create worktree first, then directory structure
    2. If not git repo: Just create directory structure

    Args:
        name: Experiment name (used for directory and branch names).

    Returns:
        Path to created experiment directory, or None if failed.

    Raises:
        SystemExit: If experiment already exists.
    """
    print(f"Creating experiment '{name}'...")

    workspace = BASE_DIR / "workspace"
    workspace.mkdir(exist_ok=True)
    exp_dir = safe_path(workspace, name)

    # Check if already exists
    if exp_dir.exists():
        # Check if it's a valid experiment directory
        if (exp_dir / "intent.yaml").exists() or (exp_dir / "logs").exists():
            logger.error(f"Experiment '{name}' already exists at {exp_dir}")
            print(f"  [ERROR] Experiment already exists!")
            print(f"  Use 'python scripts/rm_exp.py {name}' to remove it first.")
            sys.exit(1)
        else:
            # Directory exists but not a valid experiment, remove it
            logger.warning(f"Removing non-experiment directory at {exp_dir}")
            shutil.rmtree(exp_dir)

    # Check if this is a git repository
    git_repo = is_git_repository()

    if git_repo:
        # Git workflow: Create worktree FIRST, then directory structure
        branch_name = f"expl/{name}"

        # Check if worktree already exists
        if worktree_exists(exp_dir):
            logger.warning(f"Worktree already exists at {exp_dir}")
            print(f"  [SKIP] Git worktree: already exists")
        else:
            # Check if branch exists
            branch_exists_flag = branch_exists(branch_name)

            try:
                if branch_exists_flag:
                    # Branch exists, just create worktree pointing to it
                    subprocess.run(
                        ["git", "-C", str(BASE_DIR), "worktree", "add", str(exp_dir), branch_name],
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    logger.info(f"Git worktree created for existing branch '{branch_name}'")
                else:
                    # Create new branch with worktree
                    subprocess.run(
                        ["git", "-C", str(BASE_DIR), "worktree", "add", "-b", branch_name, str(exp_dir)],
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    logger.info(f"Git worktree created for new branch '{branch_name}'")

                print(f"  [OK] Git worktree: created (branch: {branch_name})")

            except subprocess.CalledProcessError as e:
                error_msg = e.stderr.strip() if e.stderr else "unknown error"
                logger.warning(f"Failed to create git worktree: {error_msg}")
                print(f"  [WARN] Git worktree: failed ({error_msg})")
                print(f"  Continuing without git integration...")

            except FileNotFoundError:
                logger.warning("Git not found - skipping worktree creation")
                print(f"  [SKIP] Git worktree: git not found")

    # Create directory structure (idempotent - safe to run after worktree)
    exp_dir.mkdir(parents=True, exist_ok=True)
    (exp_dir / "logs").mkdir(exist_ok=True)
    (exp_dir / "findings").mkdir(exist_ok=True)
    (exp_dir / "checkpoints").mkdir(exist_ok=True)
    print("  [OK] Created directory structure")

    # Copy intent template
    copy_intent_template(exp_dir, name)
    print("  [OK] Copied intent template")

    # Write .gitkeep files for empty directories
    (exp_dir / "checkpoints" / ".gitkeep").write_text("")
    (exp_dir / "logs" / ".gitkeep").write_text("")
    (exp_dir / "findings" / ".gitkeep").write_text("")

    logger.info(f"Experiment '{name}' initialized at {exp_dir}")
    print(f"\nDone: {exp_dir}")
    print(f"\nNext steps:")
    print(f"  1. Edit: {exp_dir}/intent.yaml")
    print(f"  2. Validate: python scripts/validate_intent.py {exp_dir}/intent.yaml")
    if git_repo:
        print(f"  3. Git: cd {exp_dir} && git add . && git commit -m 'Add {name}'")

    return exp_dir


def copy_intent_template(exp_dir: Path, name: str) -> None:
    """Copy and populate the intent.yaml template.

    Args:
        exp_dir: Experiment directory path.
        name: Experiment name for template substitution.
    """
    src = BASE_DIR / "templates" / "intent.yaml"
    dest = exp_dir / "intent.yaml"

    if not src.exists():
        logger.error(f"Template not found: {src}")
        # Create minimal intent.yaml
        content = f"""experiment: {name}
branch: expl/{name}
objective: |
  Describe your experiment objective (minimum 20 characters)
hypothesis: |
  Describe your hypothesis (minimum 20 characters)
success_criteria:
  metrics:
    - name: loss
      threshold: 0.1
      direction: lower_is_better
"""
    else:
        shutil.copy(src, dest)
        content = dest.read_text()
        content = content.replace("experiment: <name>", f"experiment: {name}")
        content = content.replace("branch: expl/<name>", f"branch: expl/{name}")

    dest.write_text(content)


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
        "--force", "-f",
        action="store_true",
        help="Force create even if experiment exists (will remove existing)"
    )
    parser.add_argument(
        "--version", "-V",
        action="version",
        version="%(prog)s 2.0.0"
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
