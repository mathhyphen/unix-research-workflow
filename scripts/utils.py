#!/usr/bin/env python3
"""Utility functions for experiment scripts."""

import argparse
import logging
import re
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent


def get_workspace_paths() -> List[Path]:
    """Return list of workspace directories to search for experiments."""
    paths = [BASE_DIR / "workspace"]
    # Also check .claude/worktrees/ for Claude Code native worktrees
    claude_worktrees = BASE_DIR / ".claude" / "worktrees"
    if claude_worktrees.exists():
        paths.append(claude_worktrees)
    return paths


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
