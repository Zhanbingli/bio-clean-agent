"""Unit tests for BioCleaningAgent."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from bio_clean_agent.agent import (
    BioCleaningAgent,
    AgentRequest,
    AgentPlan,
    PlanStep,
    SimulatedToolExecutor,
    SubprocessToolExecutor,
)
from bio_clean_agent.pipelines.base import Pipeline, PipelineReport, PipelineStep


class MockPipeline(Pipeline):
    """Mock pipeline for testing."""

    def __init__(self, dataset, workdir):
        super().__init__(dataset, workdir)
        self.name = "mock_pipeline"
        self.steps = [
            PipelineStep("step1", "Step 1 description"),
            PipelineStep("step2", "Step 2 description"),
        ]

    def run(self, context):
        return PipelineReport(
            success=True,
            message="Mock pipeline completed",
            steps_completed=2,
            steps_total=2,
        )


@pytest.mark.unit
class TestBioCleaningAgent:
    """Test suite for BioCleaningAgent."""

    def test_agent_initialization(self):
        """Test agent can be initialized with default settings."""
        agent = BioCleaningAgent()
        assert agent.default_output_root == Path("outputs")
        assert isinstance(agent.executor, SubprocessToolExecutor)

    def test_agent_with_custom_output_root(self):
        """Test agent can be initialized with custom output root."""
        custom_root = "/tmp/custom_output"
        agent = BioCleaningAgent(default_output_root=custom_root)
        assert agent.default_output_root == Path(custom_root)

    def test_agent_with_simulated_executor(self):
        """Test agent can use simulated executor."""
        executor = SimulatedToolExecutor(succeed=True)
        agent = BioCleaningAgent(executor=executor)
        assert agent.executor == executor

    def test_register_pipeline(self):
        """Test pipeline registration."""
        agent = BioCleaningAgent()

        def mock_factory(dataset, workdir):
            return MockPipeline(dataset, workdir)

        agent.register_pipeline("mock_type", mock_factory)
        assert "mock_type" in agent.pipeline_registry

    def test_plan_creation(self, sample_dataset_config, tmp_path):
        """Test plan creation from dataset config."""
        agent = BioCleaningAgent()

        # Register mock pipeline
        def mock_factory(dataset, workdir):
            return MockPipeline(dataset, workdir)

        agent.register_pipeline("sequencing", mock_factory)

        # Create dataset
        from bio_clean_agent.dataspec.models import load_dataset

        dataset = load_dataset("sequencing", sample_dataset_config)

        # Create plan
        plan = agent.plan(dataset, output_dir=str(tmp_path))

        assert isinstance(plan, AgentPlan)
        assert plan.dataset_id == "test_dataset"
        assert plan.dataset_type == "sequencing"
        assert plan.pipeline == "mock_pipeline"
        assert len(plan.steps) == 2
        assert all(isinstance(step, PlanStep) for step in plan.steps)

    def test_plan_without_output_dir_uses_default(self, sample_dataset_config):
        """Test plan uses default output directory."""
        agent = BioCleaningAgent()

        def mock_factory(dataset, workdir):
            return MockPipeline(dataset, workdir)

        agent.register_pipeline("sequencing", mock_factory)

        from bio_clean_agent.dataspec.models import load_dataset

        dataset = load_dataset("sequencing", sample_dataset_config)
        plan = agent.plan(dataset)

        assert "outputs" in plan.workdir
        assert "test_dataset" in plan.workdir

    def test_plan_with_parameters(self, sample_dataset_config):
        """Test plan includes custom parameters."""
        agent = BioCleaningAgent()

        def mock_factory(dataset, workdir):
            return MockPipeline(dataset, workdir)

        agent.register_pipeline("sequencing", mock_factory)

        from bio_clean_agent.dataspec.models import load_dataset

        dataset = load_dataset("sequencing", sample_dataset_config)
        parameters = {"quality_threshold": 30, "custom_param": "value"}

        plan = agent.plan(dataset, parameters=parameters)

        assert plan.parameters["quality_threshold"] == 30
        assert plan.parameters["custom_param"] == "value"

    def test_plan_to_dict(self, sample_dataset_config):
        """Test plan can be converted to dictionary."""
        agent = BioCleaningAgent()

        def mock_factory(dataset, workdir):
            return MockPipeline(dataset, workdir)

        agent.register_pipeline("sequencing", mock_factory)

        from bio_clean_agent.dataspec.models import load_dataset

        dataset = load_dataset("sequencing", sample_dataset_config)
        plan = agent.plan(dataset)

        plan_dict = plan.to_dict()

        assert isinstance(plan_dict, dict)
        assert plan_dict["dataset_id"] == "test_dataset"
        assert plan_dict["dataset_type"] == "sequencing"
        assert "steps" in plan_dict
        assert isinstance(plan_dict["steps"], list)

    def test_unregistered_pipeline_raises_error(self, sample_dataset_config):
        """Test error is raised for unregistered pipeline."""
        agent = BioCleaningAgent()

        from bio_clean_agent.dataspec.models import load_dataset

        dataset = load_dataset("sequencing", sample_dataset_config)

        with pytest.raises(ValueError, match="No pipeline registered"):
            agent.plan(dataset)


@pytest.mark.unit
class TestSimulatedToolExecutor:
    """Test suite for SimulatedToolExecutor."""

    def test_successful_execution(self):
        """Test simulated successful execution."""
        executor = SimulatedToolExecutor(succeed=True)
        result = executor.run(["echo", "test"], workdir="/tmp")

        assert result["returncode"] == 0
        assert result["stdout"] == "simulated execution"
        assert result["stderr"] == ""

    def test_failed_execution(self):
        """Test simulated failed execution."""
        executor = SimulatedToolExecutor(succeed=False)
        result = executor.run(["false"], workdir="/tmp")

        assert result["returncode"] == 1
        assert result["stderr"] == "simulated failure"


@pytest.mark.unit
class TestAgentRequest:
    """Test suite for AgentRequest."""

    def test_agent_request_creation(self, sample_dataset_config):
        """Test agent request can be created."""
        request = AgentRequest(
            dataset=sample_dataset_config,
            output_dir="/tmp/output",
            parameters={"quality_threshold": 20},
        )

        assert request.dataset == sample_dataset_config
        assert request.output_dir == "/tmp/output"
        assert request.parameters["quality_threshold"] == 20

    def test_agent_request_without_optional_params(self, sample_dataset_config):
        """Test agent request with minimal parameters."""
        request = AgentRequest(dataset=sample_dataset_config)

        assert request.dataset == sample_dataset_config
        assert request.output_dir is None
        assert request.parameters is None


@pytest.mark.unit
class TestPlanStep:
    """Test suite for PlanStep."""

    def test_plan_step_creation(self):
        """Test plan step can be created."""
        step = PlanStep("test_step", "This is a test step")

        assert step.name == "test_step"
        assert step.description == "This is a test step"

    def test_plan_step_to_dict(self):
        """Test plan step can be converted to dictionary."""
        step = PlanStep("test_step", "This is a test step")
        step_dict = step.to_dict()

        assert isinstance(step_dict, dict)
        assert step_dict["name"] == "test_step"
        assert step_dict["description"] == "This is a test step"
