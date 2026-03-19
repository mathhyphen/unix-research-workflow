"""Tests for validate_intent module."""

import tempfile
from pathlib import Path

from scripts.validate_intent import validate_intent


VALID_SUCCESS_CRITERIA = """success_criteria:
  metrics:
    - name: val_loss
      threshold: 0.1
      direction: lower_is_better
"""


class TestValidateIntent:
    """Test cases for validate_intent function."""

    def test_valid_intent(self) -> None:
        """Test validation of a valid intent.yaml."""
        content = f"""
experiment: test-exp
branch: expl/test-exp
objective: |
  This is a valid objective that is long enough
  for the validation to pass.
hypothesis: |
  This is a valid hypothesis that is also long
  enough to pass the validation checks.
{VALID_SUCCESS_CRITERIA}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(content)
            f.flush()
            result = validate_intent(Path(f.name))
            assert result is None

    def test_missing_file(self) -> None:
        """Test validation when file does not exist."""
        result = validate_intent(Path("/nonexistent/path.yaml"))
        assert result is not None
        assert "File not found" in result[0]

    def test_invalid_yaml_syntax(self) -> None:
        """Test validation with invalid YAML syntax."""
        content = """
experiment: test-exp
branch: expl/test-exp
objective: |
  Invalid YAML
  unclosed block
hypothesis
  missing colon
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(content)
            f.flush()
            result = validate_intent(Path(f.name))
            assert result is not None
            assert "Invalid YAML syntax" in result[0]

    def test_empty_file(self) -> None:
        """Test validation with empty file."""
        content = ""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(content)
            f.flush()
            result = validate_intent(Path(f.name))
            assert result is not None
            assert "Empty YAML file" in result[0]

    def test_invalid_branch_pattern(self) -> None:
        """Test validation with invalid branch pattern."""
        content = f"""
experiment: test-exp
branch: invalid-branch
objective: |
  This is a valid objective that is long enough
  for the validation to pass.
hypothesis: |
  This is a valid hypothesis that is also long
  enough to pass the validation checks.
{VALID_SUCCESS_CRITERIA}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(content)
            f.flush()
            result = validate_intent(Path(f.name))
            assert result is not None
            assert "Branch pattern must be" in result[0]

    def test_short_objective(self) -> None:
        """Test validation with objective too short."""
        content = f"""
experiment: test-exp
branch: expl/test-exp
objective: |
  Too short.
hypothesis: |
  This is a valid hypothesis that is also long
  enough to pass the validation checks.
{VALID_SUCCESS_CRITERIA}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(content)
            f.flush()
            result = validate_intent(Path(f.name))
            assert result is not None
            assert "Objective must be at least 20 characters" in result[0]

    def test_short_hypothesis(self) -> None:
        """Test validation with hypothesis too short."""
        content = f"""
experiment: test-exp
branch: expl/test-exp
objective: |
  This is a valid objective that is long enough
  for the validation to pass.
hypothesis: |
  Too short.
{VALID_SUCCESS_CRITERIA}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(content)
            f.flush()
            result = validate_intent(Path(f.name))
            assert result is not None
            assert "Hypothesis must be at least 20 characters" in result[0]

    def test_missing_fields(self) -> None:
        """Test validation with missing required fields."""
        content = """
experiment: test-exp
branch: expl/test-exp
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(content)
            f.flush()
            result = validate_intent(Path(f.name))
            assert result is not None
            assert len(result) >= 2
            assert any("Objective field is required" in err for err in result)
            assert any("Hypothesis field is required" in err for err in result)

    def test_missing_success_criteria(self) -> None:
        """Test validation when success criteria are missing."""
        content = """
experiment: test-exp
branch: expl/test-exp
objective: |
  This is a valid objective that is long enough
  for the validation to pass.
hypothesis: |
  This is a valid hypothesis that is also long
  enough to pass the validation checks.
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(content)
            f.flush()
            result = validate_intent(Path(f.name))
            assert result is not None
            assert any("success_criteria field is required" in err for err in result)

    def test_invalid_success_criteria_metric(self) -> None:
        """Test validation for malformed success criteria metrics."""
        content = """
experiment: test-exp
branch: expl/test-exp
objective: |
  This is a valid objective that is long enough
  for the validation to pass.
hypothesis: |
  This is a valid hypothesis that is also long
  enough to pass the validation checks.
success_criteria:
  metrics:
    - name: val_loss
      threshold: "low"
      direction: sideways
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(content)
            f.flush()
            result = validate_intent(Path(f.name))
            assert result is not None
            assert any(
                ".threshold is required and must be numeric" in err
                for err in result
            )
            assert any(".direction must be one of" in err for err in result)
