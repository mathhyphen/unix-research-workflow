#!/usr/bin/env python3
"""Migrate a legacy experiment directory to the standard workspace structure."""

import argparse
import logging
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from scripts.utils import safe_path, validate_experiment_name, format_error, get_workspace_paths

logger = logging.getLogger(__name__)


def create_migration_target(name: str) -> Path:
    """Create the migration target directory in workspace."""
    # Use first available workspace
    workspace = get_workspace_paths()[0]
    workspace.mkdir(exist_ok=True)

    exp_dir = safe_path(workspace, name)

    if exp_dir.exists():
        raise FileExistsError(f"Experiment '{name}' already exists at {exp_dir}")

    exp_dir.mkdir(parents=True)
    (exp_dir / "logs").mkdir(exist_ok=True)
    (exp_dir / "findings").mkdir(exist_ok=True)

    return exp_dir


def copy_intent_template(exp_dir: Path, name: str, custom_intent: Optional[Dict[str, Any]] = None) -> None:
    """Create intent.yaml for migrated experiment."""
    template_path = BASE_DIR / "templates" / "intent.yaml"

    if template_path.exists() and not custom_intent:
        # Use template
        shutil.copy(template_path, exp_dir / "intent.yaml")
        content = (exp_dir / "intent.yaml").read_text()
        content = content.replace("experiment: <name>", f"experiment: {name}")
        content = content.replace("branch: expl/<name>", f"branch: migrated/{name}")
        (exp_dir / "intent.yaml").write_text(content)
    else:
        # Create minimal intent
        intent_content = f"""experiment: {name}
branch: migrated/{name}
objective: |
  [TODO] Describe the objective of this migrated experiment
hypothesis: |
  [TODO] Describe your hypothesis
success_criteria:
  metrics:
    - name: loss
      threshold: 0.1
      direction: lower_is_better
migrated_from: legacy directory
"""
        (exp_dir / "intent.yaml").write_text(intent_content)


def migrate_logs(source: Path, target: Path) -> int:
    """Migrate log files to standard format.

    Returns the number of files migrated.
    """
    migrated = 0
    metrics_target = target / "logs" / "metrics.jsonl"

    # Look for common log file patterns
    log_patterns = [
        "*.jsonl", "*.json", "*.log", "*.txt", "*.csv",
        "*metric*", "*log*", "*result*", "*output*",
    ]

    found_files: List[Path] = []
    for pattern in log_patterns:
        found_files.extend(source.rglob(pattern))

    # Deduplicate
    found_files = list(set(found_files))

    if not found_files:
        logger.warning(f"No log files found in {source}")
        return 0

    # Copy log files to logs directory
    logs_dir = target / "logs"
    logs_dir.mkdir(exist_ok=True)

    for log_file in found_files[:10]:  # Limit to 10 files
        if log_file.is_file():
            try:
                shutil.copy2(log_file, logs_dir / log_file.name)
                migrated += 1
                logger.info(f"Copied log: {log_file.name}")
            except Exception as e:
                logger.warning(f"Failed to copy {log_file.name}: {e}")

    # Create a combined metrics.jsonl if we found JSON/JSONL files
    jsonl_files = [f for f in found_files if f.suffix in {".jsonl", ".json"}]
    if jsonl_files:
        with open(metrics_target, "w") as out_f:
            for jsonl_file in jsonl_files[:5]:  # Limit to 5 files
                try:
                    with open(jsonl_file, "r") as in_f:
                        for line in in_f:
                            if line.strip():
                                out_f.write(line)
                except Exception as e:
                    logger.warning(f"Failed to read {jsonl_file.name}: {e}")
        migrated += 1
        logger.info(f"Created combined metrics.jsonl from {len(jsonl_files)} files")

    return migrated


