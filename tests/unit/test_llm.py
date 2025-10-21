"""Unit tests for LLM integration - basic smoke tests."""

import pytest

from bio_clean_agent.llm import SimulatedLLM


@pytest.mark.unit
class TestSimulatedLLM:
    """Test suite for SimulatedLLM."""

    def test_simulated_llm_initialization(self):
        """Test simulated LLM can be initialized."""
        llm = SimulatedLLM()
        assert isinstance(llm, SimulatedLLM)

    def test_simulated_llm_generate(self):
        """Test simulated LLM can generate response."""
        llm = SimulatedLLM()
        response = llm.generate("Test prompt")

        assert isinstance(response, str)
        assert len(response) > 0
