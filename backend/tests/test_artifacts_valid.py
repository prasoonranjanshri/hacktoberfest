"""Tests for validating sample artifacts against schema contract."""

from backend.app.config import ARTIFACTS_DIR
from common.artifact_schema import validate_artifacts


def test_sample_artifacts_valid():
    """Sample artifacts in artifacts/ must pass validation with 0 errors."""
    errors = validate_artifacts(ARTIFACTS_DIR)
    assert errors == []