def migrate_models(source: Path, target: Path) -> int:
    """Migrate model files to standard location.

    Returns the number of models migrated.
    """
    migrated = 0
    model_extensions = {".pt", ".pth", ".ckpt", ".bin", ".onnx", ".pb"}

    # Find model files
    model_files: List[Path] = []
    for ext in model_extensions:
        model_files.extend(source.rglob(f"*{ext}"))

    # Also look for "model" or "checkpoint" in name
    for pattern in ["*model*", "*checkpoint*", "*best*"]:
        for f in source.rglob(pattern):
            if f.is_file() and f not in model_files:
                model_files.append(f)

    if not model_files:
        logger.info(f"No model files found in {source}")
        return 0

    # Create checkpoints directory
    checkpoints_dir = target / "checkpoints"
    checkpoints_dir.mkdir(exist_ok=True)

    for model_file in model_files[:10]:  # Limit to 10 models
        if model_file.is_file():
            try:
                shutil.copy2(model_file, checkpoints_dir / model_file.name)
                migrated += 1
                logger.info(f"Copied model: {model_file.name}")
            except Exception as e:
                logger.warning(f"Failed to copy {model_file.name}: {e}")

    return migrated


def migrate_experiment(
    name: str,
    source: Path,
    target_name: Optional[str] = None,
    skip_models: bool = False,
    skip_logs: bool = False,
) -> Optional[Path]:
    """Migrate a legacy experiment to standard structure.

    Args:
        name: Source experiment name (directory name).
        source: Source directory path.
        target_name: Optional custom target name in workspace.
        skip_models: Skip model file migration.
        skip_logs: Skip log file migration.

    Returns:
        Path to migrated experiment directory, or None if failed.
    """
    target_name = target_name or name.replace(" ", "-").replace("_", "-")

    # Validate target name
    try:
        validate_experiment_name(target_name)
    except argparse.ArgumentTypeError as e:
        logger.error(format_error(
            f"Invalid target name '{target_name}'",
            str(e)
        ))
        return None

    print(f"\nMigrating '{name}' → '{target_name}'...")

    try:
        exp_dir = create_migration_target(target_name)
    except FileExistsError as e:
        logger.error(str(e))
        return None

    # Create intent.yaml
    copy_intent_template(exp_dir, target_name)
    print("  [OK] Created intent.yaml")

    # Migrate logs
    if not skip_logs:
        log_count = migrate_logs(source, exp_dir)
        if log_count > 0:
            print(f"  [OK] Migrated {log_count} log file(s)")
        else:
            print("  [SKIP] No log files found")

    # Migrate models
    if not skip_models:
        model_count = migrate_models(source, exp_dir)
        if model_count > 0:
            print(f"  [OK] Migrated {model_count} model file(s)")
        else:
            print("  [SKIP] No model files found")

    print(f"\nDone: {exp_dir}")
    print(f"\nNext steps:")
    print(f"  1. Edit {exp_dir}/intent.yaml to fill in experiment details")
    print(f"  2. Run: python scripts/validate_intent.py {exp_dir}/intent.yaml")
    print(f"  3. Run: python scripts/summarize.py {target_name}")

    return exp_dir


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Migrate legacy experiment to standard workspace structure"
    )
    parser.add_argument(
        "source",
        type=Path,
        help="Source legacy experiment directory"
    )
    parser.add_argument(
        "--name", "-n",
        type=str,
        default=None,
        help="Target name in workspace (default: derived from source directory name)"
    )
    parser.add_argument(
        "--skip-models",
        action="store_true",
        help="Skip migrating model files"
    )
    parser.add_argument(
        "--skip-logs",
        action="store_true",
        help="Skip migrating log files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without actually doing it"
    )
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        stream=sys.stderr,
    )

    args = parse_args()

    if not args.source.exists():
        logger.error(f"Source directory not found: {args.source}")
        return 1

    if not args.source.is_dir():
        logger.error(f"Source is not a directory: {args.source}")
        return 1

    if args.dry_run:
        print(f"\n[DRY RUN] Would migrate:")
        print(f"  Source: {args.source}")
        print(f"  Target: workspace/{args.name or args.source.name}")
        print(f"  Skip models: {args.skip_models}")
        print(f"  Skip logs: {args.skip_logs}")
        return 0

    result = migrate_experiment(
        name=args.source.name,
        source=args.source,
        target_name=args.name,
        skip_models=args.skip_models,
        skip_logs=args.skip_logs,
    )

    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())
