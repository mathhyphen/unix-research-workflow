#!/usr/bin/env python3
"""Configuration management for Unix Research Workflow."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

BASE_DIR = Path(__file__).resolve().parent.parent

DEFAULT_CONFIG: Dict[str, Any] = {
    "workspace": "workspace",
    "templates": "templates",
    "outputs": "outputs",
    "log_level": "INFO",
    "report_formats": ["markdown", "json", "html"],
    "git_enabled": True,
    "git_base_branch": "main",
    "max_name_length": 64,
    "name_pattern": r"^[a-zA-Z][a-zA-Z0-9_-]*$",
}


class Config:
    """Configuration manager for Unix Research Workflow."""

    def __init__(self, config_path: Optional[Path] = None) -> None:
        """Initialize configuration.

        Args:
            config_path: Path to config file. Defaults to BASE_DIR/config.yaml.
        """
        self.config_path = config_path or BASE_DIR / "config.yaml"
        self._config = DEFAULT_CONFIG.copy()
        self._load()

    def _load(self) -> None:
        """Load configuration from file using proper YAML parser."""
        if not self.config_path.exists():
            logging.debug(f"Config file not found at {self.config_path}, using defaults")
            return

        try:
            content = self.config_path.read_text(encoding="utf-8")
            loaded_config: Dict[str, Any] = yaml.safe_load(content)
            if loaded_config:
                self._config.update(loaded_config)
        except (IOError, OSError, PermissionError) as e:
            logging.warning(f"Failed to read config file: {e}, using defaults")
        except yaml.YAMLError as e:
            logging.warning(f"Failed to parse config file: {e}, using defaults")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._config.get(key, default)

    @property
    def workspace(self) -> Path:
        """Get workspace directory path."""
        return BASE_DIR / self._config["workspace"]

    @property
    def templates(self) -> Path:
        """Get templates directory path."""
        return BASE_DIR / self._config["templates"]

    @property
    def outputs(self) -> Path:
        """Get outputs directory path."""
        return BASE_DIR / self._config["outputs"]

    @property
    def log_level(self) -> str:
        """Get log level."""
        return self._config["log_level"]

    @property
    def report_formats(self) -> List[str]:
        """Get supported report formats."""
        formats = self._config["report_formats"]
        return formats if isinstance(formats, list) else ["markdown"]

    @property
    def git_enabled(self) -> bool:
        """Get git integration enabled status."""
        return bool(self._config["git_enabled"])

    @property
    def git_base_branch(self) -> str:
        """Get git base branch name."""
        return self._config["git_base_branch"]

    @property
    def max_name_length(self) -> int:
        """Get maximum experiment name length."""
        return int(self._config["max_name_length"])

    @property
    def name_pattern(self) -> str:
        """Get experiment name regex pattern."""
        return self._config["name_pattern"]
