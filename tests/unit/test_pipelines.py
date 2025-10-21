"""Unit tests for pipeline base classes - basic smoke tests."""

import pytest

from bio_clean_agent.pipelines.base import Pipeline, PipelineStep, PipelineReport


@pytest.mark.unit
class TestPipelineImports:
    """Test suite for pipeline imports."""

    def test_can_import_pipeline(self):
        """Test Pipeline class can be imported."""
        assert Pipeline is not None

    def test_can_import_pipeline_step(self):
        """Test PipelineStep class can be imported."""
        assert PipelineStep is not None

    def test_can_import_pipeline_report(self):
        """Test PipelineReport class can be imported."""
        assert PipelineReport is not None
