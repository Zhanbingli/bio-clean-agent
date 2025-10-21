"""Unit tests for LLM integration."""

import pytest
from unittest.mock import Mock, patch

from bio_clean_agent.llm import (
    LLMPlanner,
    SimulatedLLM,
    PlannerConfig,
    PlannerOutput,
    LLMRegistry,
)


@pytest.mark.unit
class TestSimulatedLLM:
    """Test suite for SimulatedLLM."""

    def test_simulated_llm_initialization(self):
        """Test simulated LLM can be initialized."""
        llm = SimulatedLLM()
        assert llm.model_name == "simulated"

    def test_simulated_llm_generate(self):
        """Test simulated LLM can generate response."""
        llm = SimulatedLLM()
        response = llm.generate("Test prompt")

        assert isinstance(response, str)
        assert len(response) > 0
        assert "simulated" in response.lower() or "test" in response.lower()

    def test_simulated_llm_different_prompts(self):
        """Test simulated LLM responds to different prompts."""
        llm = SimulatedLLM()
        response1 = llm.generate("What is the quality threshold?")
        response2 = llm.generate("How should I clean this data?")

        # Both should return responses
        assert isinstance(response1, str)
        assert isinstance(response2, str)


@pytest.mark.unit
class TestPlannerConfig:
    """Test suite for PlannerConfig."""

    def test_planner_config_default(self):
        """Test planner config with default settings."""
        config = PlannerConfig(model="simulated")

        assert config.model == "simulated"
        assert config.temperature >= 0
        assert config.max_tokens > 0

    def test_planner_config_custom(self):
        """Test planner config with custom settings."""
        config = PlannerConfig(
            model="gpt-4", temperature=0.5, max_tokens=2000, top_p=0.95
        )

        assert config.model == "gpt-4"
        assert config.temperature == 0.5
        assert config.max_tokens == 2000
        assert config.top_p == 0.95


@pytest.mark.unit
class TestPlannerOutput:
    """Test suite for PlannerOutput."""

    def test_planner_output_creation(self):
        """Test planner output can be created."""
        output = PlannerOutput(
            steps=["Step 1", "Step 2", "Step 3"],
            parameters={"quality_threshold": 20},
            reasoning="This is the reasoning for the plan",
        )

        assert len(output.steps) == 3
        assert output.parameters["quality_threshold"] == 20
        assert "reasoning" in output.reasoning.lower()


@pytest.mark.unit
class TestLLMRegistry:
    """Test suite for LLMRegistry."""

    def test_registry_initialization(self):
        """Test LLM registry can be initialized."""
        registry = LLMRegistry()
        assert isinstance(registry, LLMRegistry)

    def test_registry_register_llm(self):
        """Test registering an LLM provider."""
        registry = LLMRegistry()

        def mock_factory(config):
            return Mock()

        registry.register("mock_llm", mock_factory)
        assert "mock_llm" in registry._providers

    def test_registry_get_registered_llm(self):
        """Test getting a registered LLM."""
        registry = LLMRegistry()

        mock_llm = Mock()

        def mock_factory(config):
            return mock_llm

        registry.register("mock_llm", mock_factory)
        config = PlannerConfig(model="mock_llm")
        result = registry.get(config)

        assert result == mock_llm

    def test_registry_simulated_llm_available(self):
        """Test simulated LLM is available in registry."""
        registry = LLMRegistry()
        config = PlannerConfig(model="simulated")

        llm = registry.get(config)
        assert isinstance(llm, SimulatedLLM)


@pytest.mark.unit
@pytest.mark.requires_api_key
class TestOpenAILLM:
    """Test suite for OpenAI LLM integration."""

    @pytest.mark.skip(reason="Requires OpenAI API key")
    def test_openai_llm_initialization(self):
        """Test OpenAI LLM can be initialized with API key."""
        import os

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")

        from bio_clean_agent.llm import OpenAILLM

        llm = OpenAILLM(api_key=api_key, model="gpt-3.5-turbo")
        assert llm.model_name == "gpt-3.5-turbo"

    @pytest.mark.skip(reason="Requires OpenAI API key and makes API calls")
    def test_openai_llm_generate(self):
        """Test OpenAI LLM can generate responses."""
        import os

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")

        from bio_clean_agent.llm import OpenAILLM

        llm = OpenAILLM(api_key=api_key, model="gpt-3.5-turbo")
        response = llm.generate("What is 2+2?")

        assert isinstance(response, str)
        assert len(response) > 0
