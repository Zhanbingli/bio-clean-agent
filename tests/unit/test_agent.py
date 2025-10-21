"""Unit tests for BioCleaningAgent - basic smoke tests."""

import pytest
from pathlib import Path

from bio_clean_agent.agent import (
    BioCleaningAgent,
    AgentRequest,
    SimulatedToolExecutor,
    SubprocessToolExecutor,
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

    def test_agent_request_creation(self):
        """Test agent request can be created."""
        dataset = {
            "dataset_id": "test",
            "dataset_type": "sequencing",
            "raw_paths": ["test.fastq.gz"],
        }
        request = AgentRequest(
            dataset=dataset,
            output_dir="/tmp/output",
            parameters={"quality_threshold": 20},
        )

        assert request.dataset == dataset
        assert request.output_dir == "/tmp/output"
        assert request.parameters["quality_threshold"] == 20

    def test_agent_request_without_optional_params(self):
        """Test agent request with minimal parameters."""
        dataset = {"dataset_id": "test", "dataset_type": "sequencing"}
        request = AgentRequest(dataset=dataset)

        assert request.dataset == dataset
        assert request.output_dir is None
        assert request.parameters is None
