#!/usr/bin/env python3
"""Scan a legacy messy experiment directory and generate a migration report."""

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent


class ExperimentCategory(Enum):
    """Category for legacy experiments."""
    VALUABLE = "valuable"      # Worth migrating
    MAYBE = "maybe"           # Maybe migrate later
    ARCHIVE = "archive"       # Archive only
    DELETE = "delete"         # Can delete


@dataclass
class LegacyExperiment:
    """Information about a legacy experiment."""
    name: str
    path: Path
    category: ExperimentCategory
    has_metrics: bool
    has_models: bool
    has_logs: bool
    file_count: int
    total_size_mb: float
    notes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": str(self.path),
            "category": self.category.value,
            "has_metrics": self.has_metrics,
            "has_models": self.has_models,
            "has_logs": self.has_logs,
            "file_count": self.file_count,
            "total_size_mb": round(self.total_size_mb, 2),
            "notes": self.notes,
        }


# Keywords for categorization
VALUABLE_KEYWORDS = [
    "final", "best", "paper", "submit", "result", "baseline",
    "main", "core", "key", "important", "v2", "v3",  # Later versions
]

DELETE_KEYWORDS = [
    "test", "temp", "tmp", "backup", "old", "copy",
    "debug", "try", "随便", "测试",
]

ARCHIVE_KEYWORDS = [
    "backup", "history", "202", "201",  # Old dates
]


def guess_category(name: str, exp: "LegacyExperiment") -> ExperimentCategory:
    """Guess the category of an experiment based on name and content."""
    name_lower = name.lower()

    # Check for delete keywords
    for kw in DELETE_KEYWORDS:
        if kw in name_lower:
            return ExperimentCategory.DELETE

    # Check for valuable keywords
    for kw in VALUABLE_KEYWORDS:
        if kw in name_lower:
            return ExperimentCategory.VALUABLE

    # Check for archive keywords
    for kw in ARCHIVE_KEYWORDS:
        if kw in name_lower:
            return ExperimentCategory.ARCHIVE

    # Default based on content
    if exp.has_metrics or exp.has_models:
        return ExperimentCategory.MAYBE

    return ExperimentCategory.ARCHIVE


def analyze_directory(path: Path) -> LegacyExperiment:
    """Analyze a directory to understand what's in it."""
    notes: List[str] = []
    has_metrics = False
    has_models = False
    has_logs = False
    file_count = 0
    total_size = 0

    model_extensions = {".pt", ".pth", ".ckpt", ".bin", ".onnx", ".pb"}
    metric_extensions = {".json", ".jsonl", ".csv", ".txt", ".log"}
    log_extensions = {".log", ".txt", ".out", ".err"}

    try:
        for item in path.rglob("*"):
            if item.is_file():
                file_count += 1
                total_size += item.stat().st_size

                suffix = item.suffix.lower()
                name_lower = item.name.lower()

                if suffix in model_extensions:
                    has_models = True
                    notes.append(f"Model: {item.name}")

                if suffix in metric_extensions or "metric" in name_lower:
                    has_metrics = True

                if suffix in log_extensions or "log" in name_lower:
                    has_logs = True

    except PermissionError:
        notes.append("Permission denied on some files")

    # Estimate category
    exp = LegacyExperiment(
        name=path.name,
        path=path,
        category=ExperimentCategory.ARCHIVE,  # Will be updated
        has_metrics=has_metrics,
        has_models=has_models,
        has_logs=has_logs,
        file_count=file_count,
        total_size_mb=total_size / 1024 / 1024,
        notes=notes[:5],  # Limit notes
    )

    exp.category = guess_category(path.name, exp)

    return exp


def scan_directory(target: Path) -> List[LegacyExperiment]:
    """Scan a directory for potential experiments."""
    experiments = []

    # Look for subdirectories that might be experiments
    for item in target.iterdir():
        if not item.is_dir():
            continue

        # Skip hidden directories and common non-experiment dirs
        if item.name.startswith(".") or item.name in {
            "__pycache__", "node_modules", ".git", "venv", "env",
            "scripts", "rules", "templates", "tests", "workspace",
        }:
            continue

        exp = analyze_directory(item)
        experiments.append(exp)

    return experiments


def print_report(experiments: List[LegacyExperiment]) -> None:
    """Print a migration report."""
    if not experiments:
        print("No legacy experiments found.")
        return

    # Count by category
    valuable = [e for e in experiments if e.category == ExperimentCategory.VALUABLE]
    maybe = [e for e in experiments if e.category == ExperimentCategory.MAYBE]
    archive = [e for e in experiments if e.category == ExperimentCategory.ARCHIVE]
    delete = [e for e in experiments if e.category == ExperimentCategory.DELETE]

    print("\n" + "=" * 60)
    print("LEGACY EXPERIMENT SCAN REPORT")
    print("=" * 60)

    print(f"\n📊 Summary:")
    print(f"   Total directories scanned: {len(experiments)}")
    print(f"   🟢 Valuable (migrate first): {len(valuable)}")
    print(f"   🟡 Maybe (migrate later): {len(maybe)}")
    print(f"   🟠 Archive (keep but don't migrate): {len(archive)}")
    print(f"   🔴 Delete (can remove): {len(delete)}")

    if valuable:
        print(f"\n🟢 VALUABLE - Priority Migration:")
        for exp in valuable:
            print(f"   • {exp.name}")
            print(f"     Files: {exp.file_count}, Size: {exp.total_size_mb:.1f}MB")
            if exp.has_models:
                print(f"     ✓ Has model files")
            if exp.has_metrics:
                print(f"     ✓ Has metrics/logs")

    if maybe:
        print(f"\n🟡 MAYBE - Consider Migration:")
        for exp in maybe:
            print(f"   • {exp.name} ({exp.file_count} files, {exp.total_size_mb:.1f}MB)")

    if archive:
        print(f"\n🟠 ARCHIVE - Keep As-Is:")
        for exp in archive:
            print(f"   • {exp.name}")

    if delete:
        print(f"\n🔴 DELETE - Safe to Remove:")
        for exp in delete:
            print(f"   • {exp.name} ({exp.total_size_mb:.1f}MB)")

    print("\n" + "=" * 60)
    print("Migration Commands:")
    print("=" * 60)

    if valuable:
        print("\n# Step 1: Migrate valuable experiments")
        for exp in valuable:
            print(f"python scripts/new_exp.py --name {exp.name.replace(' ', '-')}")

    print("\n# Step 2: Archive old directories")
    print("mkdir -p .old-archive")
    for exp in archive + delete:
        print(f"# mv {exp.path.name} .old-archive/")

    print()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Scan legacy experiment directory and generate migration report"
    )
    parser.add_argument(
        "--target", "-t",
        type=Path,
        default=None,
        help="Target directory to scan (default: parent of workspace)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON instead of formatted report"
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

    target = args.target or (BASE_DIR)

    if not target.exists():
        logger.error(f"Target directory not found: {target}")
        return 1

    experiments = scan_directory(target)

    if args.json:
        import json
        print(json.dumps([e.to_dict() for e in experiments], indent=2))
    else:
        print_report(experiments)

    return 0


if __name__ == "__main__":
    sys.exit(main())
