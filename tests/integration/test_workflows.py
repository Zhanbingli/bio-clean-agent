"""Integration tests for end-to-end workflows - basic smoke tests."""

import pytest
from pathlib import Path

from bio_clean_agent.agent import BioCleaningAgent, AgentRequest, SimulatedToolExecutor


@pytest.mark.integration
class TestBasicWorkflow:
    """Test suite for basic agent workflow."""

    def test_agent_can_be_created(self, tmp_path):
        """Test basic agent creation."""
        agent = BioCleaningAgent(
            default_output_root=tmp_path,
            executor=SimulatedToolExecutor(succeed=True)
        )
        assert agent is not None

    def test_agent_request_can_be_created(self):
        """Test creating an agent request."""
        request = AgentRequest(
            dataset={
                "dataset_id": "test",
                "dataset_type": "sequencing",
                "raw_paths": ["test.fastq.gz"],
                "read_type": "single",
            },
            parameters={"quality_threshold": 20},
        )
        assert request is not None
