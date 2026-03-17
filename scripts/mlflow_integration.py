#!/usr/bin/env python3
"""MLflow integration helper for the Unix Research Workflow skill.

This module provides seamless MLflow integration while maintaining
compatibility with the existing LogHook system.

Usage:
    from scripts.mlflow_hook import MlflowHook

    hook = MlflowHook(workspace_path, experiment_name="my-experiment")
    hook.start_run()

    for epoch in range(epochs):
        loss, dice = train()
        hook.log_epoch(epoch, {"loss": loss, "dice": dice})

    hook.end_run()
"""

import logging
import os
import platform
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("[MLflow] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class MlflowHook:
    """Hook for logging to both MLflow and Skill's JSONL format.

    This hook maintains compatibility with the existing LogHook
    while adding MLflow tracking capabilities.

    Attributes:
        workspace_path: Path to the experiment workspace.
        experiment_name: Name of the MLflow experiment.
        mlflow_experiment_id: ID of the MLflow experiment.
        run: Current MLflow run object.
        tracking_uri: MLflow tracking server URI.
    """

    def __init__(
        self,
        workspace_path: Path,
        experiment_name: Optional[str] = None,
        tracking_uri: Optional[str] = None,
        log_to_jsonl: bool = True,
    ) -> None:
        """Initialize the MLflow hook.

        Args:
            workspace_path: Path to the experiment workspace directory.
            experiment_name: Name for MLflow experiment (default: parent dir name).
            tracking_uri: MLflow tracking server URI (default: ./mlruns).
            log_to_jsonl: Also log to metrics.jsonl for Skill compatibility.
        """
        self.workspace_path = workspace_path
        self.experiment_name = experiment_name or workspace_path.name
        self.log_to_jsonl = log_to_jsonl

        # Setup paths
        self.logs_dir = workspace_path / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_file = self.logs_dir / "metrics.jsonl"

        # MLflow setup
        try:
            import mlflow
            self.mlflow = mlflow
        except ImportError:
            raise ImportError(
                "MLflow is not installed. Install with: pip install mlflow"
            )

        # Set tracking URI (default to local mlruns folder)
        if tracking_uri is None:
            tracking_uri = str(workspace_path / "mlruns")
        self.tracking_uri = tracking_uri
        self.mlflow.set_tracking_uri(tracking_uri)

        # Set experiment
        self.mlflow.set_experiment(self.experiment_name)
        self.run = None

        if logger:
            logger.info(f"MLflow tracking URI: {tracking_uri}")
            logger.info(f"Experiment: {self.experiment_name}")

    def start_run(
        self,
        run_name: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        log_params: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Start a new MLflow run.

        Args:
            run_name: Name for this run (default: experiment name).
            tags: Additional tags to add to the run.
            log_params: Parameters to log at the start of the run.
        """
        run_name = run_name or self.experiment_name

        # Build tags
        all_tags = tags or {}
        all_tags["skill"] = "unix-research-workflow"
        all_tags["workspace"] = str(self.workspace_path)

        # Start run
        self.run = self.mlflow.start_run(run_name=run_name, tags=all_tags)

        # Log initial parameters
        if log_params:
            for key, value in log_params.items():
                self.mlflow.log_param(key, value)

        # Log environment info
        self.log_environment()

        if logger:
            logger.info(f"Started MLflow run: {run_name}")

    def end_run(self) -> None:
        """End the current MLflow run."""
        if self.run:
            self.mlflow.end_run()
            if logger:
                logger.info("Ended MLflow run")
            self.run = None

    def log(self, data: Dict[str, Any], step: Optional[int] = None) -> None:
        """Log metrics to MLflow and optionally to JSONL.

        Args:
            data: Dictionary of metrics to log.
            step: Step number for MLflow (for epoch-based logging).
        """
        # Log to MLflow
        metrics_to_log = {
            k: v for k, v in data.items()
            if isinstance(v, (int, float))
        }
        if metrics_to_log:
            self.mlflow.log_metrics(metrics_to_log, step=step)

        # Log to JSONL for Skill compatibility
        if self.log_to_jsonl and step is not None:
            self._log_to_jsonl(data, step)

    def _log_to_jsonl(self, data: Dict[str, Any], step: int) -> None:
        """Log data to JSONL file (for Skill compatibility)."""
        import json
        from datetime import datetime

        data_with_time = {
            "_timestamp": datetime.now().isoformat(),
            **data
        }
        with open(self.metrics_file, "a") as f:
            f.write(json.dumps(data_with_time) + "\n")

    def log_epoch(
        self,
        epoch: int,
        metrics: Dict[str, float],
        phase: str = "train",
        log_images: bool = False,
    ) -> None:
        """Log epoch-level metrics to MLflow and JSONL.

        Args:
            epoch: Current epoch number.
            metrics: Dictionary of metric name -> value.
            phase: Training phase (train/val/test).
            log_images: Whether to log images (if provided in metrics).
        """
        # Prefix metrics with phase
        prefixed_metrics = {
            f"{phase}_{k}": v for k, v in metrics.items()
        }

        # Log to MLflow
        self.log(prefixed_metrics, step=epoch)

        # Log to JSONL
        if self.log_to_jsonl:
            self._log_to_jsonl({
                "epoch": epoch,
                "phase": phase,
                **metrics
            }, epoch)

    def log_environment(self) -> None:
        """Log environment information as MLflow params."""
        env_params = {
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
            "hostname": platform.node(),
        }

        # Try to get PyTorch version
        try:
            import torch
            env_params["torch_version"] = torch.__version__
            env_params["cuda_available"] = torch.cuda.is_available()
            if torch.cuda.is_available():
                env_params["cuda_version"] = torch.version.cuda
                env_params["gpu_name"] = torch.cuda.get_device_name(0)
        except ImportError:
            pass

        # Try to get MONAI version (common in medical imaging)
        try:
            import monai
            env_params["monai_version"] = monai.__version__
        except ImportError:
            pass

        # Log as parameters
        for key, value in env_params.items():
            self.mlflow.log_param(key, value)

    def log_model(
        self,
        model: Any,
        artifact_path: str = "model",
        save_dir: Optional[Path] = None,
    ) -> None:
        """Log a PyTorch model to MLflow.

        Args:
            model: PyTorch model to log.
            artifact_path: Path within the artifact directory.
            save_dir: Optional directory to save model before logging.
        """
        import torch

        # Save model to temp file
        if save_dir is None:
            save_dir = self.logs_dir / "models"
            save_dir.mkdir(parents=True, exist_ok=True)

        model_path = save_dir / "model.pth"
        torch.save(model.state_dict(), model_path)

        # Log to MLflow
        self.mlflow.log_artifact(str(model_path), artifact_path)

        if logger:
            logger.info(f"Logged model to {artifact_path}")

    def log_figure(
        self,
        figure: Any,
        artifact_path: str = "figures",
        filename: str = "figure.png",
    ) -> None:
        """Log a matplotlib figure to MLflow.

        Args:
            figure: Matplotlib figure object.
            artifact_path: Path within the artifact directory.
            filename: Name for the saved figure.
        """
        import io
        from PIL import Image

        # Save figure to buffer
        buf = io.BytesIO()
        figure.savefig(buf, format="png", bbox_inches="tight")
        buf.seek(0)

        # Save to file
        fig_dir = self.logs_dir / artifact_path
        fig_dir.mkdir(parents=True, exist_ok=True)
        fig_path = fig_dir / filename

        img = Image.open(buf)
        img.save(fig_path)

        # Log to MLflow
        self.mlflow.log_artifact(str(fig_path), artifact_path)

    def set_tag(self, key: str, value: str) -> None:
        """Set a tag on the current run."""
        if self.run:
            self.mlflow.set_tag(key, value)

    def log_params(self, params: Dict[str, Any]) -> None:
        """Log multiple parameters."""
        for key, value in params.items():
            self.mlflow.log_param(key, value)

    def get_run_url(self) -> Optional[str]:
        """Get the URL to view the current run in MLflow UI."""
        if self.run:
            tracking_uri = self.mlflow.get_tracking_uri()
            if tracking_uri.startswith("http"):
                return f"{tracking_uri}/#/experiments/0/runs/{self.run.info.run_id}"
        return None


def get_mlflow_tracking_command(workspace_path: Optional[Path] = None) -> str:
    """Get the command to start MLflow UI.

    Args:
        workspace_path: Path to workspace (for local mlruns folder).

    Returns:
        Command string to start MLflow UI.
    """
    if workspace_path:
        mlruns_dir = workspace_path / "mlruns"
        return f"mlflow ui --backend-store-uri {mlruns_dir}"
    else:
        return "mlflow ui"


def show_mlflow_info(workspace_path: Path) -> None:
    """Print information about accessing MLflow UI.

    Args:
        workspace_path: Path to the experiment workspace.
    """
    mlruns_dir = workspace_path / "mlruns"

    print("\n" + "=" * 60)
    print("MLflow Tracking Information")
    print("=" * 60)
    print(f"\nTracking directory: {mlruns_dir}")
    print(f"\nTo view the MLflow UI, run:")
    print(f"  mlflow ui --backend-store-uri {mlruns_dir}")
    print(f"\nThen open: http://localhost:5000")
    print("=" * 60 + "\n")
