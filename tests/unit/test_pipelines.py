"""Unit tests for pipeline base classes."""

import pytest
from pathlib import Path

from bio_clean_agent.pipelines.base import Pipeline, PipelineStep, PipelineReport


class ConcretePipeline(Pipeline):
    """Concrete pipeline implementation for testing."""

    def __init__(self, dataset, workdir):
        super().__init__(dataset, workdir)
        self.name = "test_pipeline"
        self.steps = [
            PipelineStep("step1", "First step"),
            PipelineStep("step2", "Second step"),
        ]

    def run(self, context):
        return PipelineReport(
            success=True,
            message="Test pipeline completed",
            steps_completed=2,
            steps_total=2,
            outputs={"result": "success"},
        )


@pytest.mark.unit
class TestPipelineStep:
    """Test suite for PipelineStep."""

    def test_pipeline_step_creation(self):
        """Test pipeline step can be created."""
        step = PipelineStep("quality_check", "Check data quality")

        assert step.name == "quality_check"
        assert step.description == "Check data quality"

    def test_pipeline_step_equality(self):
        """Test pipeline steps can be compared."""
        step1 = PipelineStep("step1", "Description 1")
        step2 = PipelineStep("step1", "Description 1")
        step3 = PipelineStep("step2", "Description 2")

        assert step1.name == step2.name
        assert step1.name != step3.name


@pytest.mark.unit
class TestPipelineReport:
    """Test suite for PipelineReport."""

    def test_successful_report(self):
        """Test successful pipeline report."""
        report = PipelineReport(
            success=True,
            message="Pipeline completed successfully",
            steps_completed=5,
            steps_total=5,
        )

        assert report.success is True
        assert "successful" in report.message.lower()
        assert report.steps_completed == 5
        assert report.steps_total == 5

    def test_failed_report(self):
        """Test failed pipeline report."""
        report = PipelineReport(
            success=False,
            message="Pipeline failed at step 3",
            steps_completed=2,
            steps_total=5,
            errors=["Error in step 3"],
        )

        assert report.success is False
        assert "failed" in report.message.lower()
        assert report.steps_completed < report.steps_total
        assert len(report.errors) > 0

    def test_report_with_outputs(self):
        """Test report can include outputs."""
        outputs = {"cleaned_data": "output.csv", "report": "report.html"}
        report = PipelineReport(
            success=True,
            message="Completed",
            steps_completed=3,
            steps_total=3,
            outputs=outputs,
        )

        assert report.outputs == outputs
        assert "cleaned_data" in report.outputs

    def test_report_with_warnings(self):
        """Test report can include warnings."""
        warnings = ["Missing some metadata", "Low quality scores"]
        report = PipelineReport(
            success=True,
            message="Completed with warnings",
            steps_completed=3,
            steps_total=3,
            warnings=warnings,
        )

        assert len(report.warnings) == 2
        assert "Missing some metadata" in report.warnings


@pytest.mark.unit
class TestPipeline:
    """Test suite for Pipeline base class."""

    def test_pipeline_initialization(self, sample_dataset_config, tmp_path):
        """Test pipeline can be initialized."""
        from bio_clean_agent.dataspec.models import load_dataset

        dataset = load_dataset("sequencing", sample_dataset_config)
        pipeline = ConcretePipeline(dataset, tmp_path)

        assert pipeline.dataset == dataset
        assert pipeline.workdir == tmp_path
        assert pipeline.name == "test_pipeline"
        assert len(pipeline.steps) == 2

    def test_pipeline_has_steps(self, sample_dataset_config, tmp_path):
        """Test pipeline has defined steps."""
        from bio_clean_agent.dataspec.models import load_dataset

        dataset = load_dataset("sequencing", sample_dataset_config)
        pipeline = ConcretePipeline(dataset, tmp_path)

        assert len(pipeline.steps) > 0
        assert all(isinstance(step, PipelineStep) for step in pipeline.steps)

    def test_pipeline_run_returns_report(self, sample_dataset_config, tmp_path):
        """Test pipeline run returns a report."""
        from bio_clean_agent.dataspec.models import load_dataset

        dataset = load_dataset("sequencing", sample_dataset_config)
        pipeline = ConcretePipeline(dataset, tmp_path)

        context = {
            "dataset": dataset,
            "workdir": str(tmp_path),
            "parameters": {},
        }
        report = pipeline.run(context)

        assert isinstance(report, PipelineReport)
        assert report.success is True
        assert report.steps_completed == report.steps_total

    def test_pipeline_workdir_is_path(self, sample_dataset_config, tmp_path):
        """Test pipeline workdir is a Path object."""
        from bio_clean_agent.dataspec.models import load_dataset

        dataset = load_dataset("sequencing", sample_dataset_config)
        pipeline = ConcretePipeline(dataset, tmp_path)

        assert isinstance(pipeline.workdir, Path)
