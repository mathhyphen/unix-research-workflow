#!/usr/bin/env python3
"""Utility functions for experiment scripts."""

import argparse
import logging
import re
from pathlib import Path
from typing import Iterable, List, Optional

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
REPORT_FILENAMES = ("report.md", "report.json", "report.html")


def _dedupe_paths(paths: Iterable[Path]) -> List[Path]:
    """De-duplicate paths while preserving their order."""
    seen = set()
    result: List[Path] = []

    for path in paths:
        resolved = path.expanduser().resolve()
        key = str(resolved).lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(resolved)

    return result


def get_workspace_paths(include_missing: bool = False) -> List[Path]:
    """Return workspace directories to search for experiments.

    Args:
        include_missing: Include paths even when the directory does not exist yet.
    """
    candidates = _dedupe_paths([
        BASE_DIR / "workspace",
        BASE_DIR / ".claude" / "worktrees",
        Path.home() / ".claude" / "worktrees",
    ])
    if include_missing:
        return candidates
    return [path for path in candidates if path.exists()]


def find_experiment_path(name: str) -> Optional[Path]:
    """Find an experiment directory across all configured workspaces."""
    for workspace in get_workspace_paths():
        exp_dir = safe_path(workspace, name)
        if exp_dir.exists():
            return exp_dir
    return None


def resolve_workspace_path(path: Path) -> Path:
    """Resolve a user path and ensure it stays within a known workspace root."""
    resolved = path.expanduser().resolve()
    for workspace in get_workspace_paths(include_missing=True):
        try:
            resolved.relative_to(workspace)
            return resolved
        except ValueError:
            continue

    allowed = ", ".join(str(path) for path in get_workspace_paths(include_missing=True))
    raise ValueError(
        f"Path '{resolved}' is outside supported workspaces. Allowed roots: {allowed}"
    )


def has_report(exp_dir: Path) -> bool:
    """Return True when any supported report artifact exists for an experiment."""
    findings_dir = exp_dir / "findings"
    return any((findings_dir / filename).exists() for filename in REPORT_FILENAMES)


def safe_path(base: Path, user_input: str) -> Path:
    """Validate and resolve a user-provided path safely.

    Prevents path traversal attacks by ensuring the resolved
    path is within the base directory.

    Args:
        base: Base directory that should contain all paths
        user_input: User-provided path component

    Returns:
        Resolved and validated path

    Raises:
        ValueError: If path traversal is detected
    """
    result = (base / user_input).resolve()
    base_resolved = base.resolve()

    try:
        result.relative_to(base_resolved)
    except ValueError:
        raise ValueError(
            f"Path traversal detected: '{user_input}' resolves outside base directory"
        )

    return result


def validate_experiment_name(name: str) -> str:
    """Validate experiment name format.

    Args:
        name: Experiment name to validate

    Returns:
        Validated name

    Raises:
        argparse.ArgumentTypeError: If name is invalid
    """
    if not name:
        raise argparse.ArgumentTypeError("Experiment name cannot be empty")

    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', name):
        raise argparse.ArgumentTypeError(
            f"Invalid experiment name '{name}'. "
            "Must start with a letter and contain only alphanumeric characters, "
            "hyphens, and underscores."
        )

    if len(name) > 64:
        raise argparse.ArgumentTypeError(
            f"Experiment name '{name}' is too long ({len(name)} chars). Max 64 chars."
        )

    return name


def format_error(message: str, suggestion: Optional[str] = None) -> str:
    """Format error message with optional suggestion.

    Args:
        message: The error message.
        suggestion: Optional suggestion for fixing the error.

    Returns:
        Formatted error string.
    """
    result = f"Error: {message}"
    if suggestion:
        result += f"\n  Suggestion: {suggestion}"
    return result
