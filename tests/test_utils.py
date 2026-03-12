#!/usr/bin/env python3
"""Tests for utility functions in utils.py."""

import argparse
from pathlib import Path
from typing import Any

import pytest

from scripts.utils import safe_path, validate_experiment_name, format_error


class TestSafePath:
    """Test suite for safe_path function."""

    def test_safe_path_with_simple_name(self, tmp_path: Path) -> None:
        """Test safe_path with a simple valid name."""
        base = tmp_path / "workspace"
        base.mkdir()

        result = safe_path(base, "my-experiment")

        assert result == base / "my-experiment"

    def test_safe_path_with_nested_name(self, tmp_path: Path) -> None:
        """Test safe_path with name containing hyphens."""
        base = tmp_path / "workspace"
        base.mkdir()

        result = safe_path(base, "ablation-study-v2")

        assert result == base / "ablation-study-v2"

    def test_safe_path_blocks_traversal_with_dotdot(self) -> None:
        """Test that safe_path blocks ../ traversal."""
        base = Path("/tmp/workspace")

        with pytest.raises(ValueError, match="Path traversal detected"):
            safe_path(base, "../etc/passwd")

    def test_safe_path_blocks_traversal_with_absolute(self) -> None:
        """Test that safe_path blocks absolute path traversal."""
        base = Path("/tmp/workspace")

        with pytest.raises(ValueError, match="Path traversal detected"):
            safe_path(base, "/etc/passwd")

    def test_safe_path_blocks_complex_traversal(self) -> None:
        """Test that safe_path blocks complex traversal."""
        base = Path("/tmp/workspace")

        with pytest.raises(ValueError, match="Path traversal detected"):
            safe_path(base, "foo/../../etc/passwd")

    def test_safe_path_with_normal_name(self, tmp_path: Path) -> None:
        """Test safe_path with alphanumeric name."""
        base = tmp_path / "workspace"
        base.mkdir()

        result = safe_path(base, "experiment123")

        assert result == base / "experiment123"

    def test_safe_path_with_underscore(self, tmp_path: Path) -> None:
        """Test safe_path with underscore in name."""
        base = tmp_path / "workspace"
        base.mkdir()

        result = safe_path(base, "my_experiment")

        assert result == base / "my_experiment"


class TestValidateExperimentName:
    """Test suite for validate_experiment_name function."""

    def test_valid_simple_name(self) -> None:
        """Test validation of simple valid name."""
        result = validate_experiment_name("my-experiment")
        assert result == "my-experiment"

    def test_valid_name_with_underscore(self) -> None:
        """Test validation of name with underscore."""
        result = validate_experiment_name("my_experiment")
        assert result == "my_experiment"

    def test_valid_name_with_numbers(self) -> None:
        """Test validation of name with numbers."""
        result = validate_experiment_name("experiment123")
        assert result == "experiment123"

    def test_valid_name_mixed(self) -> None:
        """Test validation of name with mixed characters."""
        result = validate_experiment_name("ablation-study_v2-test")
        assert result == "ablation-study_v2-test"

    def test_invalid_empty_name(self) -> None:
        """Test that empty name is rejected."""
        with pytest.raises(argparse.ArgumentTypeError, match="cannot be empty"):
            validate_experiment_name("")

    def test_invalid_starts_with_number(self) -> None:
        """Test that name starting with number is rejected."""
        with pytest.raises(argparse.ArgumentTypeError, match="Must start with a letter"):
            validate_experiment_name("123experiment")

    def test_invalid_contains_space(self) -> None:
        """Test that name with space is rejected."""
        with pytest.raises(argparse.ArgumentTypeError, match="Must start with a letter"):
            validate_experiment_name("my experiment")

    def test_invalid_contains_special_chars(self) -> None:
        """Test that name with special chars is rejected."""
        with pytest.raises(argparse.ArgumentTypeError, match="Must start with a letter"):
            validate_experiment_name("my@experiment")

    def test_invalid_too_long(self) -> None:
        """Test that too long name is rejected."""
        long_name = "a" * 65  # 65 chars, max is 64
        with pytest.raises(argparse.ArgumentTypeError, match="too long"):
            validate_experiment_name(long_name)

    def test_valid_max_length(self) -> None:
        """Test that exactly max length name is accepted."""
        max_name = "a" * 64  # 64 chars, exactly at max
        result = validate_experiment_name(max_name)
        assert result == max_name

    def test_invalid_starts_with_underscore(self) -> None:
        """Test that name starting with underscore is rejected."""
        with pytest.raises(argparse.ArgumentTypeError, match="Must start with a letter"):
            validate_experiment_name("_experiment")

    def test_invalid_starts_with_hyphen(self) -> None:
        """Test that name starting with hyphen is rejected."""
        with pytest.raises(argparse.ArgumentTypeError, match="Must start with a letter"):
            validate_experiment_name("-experiment")


class TestFormatError:
    """Test suite for format_error function."""

    def test_format_error_without_suggestion(self) -> None:
        """Test format_error without suggestion."""
        result = format_error("Something went wrong")
        assert result == "Error: Something went wrong"

    def test_format_error_with_suggestion(self) -> None:
        """Test format_error with suggestion."""
        result = format_error("File not found", "Check the path")
        assert result == "Error: File not found\n  Suggestion: Check the path"

    def test_format_error_with_multiline_suggestion(self) -> None:
        """Test format_error with multiline suggestion."""
        result = format_error(
            "Invalid input",
            "Run 'validate.py' to check\nOr see the documentation"
        )
        assert "Error: Invalid input" in result
        assert "Suggestion:" in result
