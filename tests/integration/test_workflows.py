"""Integration tests for end-to-end workflows."""

import pytest
import pandas as pd
from pathlib import Path

from bio_clean_agent.agent import BioCleaningAgent, AgentRequest, SimulatedToolExecutor
from bio_clean_agent.llm import SimulatedLLM, LLMPlanner, PlannerConfig


@pytest.mark.integration
class TestBasicWorkflow:
    """Test suite for basic agent workflow."""

    def test_complete_workflow_with_simulated_executor(self, tmp_path):
        """Test complete workflow from request to completion."""
        # Setup
        agent = BioCleaningAgent(
            default_output_root=tmp_path, executor=SimulatedToolExecutor(succeed=True)
        )

        # Register a mock pipeline
        from bio_clean_agent.pipelines.base import Pipeline, PipelineReport, PipelineStep

        class TestPipeline(Pipeline):
            def __init__(self, dataset, workdir):
                super().__init__(dataset, workdir)
                self.name = "test_pipeline"
                self.steps = [PipelineStep("step1", "Test step")]

            def run(self, context):
                return PipelineReport(
                    success=True,
                    message="Completed",
                    steps_completed=1,
                    steps_total=1,
                )

        agent.register_pipeline("sequencing", lambda d, w: TestPipeline(d, w))

        # Create request
        request = AgentRequest(
            dataset={
                "dataset_id": "test",
                "dataset_type": "sequencing",
                "raw_paths": ["test.fastq.gz"],
            },
            parameters={"quality_threshold": 20},
        )

        # Execute
        result = agent.plan_and_execute(request)

        # Verify
        assert result.plan is not None
        assert result.report is not None
        assert result.report.success is True


@pytest.mark.integration
class TestClinicalTrialWorkflow:
    """Test suite for clinical trial data cleaning workflow."""

    def test_clinical_trial_end_to_end(self, tmp_path):
        """Test end-to-end clinical trial data cleaning."""
        # Create sample clinical trial data
        data = pd.DataFrame(
            {
                "patient_id": [1, 2, 3, 4, 5],
                "visit_date": [
                    "2024-01-01",
                    "2024-01-02",
                    "2024-01-03",
                    "2024-01-04",
                    "2024-01-05",
                ],
                "blood_pressure_systolic": [120, 130, 125, 128, 122],
                "blood_pressure_diastolic": [80, 85, 82, 84, 81],
                "heart_rate": [70, 75, 72, 74, 71],
            }
        )

        csv_path = tmp_path / "trial_data.csv"
        data.to_csv(csv_path, index=False)

        # Load and process
        from bio_clean_agent.medical.clinical_trials import ClinicalTrialHandler

        handler = ClinicalTrialHandler()
        loaded_data = handler.load(str(csv_path))

        # Assess quality
        quality = handler.assess_quality(loaded_data)

        assert "score" in quality
        assert quality["score"] > 0


@pytest.mark.integration
class TestLLMIntegration:
    """Test suite for LLM integration in workflows."""

    def test_workflow_with_llm_planner(self, tmp_path):
        """Test workflow with LLM-assisted planning."""
        # Setup agent with simulated LLM
        agent = BioCleaningAgent(
            default_output_root=tmp_path, executor=SimulatedToolExecutor(succeed=True)
        )

        # Register pipeline
        from bio_clean_agent.pipelines.base import Pipeline, PipelineReport, PipelineStep

        class TestPipeline(Pipeline):
            def __init__(self, dataset, workdir):
                super().__init__(dataset, workdir)
                self.name = "test_pipeline"
                self.steps = [PipelineStep("step1", "Test step")]

            def run(self, context):
                return PipelineReport(
                    success=True,
                    message="Completed",
                    steps_completed=1,
                    steps_total=1,
                )

        agent.register_pipeline("sequencing", lambda d, w: TestPipeline(d, w))

        # Create LLM planner
        config = PlannerConfig(model="simulated")
        llm = SimulatedLLM()
        planner = LLMPlanner(llm, config)

        # Create request
        request = AgentRequest(
            dataset={
                "dataset_id": "test",
                "dataset_type": "sequencing",
                "raw_paths": ["test.fastq.gz"],
            }
        )

        # Execute with LLM guidance
        result = agent.plan_and_execute(
            request, user_goal="Clean sequencing data", planner=planner
        )

        # Verify
        assert result.plan is not None
        assert result.report is not None
        assert result.planner_output is not None


@pytest.mark.integration
class TestErrorHandling:
    """Test suite for error handling in workflows."""

    def test_workflow_with_missing_input_files(self, tmp_path):
        """Test workflow handles missing input files gracefully."""
        agent = BioCleaningAgent(
            default_output_root=tmp_path, executor=SimulatedToolExecutor(succeed=True)
        )

        # Register pipeline
        from bio_clean_agent.pipelines.base import Pipeline, PipelineReport, PipelineStep

        class TestPipeline(Pipeline):
            def __init__(self, dataset, workdir):
                super().__init__(dataset, workdir)
                self.name = "test_pipeline"
                self.steps = [PipelineStep("step1", "Test step")]

            def run(self, context):
                return PipelineReport(
                    success=True,
                    message="Completed",
                    steps_completed=1,
                    steps_total=1,
                )

        agent.register_pipeline("sequencing", lambda d, w: TestPipeline(d, w))

        # Create request with non-existent file
        request = AgentRequest(
            dataset={
                "dataset_id": "test",
                "dataset_type": "sequencing",
                "raw_paths": [str(tmp_path / "nonexistent.fastq.gz")],
            }
        )

        # Should raise error or handle gracefully
        try:
            result = agent.plan_and_execute(request)
            # If it doesn't raise, check for warnings
            assert len(result.plan.warnings) > 0 or not result.report.success
        except (FileNotFoundError, ValueError):
            # Expected behavior
            pass

    def test_workflow_with_invalid_parameters(self, tmp_path):
        """Test workflow handles invalid parameters."""
        agent = BioCleaningAgent(
            default_output_root=tmp_path, executor=SimulatedToolExecutor(succeed=True)
        )

        # Register pipeline
        from bio_clean_agent.pipelines.base import Pipeline, PipelineReport, PipelineStep

        class TestPipeline(Pipeline):
            def __init__(self, dataset, workdir):
                super().__init__(dataset, workdir)
                self.name = "test_pipeline"
                self.steps = [PipelineStep("step1", "Test step")]

            def run(self, context):
                return PipelineReport(
                    success=True,
                    message="Completed",
                    steps_completed=1,
                    steps_total=1,
                )

        agent.register_pipeline("sequencing", lambda d, w: TestPipeline(d, w))

        # Create request with invalid parameters
        request = AgentRequest(
            dataset={
                "dataset_id": "test",
                "dataset_type": "sequencing",
                "raw_paths": ["test.fastq.gz"],
            },
            parameters={"quality_threshold": -10},  # Invalid threshold
        )

        # Execute - should handle invalid parameter
        result = agent.plan_and_execute(request)

        # Should complete but may have warnings
        assert result.plan is not None
