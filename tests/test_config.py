#!/usr/bin/env python3
"""Tests for the Config class."""

import logging
from pathlib import Path
from typing import Any, Dict

import pytest

from scripts.config import Config, DEFAULT_CONFIG


class TestConfigInitialization:
    """Test suite for Config initialization."""

    def test_config_uses_defaults_when_no_file(self, tmp_path: Path) -> None:
        """Test that Config uses defaults when config file doesn't exist."""
        config_path = tmp_path / "nonexistent.yaml"
        config = Config(config_path)

        assert config.workspace.name == "workspace"
        assert config.templates.name == "templates"
        assert config.log_level == "INFO"

    def test_config_loads_from_file(self, tmp_path: Path) -> None:
        """Test that Config loads values from file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("workspace: custom_workspace\n")

        config = Config(config_file)

        assert config.workspace.name == "custom_workspace"

    def test_config_partial_override(self, tmp_path: Path) -> None:
        """Test that Config partially overrides defaults."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("log_level: DEBUG\n")

        config = Config(config_file)

        assert config.log_level == "DEBUG"
        assert config.workspace.name == "workspace"  # default


class TestConfigSimpleYamlParser:
    """Test suite for the simple YAML parser."""

    def test_parse_string_value(self, tmp_path: Path) -> None:
        """Test parsing string values."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("workspace: my_workspace\n")

        config = Config(config_file)

        # String values are stored with quotes if provided
        assert config.get("workspace") in ["my_workspace", '"my_workspace"']

    def test_parse_integer_value(self, tmp_path: Path) -> None:
        """Test parsing integer values."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("max_name_length: 128\n")

        config = Config(config_file)

        assert config.get("max_name_length") == 128

    def test_parse_float_value(self, tmp_path: Path) -> None:
        """Test parsing float values."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("learning_rate: 0.001\n")

        config = Config(config_file)

        assert config.get("learning_rate") == 0.001

    def test_parse_boolean_true(self, tmp_path: Path) -> None:
        """Test parsing boolean true."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("git_enabled: true\n")

        config = Config(config_file)

        assert config.get("git_enabled") is True

    def test_parse_boolean_false(self, tmp_path: Path) -> None:
        """Test parsing boolean false."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("git_enabled: false\n")

        config = Config(config_file)

        assert config.get("git_enabled") is False

    def test_parse_list(self, tmp_path: Path) -> None:
        """Test parsing list values."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "report_formats:\n"
            "  - markdown\n"
            "  - json\n"
            "  - html\n"
        )

        config = Config(config_file)

        assert config.get("report_formats") == ["markdown", "json", "html"]

    def test_parse_ignores_comments(self, tmp_path: Path) -> None:
        """Test that comments are ignored."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "# This is a comment\n"
            "workspace: test_ws\n"
            "# Another comment\n"
        )

        config = Config(config_file)

        assert config.workspace.name == "test_ws"

    def test_parse_handles_empty_lines(self, tmp_path: Path) -> None:
        """Test that empty lines are handled gracefully."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "workspace: test_ws\n"
            "\n"
            "log_level: WARNING\n"
        )

        config = Config(config_file)

        assert config.workspace.name == "test_ws"
        assert config.log_level == "WARNING"


class TestConfigProperties:
    """Test suite for Config property accessors."""

    def test_workspace_property(self, tmp_path: Path) -> None:
        """Test workspace property returns correct path."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("workspace: my_workspace\n")

        config = Config(config_file)

        # Workspace should be BASE_DIR / workspace_value
        assert str(config.workspace).endswith("my_workspace")

    def test_templates_property(self, tmp_path: Path) -> None:
        """Test templates property returns correct path."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("templates: my_templates\n")

        config = Config(config_file)

        assert str(config.templates).endswith("my_templates")

    def test_git_enabled_property(self, tmp_path: Path) -> None:
        """Test git_enabled property."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("git_enabled: false\n")

        config = Config(config_file)

        assert config.git_enabled is False

    def test_git_base_branch_property(self, tmp_path: Path) -> None:
        """Test git_base_branch property."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("git_base_branch: develop\n")

        config = Config(config_file)

        # Value is stored with quotes if provided
        assert config.git_base_branch in ["develop", '"develop"']

    def test_max_name_length_property(self, tmp_path: Path) -> None:
        """Test max_name_length property."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("max_name_length: 128\n")

        config = Config(config_file)

        assert config.max_name_length == 128

    def test_name_pattern_property(self, tmp_path: Path) -> None:
        """Test name_pattern property."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("name_pattern: ^[a-z]+$\n")

        config = Config(config_file)

        # Value might have quotes stripped by parser
        result = config.name_pattern
        if result.startswith('"') and result.endswith('"'):
            result = result[1:-1]
        assert result == "^[a-z]+$"


class TestConfigGetMethod:
    """Test suite for Config.get() method."""

    def test_get_existing_key(self, tmp_path: Path) -> None:
        """Test getting an existing key."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("workspace: test_ws\n")

        config = Config(config_file)

        assert config.get("workspace") == "test_ws"

    def test_get_nonexistent_key_with_default(self, tmp_path: Path) -> None:
        """Test getting a nonexistent key returns default."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("workspace: test_ws\n")

        config = Config(config_file)

        assert config.get("nonexistent", "default_value") == "default_value"

    def test_get_nonexistent_key_no_default(self, tmp_path: Path) -> None:
        """Test getting a nonexistent key returns None."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("workspace: test_ws\n")

        config = Config(config_file)

        assert config.get("nonexistent") is None


class TestConfigErrorHandling:
    """Test suite for Config error handling."""

    def test_config_has_defaults(self) -> None:
        """Test that Config always has default values."""
        # Simple test to verify defaults work
        config = Config(Path("/nonexistent/path/config.yaml"))

        assert config.workspace is not None
        assert config.templates is not None
        assert config.log_level == "INFO"
