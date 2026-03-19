#!/usr/bin/env python3
"""Create intent.yaml for a new experiment.

Worktree can be created anywhere - this script adapts to the location.
Claude Code can use its default worktree location or a custom path.

Usage:
  python -m scripts.new_exp --name <experiment-name> [--workspace <path>]
"""

import argparse
import logging
import shutil
import sys
from pathlib import Path
from typing import Optional

from scripts.utils import (
    find_experiment_path,
    get_workspace_paths,
    safe_path,
    validate_experiment_name,
)

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent


def create_intent_yaml(name: str, workspace: Optional[Path] = None) -> Optional[Path]:
    """Create intent.yaml for an experiment.

    Args:
        name: Experiment name.
        workspace: Workspace directory (default: BASE_DIR / "workspace").

    Returns:
        Path to created intent.yaml, or None if failed.
    """
    print(f"Creating intent.yaml for '{name}'...")

    if workspace is None:
        workspace = get_workspace_paths(include_missing=True)[0]
        existing_exp = find_experiment_path(name)
        if existing_exp is not None:
            workspace = existing_exp.parent

    exp_dir = safe_path(workspace, name)

    # Check if directory exists
    if not exp_dir.exists():
        logger.error(f"Experiment directory not found: {exp_dir}")
        print(f"  [ERROR] Directory not found!")
        print(f"  Expected experiment directory: {exp_dir}")
        print(f"  Please create worktree first:")
        print(f"    Claude Code: Use native worktree command")
        print(f"    Or: git worktree add <path> -b expl/{name}")
        sys.exit(1)

    # Check if intent already exists
    intent_file = exp_dir / "intent.yaml"
    if intent_file.exists():
        logger.warning(f"intent.yaml already exists at {intent_file}")
        print(f"  [WARN] intent.yaml already exists!")
        print(f"  Use 'python -m scripts.rm_exp {name}' to remove first.")
        sys.exit(1)

    # Create intent.yaml from template
    copy_intent_template(exp_dir, name)
    print(f"  [OK] Created: {intent_file}")

    # Create subdirectories if they don't exist
    (exp_dir / "logs").mkdir(exist_ok=True)
    (exp_dir / "findings").mkdir(exist_ok=True)
    (exp_dir / "checkpoints").mkdir(exist_ok=True)
    print(f"  [OK] Created subdirectories: logs/, findings/, checkpoints/")

    # Write .gitkeep files
    (exp_dir / "checkpoints" / ".gitkeep").write_text("")
    (exp_dir / "logs" / ".gitkeep").write_text("")
    (exp_dir / "findings" / ".gitkeep").write_text("")

    logger.info(f"intent.yaml created for '{name}' at {intent_file}")
    print(f"\nDone: {intent_file}")
    print(f"\nNext steps:")
    print(f"  1. Edit: {intent_file}")
    print(f"  2. Validate: python -m scripts.validate_intent {intent_file}")

    return intent_file


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
        dest.write_text(content)
    else:
        shutil.copy(src, dest)
        content = dest.read_text()
        content = content.replace("experiment: <name>", f"experiment: {name}")
        content = content.replace("branch: expl/<name>", f"branch: expl/{name}")
        dest.write_text(content)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Create intent.yaml for a new experiment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Workflow:
  1. Claude Code creates worktree (any location)
  2. This script creates intent.yaml and subdirectories

Examples:
  python -m scripts.new_exp --name my-experiment
  python -m scripts.new_exp -n my-experiment --workspace /custom/path
"""
    )
    parser.add_argument(
        "--name", "-n",
        required=True,
        type=validate_experiment_name,
        help="Experiment name (alphanumeric with hyphens)"
    )
    parser.add_argument(
        "--workspace", "-w",
        type=Path,
        default=None,
        help="Workspace directory (default: auto-detect)"
    )
    parser.add_argument(
        "--version", "-V",
        action="version",
        version="%(prog)s 3.1.0"
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point."""
    args = parse_args()
    create_intent_yaml(args.name, workspace=args.workspace)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s"
    )
    main()
