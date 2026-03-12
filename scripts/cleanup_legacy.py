#!/usr/bin/env python3
"""Batch archive or delete legacy experiment directories."""

import argparse
import logging
import shutil
import sys
from pathlib import Path
from typing import List, Optional

from scripts.utils import safe_path

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent


def archive_directories(
    directories: List[Path],
    archive_dir: Optional[str] = ".old-archive",
    dry_run: bool = True,
) -> int:
    """Archive directories to a backup location.

    Returns the number of directories archived.
    """
    base = BASE_DIR
    archive_path = base / archive_dir

    if not dry_run:
        archive_path.mkdir(exist_ok=True)

    archived = 0
    for dir_path in directories:
        if not dir_path.exists():
            logger.warning(f"Skip (not found): {dir_path.name}")
            continue

        target = archive_path / dir_path.name

        # Handle name conflicts
        counter = 1
        while target.exists():
            target = archive_path / f"{dir_path.name}_{counter}"
            counter += 1

        if dry_run:
            print(f"  [DRY RUN] mv {dir_path} → {target}")
        else:
            try:
                shutil.move(str(dir_path), str(target))
                logger.info(f"Archived: {dir_path.name} → {target.name}")
                archived += 1
            except Exception as e:
                logger.error(f"Failed to archive {dir_path.name}: {e}")

    return archived


def delete_directories(
    directories: List[Path],
    dry_run: bool = True,
) -> int:
    """Delete directories permanently.

    Returns the number of directories deleted.
    """
    deleted = 0
    for dir_path in directories:
        if not dir_path.exists():
            logger.warning(f"Skip (not found): {dir_path.name}")
            continue

        size_mb = sum(f.stat().st_size for f in dir_path.rglob("*") if f.is_file()) / 1024 / 1024

        if dry_run:
            print(f"  [DRY RUN] rm -rf {dir_path} ({size_mb:.1f}MB)")
        else:
            try:
                shutil.rmtree(dir_path)
                logger.info(f"Deleted: {dir_path.name} ({size_mb:.1f}MB)")
                deleted += 1
            except Exception as e:
                logger.error(f"Failed to delete {dir_path.name}: {e}")

    return deleted


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Batch archive or delete legacy experiment directories"
    )
    parser.add_argument(
        "action",
        choices=["archive", "delete"],
        help="Action to perform"
    )
    parser.add_argument(
        "directories",
        nargs="*",
        type=Path,
        help="Directories to process"
    )
    parser.add_argument(
        "--archive-dir",
        default=".old-archive",
        help="Archive directory name (default: .old-archive)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all directories in parent folder"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually doing it"
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompt"
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

    directories = args.directories

    if args.all and not directories:
        # Find all non-hidden directories
        base = BASE_DIR
        directories = [
            d for d in base.iterdir()
            if d.is_dir() and not d.name.startswith(".")
            and d.name not in {"workspace", "scripts", "rules", "templates", "tests", "__pycache__"}
        ]

    if not directories:
        logger.error("No directories specified. Use --all or provide directory paths.")
        return 1

    print(f"\nAction: {args.action.upper()}")
    print(f"Directories to process: {len(directories)}")
    print()

    for d in directories:
        print(f"  • {d.name}")
    print()

    if not args.yes and not args.dry_run:
        response = input(f"Are you sure you want to {args.action} these directories? [y/N]: ")
        if response.lower() != "y":
            print("Cancelled.")
            return 0

    if args.action == "archive":
        count = archive_directories(
            directories,
            archive_dir=args.archive_dir,
            dry_run=args.dry_run,
        )
    else:
        count = delete_directories(directories, dry_run=args.dry_run)

    print(f"\nDone. {count} directories {args.action}d.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
