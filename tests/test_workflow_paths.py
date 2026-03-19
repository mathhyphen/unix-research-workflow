"""Tests for workflow path discovery and report generation."""

import tempfile
from pathlib import Path

from scripts import utils
from scripts.list_exp import determine_experiment_status, ExperimentStatus
from scripts.summarize import compute_summary
from scripts.utils import has_report, resolve_workspace_path


class TestWorkflowPaths:
    """Test workflow path handling helpers."""

    def test_resolve_workspace_path_accepts_home_worktree(self, monkeypatch) -> None:
        """Paths inside the home Claude worktree root should be accepted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            monkeypatch.setattr(Path, "home", lambda: fake_home)

            intent_path = fake_home / ".claude" / "worktrees" / "exp-a" / "intent.yaml"
            intent_path.parent.mkdir(parents=True)
            intent_path.write_text("experiment: exp-a\n", encoding="utf-8")

            resolved = resolve_workspace_path(intent_path)
            assert resolved == intent_path.resolve()

    def test_has_report_supports_multiple_formats(self) -> None:
        """Report detection should not be limited to Markdown."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exp_dir = Path(tmpdir)
            findings = exp_dir / "findings"
            findings.mkdir()
            (findings / "report.json").write_text("{}", encoding="utf-8")

            assert has_report(exp_dir) is True
            assert determine_experiment_status(exp_dir) == ExperimentStatus.REPORT_READY


class TestSummarize:
    """Test summary generation behavior."""

    def test_compute_summary_ignores_control_fields(self) -> None:
        """Control fields like epoch should not show up as metrics."""
        summary = compute_summary([
            {"epoch": 0, "phase": "train", "loss": 0.5},
            {"epoch": 1, "phase": "train", "loss": 0.25},
        ])

        assert "train.epoch.mean" not in summary
        assert summary["train.loss.last"] == 0.25
        assert summary["train.loss.mean"] == 0.375
        assert summary["train.loss.min"] == 0.25
        assert summary["train.loss.max"] == 0.5

    def test_compute_summary_supports_nested_metrics(self) -> None:
        """Nested metric payloads should still be summarized."""
        summary = compute_summary([
            {"phase": "val", "metrics": {"dice": 0.8, "loss": 0.4}},
            {"phase": "val", "metrics": {"dice": 0.85, "loss": 0.3}},
        ])

        assert summary["val.dice.last"] == 0.85
        assert summary["val.dice.max"] == 0.85
        assert summary["val.loss.min"] == 0.3
